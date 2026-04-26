import logging
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from auth import get_creds

# ---------------- LOGGING SETUP ---------------- #
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


# ---------------- MAIN FUNCTIONS ---------------- #

def create_document(title: str):
    try:
        logger.info(f"Starting create_document for title={title}")
        creds = get_creds()
        service = build("docs", "v1", credentials=creds)
        
        doc = service.documents().create(body={"title": title}).execute()
        
        return {
            "status": "success",
            "document_id": doc.get("documentId")
        }
    except Exception as e:
        logger.error(f"create_document error: {e}")
        return {"status": "error", "message": str(e)}


def get_document(doc_id: str):
    try:
        logger.info(f"Starting get_document for doc_id={doc_id}")
        creds = get_creds()
        service = build("docs", "v1", credentials=creds)
        
        doc = service.documents().get(documentId=doc_id).execute()
        
        return {
            "status": "success",
            "document": doc
        }
    except Exception as e:
        logger.error(f"get_document error: {e}")
        return {"status": "error", "message": str(e)}


def batch_update(doc_id: str, requests: list):
    try:
        logger.info(f"Starting batch_update for doc_id={doc_id}")
        creds = get_creds()
        service = build("docs", "v1", credentials=creds)
        
        result = service.documents().batchUpdate(
            documentId=doc_id,
            body={"requests": requests}
        ).execute()
        
        return {
            "status": "success",
            "replies": result.get("replies", [])
        }
    except Exception as e:
        logger.error(f"batch_update error: {e}")
        return {"status": "error", "message": str(e)}