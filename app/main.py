"""
Pulse - FastAPI Backend
Espone REST API per il frontend.
"""

import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

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

@app.get("/")
def serve_frontend():
    """Serve il frontend HTML alla root."""
    # Prova diversi path per trovare il frontend
    possible_paths = [
        os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html"),
        os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "index.html"),
        os.path.join(os.getcwd(), "frontend", "index.html"),
        "/opt/render/project/src/frontend/index.html",
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return FileResponse(path)

    # Se non trova il file, restituisci un messaggio di debug
    return {
        "error": "frontend/index.html not found",
        "cwd": os.getcwd(),
        "files_in_cwd": os.listdir(os.getcwd()) if os.path.exists(os.getcwd()) else "N/A",
        "tried_paths": possible_paths,
    }


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
    from sqlalchemy import func

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
def generate_new_briefing():
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