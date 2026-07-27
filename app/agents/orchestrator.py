"""
LangGraph Orchestrator per Pulse.
Coordina 5 field agents, sintetizza TUTTI gli articoli (25 totali), salva nel DB.
"""

from typing import List, Dict, Any, TypedDict
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.constants import START

from app.agents.field_agent import FieldAgent
from app.llm_client import get_llm_client
from app.database import SessionLocal
from app.models import Briefing


# --- State Type ---

class PulseState(TypedDict):
    """Stato condiviso tra i nodi del grafo."""
    fields: List[str]                     # campi da processare
    results: Dict[str, List[Dict]]        # tutti gli articoli per campo (5 each)
    final_briefing: List[Dict]            # TUTTI gli articoli da salvare (25)
    status: str                           # stato corrente


# --- Nodi ---

def fetch_all_fields(state: PulseState) -> PulseState:
    """
    Nodo FETCH: spawna 5 field agents.
    Ognuno fetcha 5 notizie = 25 totali.
    """
    print("\n" + "=" * 50)
    print("🚀 ORCHESTRATOR: Fetching all fields (5 each = 25 total)")
    print("=" * 50)

    fields = state.get("fields", ["tech", "finance", "sport", "health", "geo"])
    results = {}

    for field in fields:
        agent = FieldAgent(field)
        top5 = agent.run(limit=5)
        results[field] = top5

    state["results"] = results
    state["status"] = "fetched"
    return state


def synthesize_all(state: PulseState) -> PulseState:
    """
    Nodo SYNTHESIZE: scrive riassunto e "why it matters" per TUTTI i 25 articoli.
    """
    print("\n" + "=" * 50)
    print("🧠 ORCHESTRATOR: Synthesizing ALL 25 articles")
    print("=" * 50)

    llm = get_llm_client()
    final_briefing = []

    for field, articles in state["results"].items():
        for i, article in enumerate(articles):
            text = article.get("full_text", article.get("summary", ""))
            
            # Riassunto
            summary = llm.summarize(text=text, field=field)
            
            # Why it matters
            why_matters = llm.explain_why_matters(
                title=article["title"],
                summary=summary,
                field=field
            )
            if not why_matters:
                why_matters = f"Significant development in {field} with potential industry impact."

            story = {
                "field": field,
                "title": article["title"],
                "url": article["url"],
                "summary": summary,
                "why_matters": why_matters,
                "source_name": article.get("source", "Unknown"),
                "published_at": article.get("published"),
                "score": article.get("score", 0),
                "rank": i + 1,  # 1-5 per campo
            }

            final_briefing.append(story)
            print(f"  [{field.upper()} #{i+1}] {article['title'][:50]}...")

    state["final_briefing"] = final_briefing
    state["status"] = "synthesized"
    return state


def save_to_db(state: PulseState) -> PulseState:
    """
    Nodo SAVE: salva TUTTI i 25 articoli nel database.
    """
    print("\n" + "=" * 50)
    print(f"💾 ORCHESTRATOR: Saving {len(state['final_briefing'])} articles")
    print("=" * 50)

    db = SessionLocal()
    try:
        # Trova lo score più alto per il trending badge
        max_score = max(
            (s.get("score", 0) for s in state["final_briefing"]),
            default=0
        )

        for story in state["final_briefing"]:
            briefing = Briefing(
                field=story["field"],
                title=story["title"],
                url=str(story["url"]),
                summary=story["summary"],
                why_matters=story["why_matters"],
                source_name=story["source_name"],
                published_at=parse_date(story.get("published_at")),
                is_trending=(story.get("score", 0) == max_score and max_score > 7),
            )
            db.add(briefing)

        db.commit()
        print(f"  ✅ Saved {len(state['final_briefing'])} briefings")

    except Exception as e:
        db.rollback()
        print(f"  ❌ Error saving: {e}")
    finally:
        db.close()

    state["status"] = "saved"
    return state


def parse_date(date_str: Any) -> datetime:
    """Parse date string, ritorna now se fallisce."""
    if not date_str:
        return datetime.now()

    try:
        from dateutil import parser
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return parser.parse(date_str, fuzzy=True)
    except:
        return datetime.now()


# --- Costruzione Grafo ---

def build_graph() -> StateGraph:
    """
    Costruisce il grafo LangGraph.
    """
    workflow = StateGraph(PulseState)

    workflow.add_node("fetch", fetch_all_fields)
    workflow.add_node("synthesize", synthesize_all)
    workflow.add_node("save", save_to_db)

    workflow.add_edge(START, "fetch")
    workflow.add_edge("fetch", "synthesize")
    workflow.add_edge("synthesize", "save")
    workflow.add_edge("save", END)

    return workflow.compile()


# --- Entry Point ---

def generate_briefing(fields: List[str] = None) -> List[Dict[str, Any]]:
    """
    Genera un briefing completo con 25 articoli (5 per campo).
    Entry point principale.
    """
    if fields is None:
        fields = ["tech", "finance", "sport", "health", "geo"]

    graph = build_graph()

    initial_state: PulseState = {
        "fields": fields,
        "results": {},
        "final_briefing": [],
        "status": "start",
    }

    final_state = graph.invoke(initial_state)

    return final_state["final_briefing"]