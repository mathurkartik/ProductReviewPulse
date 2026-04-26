import logging
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Re-create credentials.json from environment variable for Google libraries
if os.environ.get("GOOGLE_CREDENTIALS_JSON"):
    creds_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "credentials.json")
    with open(creds_path, "w") as f:
        f.write(os.environ.get("GOOGLE_CREDENTIALS_JSON"))

# ---------------- LOGGING SETUP ---------------- #
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# ---------------- APP INIT ---------------- #
app = FastAPI(title="Google MCP Server")


# ---------------- REQUEST SCHEMAS ---------------- #
class CreateDocInput(BaseModel):
    title: str

class GetDocInput(BaseModel):
    doc_id: str

class BatchUpdateInput(BaseModel):
    doc_id: str
    requests: list

class EmailInput(BaseModel):
    to: str
    subject: str
    text: str
    html: str | None = None
    cc: str | None = ""
    bcc: str | None = ""
    headers: dict | None = None
    label: str | None = None

class SearchEmailInput(BaseModel):
    query: str

class SendMessageInput(BaseModel):
    draft_id: str


# ---------------- APPROVAL LAYER ---------------- #
def approve(action: str, payload: dict) -> bool:
    """
    Approval system:
    - Local → manual approval
    - Deployment → auto-approved
    """

    # ✅ Auto-approve in deployment (Render sets RENDER=true automatically)
    if os.getenv("AUTO_APPROVE", "false").lower() == "true" or os.getenv("RENDER"):
        logger.info(f"{action} auto-approved (deployment env)")
        return True

    # 🧪 Local CLI approval
    try:
        print("\n-----------------------------")
        print(f"ACTION: {action}")
        print(f"PAYLOAD: {payload}")
        print("-----------------------------")

        decision = input("Approve? (y/n): ").strip().lower()

        if decision == "y":
            logger.info(f"{action} approved")
            return True
        else:
            logger.warning(f"{action} rejected")
            return False

    except Exception as e:
        logger.error(f"Approval error: {e}")
        return False


# ---------------- MCP TOOL LIST ---------------- #
@app.get("/tools")
def list_tools():
    return [
        {"name": "docs.create_document", "description": "Create a new Google Doc"},
        {"name": "docs.get_document", "description": "Get a Google Doc's content"},
        {"name": "docs.batch_update", "description": "Send a batchUpdate request to a Google Doc"},
        {"name": "gmail.search_messages", "description": "Search Gmail messages"},
        {"name": "gmail.create_draft", "description": "Create Gmail draft"},
        {"name": "gmail.send_message", "description": "Send Gmail draft"}
    ]


# ---------------- DOCS TOOLS ---------------- #
from docs_tool import create_document, get_document, batch_update
from gmail_tool import search_messages, create_draft, send_message

@app.post("/docs.create_document")
def run_create(data: CreateDocInput):
    if not approve("docs.create_document", data.dict()): return {"status": "rejected"}
    return create_document(title=data.title)

@app.post("/docs.get_document")
def run_get(data: GetDocInput):
    if not approve("docs.get_document", data.dict()): return {"status": "rejected"}
    return get_document(doc_id=data.doc_id)

@app.post("/docs.batch_update")
def run_batch_update(data: BatchUpdateInput):
    if not approve("docs.batch_update", {"doc_id": data.doc_id, "requests_count": len(data.requests)}): return {"status": "rejected"}
    return batch_update(doc_id=data.doc_id, requests=data.requests)


# ---------------- EMAIL TOOL ---------------- #
@app.post("/gmail.search_messages")
def run_search(data: SearchEmailInput):
    if not approve("gmail.search_messages", data.dict()): return {"status": "rejected"}
    return search_messages(query=data.query)

@app.post("/gmail.create_draft")
def run_email(data: EmailInput):
    try:
        logger.info("Received request for gmail.create_draft")
        if not approve("gmail.create_draft", data.dict()):
            return {"status": "rejected", "message": "User rejected the action"}
        result = create_draft(
            to=data.to, 
            subject=data.subject, 
            text=data.text, 
            html=data.html,
            cc=data.cc,
            bcc=data.bcc,
            headers=data.headers,
            label_name=data.label
        )
        logger.info("gmail.create_draft executed successfully")
        return result
    except Exception as e:
        logger.error(f"Error in gmail.create_draft: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/gmail.send_message")
def run_send(data: SendMessageInput):
    try:
        logger.info("Received request for gmail.send_message")
        if not approve("gmail.send_message", data.dict()):
            return {"status": "rejected", "message": "User rejected the action"}
        result = send_message(draft_id=data.draft_id)
        logger.info("gmail.send_message executed successfully")
        return result
    except Exception as e:
        logger.error(f"Error in gmail.send_message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------- HEALTH CHECK ---------------- #
@app.get("/")
def root():
    return {
        "message": "Google MCP Server is running 🚀"
    }