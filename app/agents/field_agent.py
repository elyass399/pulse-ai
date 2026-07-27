"""
Field Agent: specializzato per un campo (tech, finance, sport, health, geo).
Fetcha 5 notizie da RSS, le scorea con LLM, restituisce top 5.
"""

from typing import List, Dict, Any
from app.mcp.client import get_mcp_client
from app.llm_client import get_llm_client


class FieldAgent:
    """
    Agente specializzato per un campo.
    Fetcha 5 notizie per campo per avere 25 totali nella tabella.
    """

    def __init__(self, field: str):
        self.field = field
        self.mcp = get_mcp_client()
        self.llm = get_llm_client()

    def run(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Pipeline completa: fetch → score → filter top 5.
        """
        print(f"\n  🔍 [{self.field.upper()}] Fetching news...")

        # 1. Fetch 5 notizie da RSS
        articles = self.mcp.fetch_news(self.field, limit=limit)
        print(f"  📰 [{self.field.upper()}] Found {len(articles)} articles")

        if not articles:
            return []

        # 2. Score rilevanza con LLM — 5 chiamate
        scored = []
        for article in articles:
            score = self.llm.score_relevance(
                title=article["title"],
                summary=article.get("summary", ""),
                field=self.field
            )
            article["score"] = score
            scored.append(article)
            print(f"    • {article['title'][:50]}... → Score: {score}")

        # 3. Ordina per score e prendi top 5
        scored.sort(key=lambda x: x["score"], reverse=True)
        top5 = scored[:5]

        # 4. Scrape full text SOLO per il top 1 (risparmio chiamate)
        if top5 and top5[0].get("url"):
            scraped = self.mcp.scrape_article(top5[0]["url"])
            top5[0]["full_text"] = scraped.get("text", top5[0].get("summary", ""))

        print(f"  ✅ [{self.field.upper()}] Top 5 selected")
        return top5