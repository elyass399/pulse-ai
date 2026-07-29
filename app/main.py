"""
Pulse - FastAPI Backend
Espone REST API per il frontend.
"""

import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db, engine, Base
from app.models import Briefing, UserPreference
from app.schemas import BriefingOut, FeedbackCreate, FeedbackOut
from app.agents.orchestrator import generate_briefing
from app.llm_client import get_llm_client
from app.config import get_settings
from app.scheduler import start_scheduler

# Crea tabelle se non esistono
Base.metadata.create_all(bind=engine)

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="AI-powered autonomous news briefing agent",
    version="1.0.0",
)

# CORS - per demo/portfolio: permetti tutto
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve cartella media per immagini fallback
app.mount("/media", StaticFiles(directory="media"), name="media")


# --- Root: serve frontend ---

def _find_frontend():
    """Trova il file frontend/index.html in vari path possibili."""
    current_file = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file)

    possible_paths = [
        os.path.join(current_dir, "..", "frontend", "index.html"),
        os.path.join(current_dir, "..", "..", "frontend", "index.html"),
        os.path.join(os.getcwd(), "frontend", "index.html"),
        "/opt/render/project/src/frontend/index.html",
        "/opt/render/project/frontend/index.html",
    ]

    results = []
    for path in possible_paths:
        abs_path = os.path.abspath(path)
        exists = os.path.exists(abs_path)
        results.append({"path": abs_path, "exists": exists})
        if exists:
            return abs_path, results

    return None, results


@app.get("/")
@app.head("/")
def serve_frontend():
    """Serve il frontend HTML alla root."""
    frontend_path, debug_info = _find_frontend()

    if frontend_path:
        return FileResponse(frontend_path)

    # Debug: mostra tutti i path provati
    cwd = os.getcwd()
    files_in_cwd = []
    try:
        files_in_cwd = os.listdir(cwd)
    except:
        pass

    # Cerca ricorsivamente frontend/index.html
    found_paths = []
    for root, dirs, files in os.walk(cwd):
        if "index.html" in files and "frontend" in root:
            found_paths.append(os.path.join(root, "index.html"))

    html_debug = f"""<!DOCTYPE html>
<html>
<head><title>Pulse - Debug</title></head>
<body style="font-family: monospace; padding: 20px;">
    <h1>Pulse - Frontend Not Found</h1>
    <h2>CWD: {cwd}</h2>
    <h3>Files in CWD:</h3>
    <ul>
    """
    for f in files_in_cwd:
        html_debug += f"<li>{f}</li>"

    html_debug += """
    </ul>
    <h3>Paths tried:</h3>
    <table border="1" cellpadding="5">
        <tr><th>Path</th><th>Exists</th></tr>
    """
    for info in debug_info:
        status = "YES" if info["exists"] else "NO"
        html_debug += f"<tr><td>{info['path']}</td><td>{status}</td></tr>"

    html_debug += f"""
    </table>
    <h3>Found frontend/index.html recursively:</h3>
    <ul>
    """
    for p in found_paths:
        html_debug += f"<li>{p}</li>"
    if not found_paths:
        html_debug += "<li>NOT FOUND</li>"

    html_debug += """
    </ul>
</body>
</html>
    """

    return HTMLResponse(content=html_debug, status_code=404)


# --- Debug endpoint ---

@app.get("/debug/tree")
def debug_tree():
    """Mostra la struttura delle cartelle."""
    cwd = os.getcwd()
    tree = []

    for root, dirs, files in os.walk(cwd):
        level = root.replace(cwd, '').count(os.sep)
        indent = ' ' * 2 * level
        tree.append(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files[:10]:  # max 10 files per dir
            tree.append(f"{subindent}{file}")
        if len(files) > 10:
            tree.append(f"{subindent}... ({len(files) - 10} more files)")

    return {"cwd": cwd, "tree": tree}


# --- Startup / Shutdown ---

@app.on_event("startup")
async def startup_event():
    start_scheduler()


@app.on_event("shutdown")
async def shutdown_event():
    from app.scheduler import stop_scheduler
    stop_scheduler()


# --- Health Check ---

@app.get("/health")
def health_check():
    return {"status": "ok", "app": settings.app_name}


# --- Briefing Endpoints ---

@app.get("/briefing/latest", response_model=list[BriefingOut])
def get_latest_briefing(db: Session = Depends(get_db)):
    latest_run = db.query(func.max(Briefing.created_at)).scalar()

    if not latest_run:
        return []

    briefings = (
        db.query(Briefing)
        .filter(func.date(Briefing.created_at) == func.date(latest_run))
        .order_by(Briefing.field, Briefing.is_trending.desc(), Briefing.id)
        .all()
    )

    return briefings


@app.get("/briefing/history", response_model=list[BriefingOut])
def get_briefing_history(
    field: str = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(Briefing).order_by(Briefing.created_at.desc())

    if field:
        query = query.filter(Briefing.field == field)

    return query.limit(limit).all()


@app.post("/briefing/generate")
def generate_new_briefing(db: Session = Depends(get_db)):
    """Genera briefing solo se non esistono gia per oggi."""
    today = datetime.now().date()
    today_briefings = db.query(Briefing).filter(
        func.date(Briefing.created_at) == today
    ).count()

    if today_briefings > 0:
        briefings = db.query(Briefing).filter(
            func.date(Briefing.created_at) == today
        ).order_by(Briefing.field, Briefing.is_trending.desc()).all()

        return {
            "status": "already_generated",
            "message": f"Today's briefing already exists ({len(briefings)} stories)",
            "data": briefings
        }

    try:
        briefing = generate_briefing()
        return {
            "status": "success",
            "message": f"Generated {len(briefing)} stories",
            "data": briefing
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Single Briefing ---

@app.get("/briefing/{briefing_id}", response_model=BriefingOut)
def get_briefing(briefing_id: int, db: Session = Depends(get_db)):
    briefing = db.query(Briefing).filter(Briefing.id == briefing_id).first()
    if not briefing:
        raise HTTPException(status_code=404, detail="Briefing not found")
    return briefing


@app.post("/briefing/{briefing_id}/explain")
def explain_briefing(briefing_id: int, db: Session = Depends(get_db)):
    briefing = db.query(Briefing).filter(Briefing.id == briefing_id).first()
    if not briefing:
        raise HTTPException(status_code=404, detail="Briefing not found")

    llm = get_llm_client()

    text_to_explain = briefing.summary
    if not text_to_explain or len(text_to_explain) < 50:
        text_to_explain = f"{briefing.title}. {briefing.why_matters}"

    explanation = llm.explain_briefing(
        title=briefing.title,
        summary=text_to_explain
    )

    return {
        "briefing_id": briefing_id,
        "original_title": briefing.title,
        "explanation": explanation
    }


# --- Feedback ---

@app.post("/briefing/{briefing_id}/feedback", response_model=FeedbackOut)
def create_feedback(
    briefing_id: int,
    feedback: FeedbackCreate,
    db: Session = Depends(get_db)
):
    briefing = db.query(Briefing).filter(Briefing.id == briefing_id).first()
    if not briefing:
        raise HTTPException(status_code=404, detail="Briefing not found")

    db_feedback = UserPreference(
        briefing_id=briefing_id,
        liked=feedback.liked
    )
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)

    return db_feedback


# --- Run ---

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)