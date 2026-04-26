import logging
from googleapiclient.discovery import build
from auth import get_creds

logger = logging.getLogger(__name__)

def search_messages(query: str):
    """Search for Gmail messages using a query (e.g. 'X-Pulse-Run-Id:123')."""
    try:
        logger.info(f"Searching messages with query: {query}")
        creds = get_creds()
        service = build("gmail", "v1", credentials=creds)
        
        results = service.users().messages().list(userId="me", q=query).execute()
        messages = results.get("messages", [])
        
        return {
            "status": "success",
            "messages": messages
        }
    except Exception as e:
        logger.error(f"search_messages error: {e}")
        return {"status": "error", "message": str(e)}

import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def create_message(to: str, subject: str, text: str, html: str = None, cc: str = "", bcc: str = "", headers: dict = None):
    """Create a base64url encoded email message."""
    if html:
        message = MIMEMultipart("alternative")
        message.attach(MIMEText(text, "plain", "utf-8"))
        message.attach(MIMEText(html, "html", "utf-8"))
    else:
        message = MIMEText(text, "plain", "utf-8")
        
    message["to"] = to
    message["subject"] = subject
    if cc: message["cc"] = cc
    if bcc: message["bcc"] = bcc
    
    if headers:
        for k, v in headers.items():
            # Avoid overwriting standard headers if they are passed in headers dict
            if k.lower() not in ["to", "subject", "cc", "bcc"]:
                message[k] = v
            
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return raw

def get_or_create_label(service, label_name: str) -> str:
    """Find a label by name, or create it if it doesn't exist."""
    try:
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])
        for lbl in labels:
            if lbl['name'] == label_name:
                return lbl['id']
                
        # Create it
        label_object = {
            'messageListVisibility': 'show',
            'name': label_name,
            'labelListVisibility': 'labelShow'
        }
        created = service.users().labels().create(userId='me', body=label_object).execute()
        return created['id']
    except Exception as e:
        logger.warning(f"Could not get or create label '{label_name}': {e}. Missing gmail.labels scope?")
        return None

def create_draft(to: str, subject: str, text: str, html: str = None, cc: str = "", bcc: str = "", headers: dict = None, label_name: str = None):
    """Create a Gmail draft."""
    try:
        logger.info(f"Creating Gmail draft for {to}")
        creds = get_creds()
        service = build("gmail", "v1", credentials=creds)
        
        raw_message = create_message(to, subject, text, html, cc, bcc, headers)
        
        body_obj = {"message": {"raw": raw_message}}
        
        # Note: Labels cannot be set on drafts via Gmail API
        # Labels are applied after the message is sent
        if label_name:
            lbl_id = get_or_create_label(service, label_name)
            if lbl_id:
                body_obj["message"]["labelIds"] = [lbl_id]
            
        draft = service.users().drafts().create(userId="me", body=body_obj).execute()
        
        return {
            "status": "success",
            "draft_id": draft.get("id")
        }
    except Exception as e:
        logger.error(f"create_draft error: {e}")
        return {"status": "error", "message": str(e)}

def send_message(draft_id: str):
    """Send an existing Gmail draft."""
    try:
        logger.info(f"Sending draft {draft_id}")
        creds = get_creds()
        service = build("gmail", "v1", credentials=creds)
        
        body = {"id": draft_id}
        result = service.users().drafts().send(userId="me", body=body).execute()
        
        return {
            "status": "success",
            "message_id": result.get("id")
        }
    except Exception as e:
        logger.error(f"send_message error: {e}")
        return {"status": "error", "message": str(e)}