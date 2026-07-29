"""
Field Agent: specializzato per un campo.
Fetcha 5 notizie, le scorea, restituisce top 5 con immagini.
"""

from typing import List, Dict, Any
from app.mcp.client import get_mcp_client
from app.llm_client import get_llm_client


class FieldAgent:
    def __init__(self, field: str):
        self.field = field
        self.mcp = get_mcp_client()
        self.llm = get_llm_client()

    def run(self, limit: int = 5) -> List[Dict[str, Any]]:
        print(f"\n  [{self.field.upper()}] Fetching news...")

        articles = self.mcp.fetch_news(self.field, limit=limit)
        print(f"  [{self.field.upper()}] Found {len(articles)} articles")

        if not articles:
            return []

        scored = []
        for article in articles:
            # FIX: Assicurati che summary non sia None prima di passarlo al LLM
            safe_summary = article.get("summary") or ""

            score = self.llm.score_relevance(
                title=article["title"],
                summary=safe_summary,
                field=self.field
            )
            article["score"] = score
            scored.append(article)
            print(f"    - {article['title'][:50]}... -> Score: {score}")

        scored.sort(key=lambda x: x["score"], reverse=True)
        top5 = scored[:5]

        # Scrape full text e immagine per top 3
        for i, article in enumerate(top5[:3]):
            if article.get("url"):
                scraped = self.mcp.scrape_article(article["url"])
                article["full_text"] = scraped.get("text", article.get("summary", ""))

                # Se non c'e image_url dal RSS, prova dallo scraping
                if not article.get("image_url") and scraped.get("image_url"):
                    article["image_url"] = scraped.get("image_url")

        # Per gli altri 2, prova solo a scrapeare l'immagine
        for article in top5[3:]:
            if article.get("url") and not article.get("image_url"):
                image = self.mcp.scrape_image(article["url"])
                if image:
                    article["image_url"] = image

        print(f"  [{self.field.upper()}] Top 5 selected")
        return top5