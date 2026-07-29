"""
Orchestrator: coordina i Field Agent e genera il briefing finale.
Salva i risultati nel database con validazione dei campi obbligatori.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from app.agents.field_agent import FieldAgent
from app.llm_client import get_llm_client
from app.database import SessionLocal
from app.models import Briefing


FIELDS = ["tech", "finance", "sport", "health", "geo"]


def generate_briefing() -> List[Dict[str, Any]]:
    """
    Genera il briefing giornaliero:
    1. Per ogni campo, fetcha e scorea le notizie
    2. Per le top, genera summary e why_matters via LLM
    3. Salva nel database
    4. Restituisce il risultato
    """
    print("\n" + "=" * 50)
    print("PULSE - Generazione Briefing")
    print("=" * 50)

    llm = get_llm_client()
    all_stories = []

    for field in FIELDS:
        agent = FieldAgent(field)
        articles = agent.run(limit=5)

        for article in articles:
            title = article.get("title", "Senza titolo").strip()
            url = article.get("url", "").strip()
            source_name = article.get("source", "Sconosciuto").strip()
            image_url = article.get("image_url")
            published = article.get("published", "")
            score = article.get("score", 5)

            raw_text = article.get("full_text", "") or article.get("summary", "") or ""

            print(f"    Generando summary per: {title[:50]}...")
            llm_result = llm.summarize_and_explain(
                title=title,
                text=raw_text,
                field=field
            )

            summary = llm_result.get("summary", "").strip()
            why_matters = llm_result.get("why_matters", "").strip()

            # Validazione: nessun campo puo essere vuoto/None
            if not summary:
                summary = raw_text[:300] + "..." if len(raw_text) > 50 else f"Articolo su {title[:100]}."
            if not why_matters:
                why_matters = f"Notizia rilevante nel settore {field}."

            story = {
                "field": field,
                "title": title,
                "url": url,
                "summary": summary,
                "why_matters": why_matters,
                "source_name": source_name,
                "image_url": image_url,
                "published_at": _parse_date(published),
                "is_trending": score >= 8,
            }
            all_stories.append(story)

    print(f"\nSalvataggio di {len(all_stories)} articoli nel database...")
    saved = _save_to_db(all_stories)
    print(f"Salvati {saved}/{len(all_stories)} articoli")

    return all_stories


def _save_to_db(stories: List[Dict[str, Any]]) -> int:
    """Salva i briefing nel database con gestione errori."""
    from app.database import Base, engine
    from app.models import Briefing, UserPreference  # noqa: F401

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    saved_count = 0

    try:
        for story in stories:
            if not story.get("title") or not story.get("url"):
                print(f"    Saltato: titolo o URL mancante")
                continue

            summary = story.get("summary") or "Riassunto non disponibile."
            why_matters = story.get("why_matters") or "Rilevanza non analizzata."

            briefing = Briefing(
                field=story["field"],
                title=story["title"],
                url=story["url"],
                summary=summary,
                why_matters=why_matters,
                source_name=story.get("source_name", "Sconosciuto"),
                image_url=story.get("image_url"),
                published_at=story.get("published_at"),
                is_trending=story.get("is_trending", False),
            )
            db.add(briefing)
            saved_count += 1

        db.commit()
        return saved_count

    except Exception as e:
        db.rollback()
        print(f"    Errore database: {e}")
        return 0
    finally:
        db.close()


def _parse_date(date_str: str) -> Optional[datetime]:
    """Parse date string in vari formati comuni."""
    if not date_str:
        return None

    formats = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S GMT",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S",
        "%d %b %Y %H:%M:%S",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue

    return None