from flask import Flask, request, jsonify
import requests
import py7zr
import io
import os

app = Flask(__name__)

# Environment variables to securely store client_id, client_secret, tenant_id
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
TENANT_ID = os.environ.get("TENANT_ID")
REFRESH_TOKEN = os.environ.get("REFRESH_TOKEN")


def refresh_access_token():
    """Function to refresh the access token using the refresh token."""
    token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    
    # Prepare the data for token refresh
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
    }

    try:
        # Send a POST request to refresh the token
        response = requests.post(token_url, data=data)
        response.raise_for_status()  # Raise error if request fails
        new_tokens = response.json()
        
        # Extract the new token
        new_access_token = new_tokens.get("access_token")
        new_refresh_token = new_tokens.get("refresh_token", REFRESH_TOKEN)  # Refresh token may or may not change
        return new_access_token, new_refresh_token
    except Exception as e:
        print("Token refresh error:", e)
        return None, None


@app.route("/extract", methods=["POST"])
def extract_and_upload():
    try:
        # Step 1: Refresh access token first
        access_token, refreshed_token = refresh_access_token()
        if not access_token:
            return jsonify({"error": "Unable to refresh access token"}), 500

        # Update refresh token securely if refreshed
        global REFRESH_TOKEN
        if refreshed_token:
            REFRESH_TOKEN = refreshed_token

        # Parse JSON input
        data = request.json
        file_id = data["file_id"]
        folder_id = data["folder_id"]

        # Step 2: Download file from OneDrive
        download_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{file_id}/content"
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(download_url, headers=headers)

        if response.status_code != 200:
            return jsonify({"error": "Failed to download file"}), 400

        # Step 3: Extract files
        file_content = io.BytesIO(response.content)
        extracted_files = {}
        with py7zr.SevenZipFile(file_content, mode='r') as archive:
            for file_name, file_info in archive.getnames().items():
                extracted_files[file_name] = archive.read([file_name])[file_name]

        # Step 4: Upload extracted files to OneDrive
        for file_name, file_data in extracted_files.items():
            upload_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{folder_id}:/{file_name}:/content"
            upload_response = requests.put(upload_url, headers=headers, data=file_data)

            if upload_response.status_code != 201:
                return jsonify({"error": f"Failed to upload {file_name}"}), 400

        return jsonify({"success": True, "message": "All files uploaded successfully!"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
