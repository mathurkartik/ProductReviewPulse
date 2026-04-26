import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Define the directory where this script lives
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/gmail.compose"
]

def get_creds():
    creds = None
    
    # Define paths relative to this script
    token_path = os.path.join(BASE_DIR, "token.json")
    creds_path = os.path.join(BASE_DIR, "credentials.json")
    
    # 1. Load from Individual Environment Variables (Most robust for Render)
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    refresh_token = os.environ.get("GOOGLE_REFRESH_TOKEN")
    
    if client_id and client_secret and refresh_token:
        creds = Credentials(
            token=None, 
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=SCOPES
        )
    
    # 2. Fallback to GOOGLE_TOKEN_JSON blob
    if not creds:
        env_token = os.environ.get("GOOGLE_TOKEN_JSON")
        if env_token:
            try:
                token_dict = json.loads(env_token)
                creds = Credentials.from_authorized_user_info(token_dict, SCOPES)
            except json.JSONDecodeError as e:
                if os.environ.get("RENDER"):
                    raise Exception(f"GOOGLE_TOKEN_JSON is set but contains invalid JSON: {e}")
                else:
                    print(f"Error parsing GOOGLE_TOKEN_JSON: {e}")

    # 3. Fallback to local file
    if not creds and os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    # 4. Refresh or Fail (No interactive login in cloud)
    if not creds or not creds.valid:
        if creds and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                if os.environ.get("RENDER"):
                    raise Exception(f"Failed to refresh Google token: {e}. Check if Client ID/Secret/Refresh Token are correct.")
                else:
                    print(f"Refresh failed: {e}")
        else:
            if os.environ.get("RENDER"):
                msg = "Google Auth failed on Render. Please set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and GOOGLE_REFRESH_TOKEN environment variables."
                raise Exception(msg)
            
            # Local flow - check if credentials.json exists
            if not os.path.exists(creds_path):
                raise FileNotFoundError(f"Missing 'credentials.json' in {BASE_DIR}. Please download it from Google Cloud Console.")
                
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the refreshed token locally if not on Render
        if not os.environ.get("RENDER"):
            with open(token_path, "w") as token:
                token.write(creds.to_json())
                
    return creds

if __name__ == "__main__":
    print("Starting Google OAuth flow...")
    try:
        get_creds()
        print(f"Successfully saved token.json to {BASE_DIR}")
    except Exception as e:
        print(f"Error: {e}")