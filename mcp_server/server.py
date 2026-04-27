import logging
import os
from fastapi import FastAPI, HTTPException, UploadFile, File, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import shutil
from pathlib import Path

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

# Enable CORS for Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your Vercel URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Path
DB_PATH = Path(os.environ.get("PULSE_DB_PATH", "pulse.sqlite"))


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
        "status": "online",
        "message": "Google MCP Server & Pulse API is running 🚀"
    }

# ---------------- DATABASE SYNC API ---------------- #
@app.post("/api/sync/db")
async def sync_database(
    file: UploadFile = File(...),
    x_sync_key: str = Header(None, alias="X-Sync-Key")
):
    """Securely receive the latest pulse.sqlite from GitHub Actions."""
    expected_key = os.environ.get("SYNC_API_KEY")
    if not expected_key or x_sync_key != expected_key:
        raise HTTPException(status_code=403, detail="Invalid or missing X-Sync-Key")

    try:
        # Save the uploaded file to a temporary location first
        temp_path = DB_PATH.with_suffix(".tmp")
        with temp_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Verify it's a valid SQLite file
        try:
            test_conn = sqlite3.connect(temp_path)
            test_conn.execute("SELECT name FROM sqlite_master LIMIT 1")
            test_conn.close()
        except Exception:
            if temp_path.exists(): temp_path.unlink()
            raise HTTPException(status_code=400, detail="Uploaded file is not a valid SQLite database")

        # Atomic swap
        shutil.move(str(temp_path), str(DB_PATH))
        logger.info(f"Database synced successfully via API from {file.filename}")
        return {"status": "success", "message": "Database updated"}
    except Exception as e:
        logger.error(f"Error syncing database: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ---------------- PULSE DATA API ---------------- #
@app.get("/api/pulse/latest")
def get_latest_pulse_data():
    """Fetch the most recent successful run."""
    if not DB_PATH.exists():
        raise HTTPException(status_code=404, detail=f"Database not found at {DB_PATH}")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        latest_run = cursor.execute(
            "SELECT run_id FROM runs WHERE status IN ('summarized', 'published') ORDER BY updated_at DESC LIMIT 1"
        ).fetchone()
        
        if not latest_run:
            raise HTTPException(status_code=404, detail="No successful runs found")
            
        return get_pulse_data(latest_run["run_id"])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching latest pulse data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pulse/{run_id}")
def get_pulse_data(run_id: str):
    """Fetch summarized data for the dashboard."""
    if not DB_PATH.exists():
        raise HTTPException(status_code=404, detail=f"Database not found at {DB_PATH}")

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 1. Fetch Run Metadata
        run = cursor.execute(
            "SELECT * FROM runs WHERE run_id = ?", (run_id,)
        ).fetchone()
        if not run:
            raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

        # 2. Fetch Product Info
        product = cursor.execute("SELECT * FROM products WHERE key = ?", (run["product_key"],)).fetchone()

        # 3. Fetch Top Themes
        themes = cursor.execute(
            "SELECT * FROM themes WHERE run_id = ? ORDER BY rank ASC", (run_id,)
        ).fetchall()

        # 4. Fetch a few sample reviews (Quotes fallback)
        quotes = []
        clusters = cursor.execute(
            "SELECT medoid_review_id FROM clusters WHERE run_id = ? LIMIT 3", (run_id,)
        ).fetchall()
        
        for c in clusters:
            rev = cursor.execute(
                "SELECT body, rating, source FROM reviews WHERE id = ?", (c["medoid_review_id"],)
            ).fetchone()
            if rev:
                quotes.append({
                    "text": rev["body"],
                    "rating": rev["rating"],
                    "source": rev["source"]
                })

        return {
            "run_id": run["run_id"],
            "product": product["display"] if product else run["product_key"],
            "iso_week": run["iso_week"],
            "status": run["status"],
            "window": {
                "start": run["window_start"],
                "end": run["window_end"]
            },
            "themes": [dict(t) for t in themes],
            "quotes": quotes
        }
    except Exception as e:
        logger.error(f"Error fetching pulse data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()