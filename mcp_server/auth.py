import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/gmail.compose"
]

def get_creds():
    creds = None
    
    # 1. Load from Environment Variable (for Render)
    env_token = os.environ.get("GOOGLE_TOKEN_JSON")
    if env_token:
        creds = Credentials.from_authorized_user_info(json.loads(env_token), SCOPES)
    # 2. Fallback to local file
    elif os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # 3. Refresh or Fail (No interactive login in cloud)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if os.environ.get("RENDER"):
                raise Exception("Missing GOOGLE_TOKEN_JSON env var or token is totally invalid.")
            
            # Local flow
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the refreshed token locally if not on Render
        if not os.environ.get("RENDER"):
            with open("token.json", "w") as token:
                token.write(creds.to_json())
                
    return creds

if __name__ == "__main__":
    print("Starting Google OAuth flow...")
    get_creds()
    print("Successfully saved token.json!")