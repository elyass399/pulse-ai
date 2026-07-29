"""
Client MCP per connettersi ai server RSS e Web.
Usato dagli agenti LangGraph per chiamare i tool.
"""

from typing import Any, List, Dict, Optional  # FIX: aggiunto Optional


class MCPClient:
    """
    Client semplificato per chiamare i tool MCP.
    Chiama direttamente le funzioni Python.
    """

    def __init__(self):
        self.rss_feeds = {
            "tech": [
                "https://techcrunch.com/feed/",
                "https://news.ycombinator.com/rss",
                "https://www.theverge.com/rss/index.xml",
            ],
            "finance": [
                "https://feeds.bbci.co.uk/news/business/rss.xml",
            ],
            "sport": [
                "https://www.espn.com/espn/rss/news",
                "https://feeds.bbci.co.uk/sport/rss.xml",
            ],
            "health": [
                "https://www.who.int/rss-feeds/news-english.xml",
                "https://medicalxpress.com/rss-feed/",
            ],
            "geo": [
                "https://feeds.bbci.co.uk/news/world/rss.xml",
                "https://www.aljazeera.com/xml/rss/all.xml",
            ],
        }

    def fetch_news(self, field: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Fetch news da RSS per un campo.
        """
        import feedparser

        feeds = self.rss_feeds.get(field, [])
        articles = []

        for feed_url in feeds:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:limit]:
                    # Estrai media:content o enclosure se presente
                    image_url = None
                    if hasattr(entry, 'media_content') and entry.media_content:
                        image_url = entry.media_content[0].get('url')
                    elif hasattr(entry, 'enclosures') and entry.enclosures:
                        image_url = entry.enclosures[0].get('href')

                    # 🔒 FIX: Usa "or" per evitare None quando la chiave esiste ma è None
                    summary = (entry.get("summary") or "")[:500]

                    articles.append({
                        "title": entry.get("title", "No title"),
                        "url": entry.get("link", ""),
                        "published": entry.get("published", ""),
                        "summary": summary,
                        "source": feed.feed.get("title", feed_url),
                        "image_url": image_url,
                    })
            except Exception as e:
                print(f"Error parsing {feed_url}: {e}")
                continue

        return articles[:limit]

    def scrape_article(self, url: str) -> Dict[str, Any]:
        """
        Scrape full text e immagine da un URL.
        """
        import requests
        from bs4 import BeautifulSoup

        headers = {"User-Agent": "Pulse/1.0 (AI News Aggregator)"}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            # Cerca og:image
            og_image = None
            og_tag = soup.find("meta", property="og:image")
            if og_tag:
                og_image = og_tag.get("content")

            # Fallback: twitter:image
            if not og_image:
                twitter_tag = soup.find("meta", attrs={"name": "twitter:image"})
                if twitter_tag:
                    og_image = twitter_tag.get("content")

            article = (
                soup.find("article") or
                soup.find("div", class_="article-content") or
                soup.find("div", class_="post-content") or
                soup.find("main")
            )

            if article:
                paragraphs = article.find_all("p")
            else:
                paragraphs = soup.find_all("p")

            text = " ".join([p.get_text(strip=True) for p in paragraphs[:20]])
            text = text[:8000]

            return {
                "url": url,
                "title": soup.title.get_text(strip=True) if soup.title else "No title",
                "text": text,
                "image_url": og_image,
                "word_count": len(text.split()),
            }

        except Exception as e:
            return {"error": f"Scraping failed: {str(e)}"}

    def scrape_image(self, url: str) -> Optional[str]:
        """
        Scrape solo l'immagine principale (og:image) da un URL.
        """
        import requests
        from bs4 import BeautifulSoup

        headers = {"User-Agent": "Pulse/1.0 (AI News Aggregator)"}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")

            og_tag = soup.find("meta", property="og:image")
            if og_tag:
                return og_tag.get("content")

            twitter_tag = soup.find("meta", attrs={"name": "twitter:image"})
            if twitter_tag:
                return twitter_tag.get("content")

            return None
        except:
            return None


# Singleton
_mcp_client = None

def get_mcp_client() -> MCPClient:
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClient()
    return _mcp_client