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
    
    # 1. Load from Environment Variable (for Render)
    env_token = os.environ.get("GOOGLE_TOKEN_JSON")
    if env_token:
        creds = Credentials.from_authorized_user_info(json.loads(env_token), SCOPES)
    # 2. Fallback to local file
    elif os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    # 3. Refresh or Fail (No interactive login in cloud)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if os.environ.get("RENDER"):
                raise Exception("Missing GOOGLE_TOKEN_JSON env var or token is totally invalid.")
            
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