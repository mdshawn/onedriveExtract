from flask import Flask, request, jsonify
import py7zr
import io
import requests
from token_manager import token_manager  # Import the token manager

app = Flask(__name__)


@app.route("/extract", methods=["POST"])
def extract_and_upload():
    try:
        # Parse JSON input
        data = request.json
        file_id = data["file_id"]
        folder_id = data["folder_id"]

        # Get an access token automatically
        access_token = token_manager.get_access_token()

        # Step 1: Download file from OneDrive
        download_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{file_id}/content"
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(download_url, headers=headers)

        if response.status_code != 200:
            return jsonify({"error": "Failed to download file"}), 400

        # Step 2: Extract files
        file_content = io.BytesIO(response.content)
        extracted_files = {}
        with py7zr.SevenZipFile(file_content, mode='r') as archive:
            for file_name, file_info in archive.getnames().items():
                extracted_files[file_name] = archive.read([file_name])[file_name]

        # Step 3: Upload extracted files to OneDrive
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
