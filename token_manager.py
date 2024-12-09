import requests
import os
import time


# Helper function to get the token from environment variables
def get_refresh_token():
    return os.getenv("REFRESH_TOKEN")


def get_client_id():
    return os.getenv("CLIENT_ID")


def get_client_secret():
    return os.getenv("CLIENT_SECRET")


def get_tenant_id():
    return os.getenv("TENANT_ID")


# Function to fetch the access token using the refresh token
def fetch_access_token():
    token_url = f"https://login.microsoftonline.com/{get_tenant_id()}/oauth2/v2.0/token"
    payload = {
        "client_id": get_client_id(),
        "client_secret": get_client_secret(),
        "grant_type": "refresh_token",
        "refresh_token": get_refresh_token(),
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    response = requests.post(token_url, data=payload, headers=headers)
    if response.status_code == 200:
        token_data = response.json()
        return token_data.get("access_token"), token_data.get("expires_in")
    else:
        raise Exception(f"Failed to fetch access token: {response.content}")


# Token Cache to avoid repeated requests
class TokenManager:
    def __init__(self):
        self.access_token = None
        self.token_expiry = 0

    def get_access_token(self):
        # Check if token is expired
        current_time = time.time()
        if not self.access_token or current_time >= self.token_expiry:
            # Refresh the token
            self.access_token, expires_in = fetch_access_token()
            self.token_expiry = current_time + expires_in - 30  # Subtract 30 seconds as buffer
        return self.access_token


# Singleton instance for reuse across routes
token_manager = TokenManager()
