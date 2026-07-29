"""
MCP Server: RSS Feed Reader
Espone tool per fetchare notizie da feed RSS per ogni campo.
"""

import json
import feedparser
from datetime import datetime
from typing import List, Dict, Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent


# Feed RSS per campo
RSS_FEEDS = {
    "tech": [
        "https://techcrunch.com/feed/",
        "https://news.ycombinator.com/rss",
        "https://www.theverge.com/rss/index.xml",
    ],
    "finance": [
        "https://feeds.bbci.co.uk/news/business/rss.xml",
        "https://www.reutersagency.com/feed/?best-topics=business-finance",
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


app = Server("rss-server")


@app.list_tools()
async def list_tools() -> List[Tool]:
    """Dichiara i tool disponibili."""
    tools = []
    for field in RSS_FEEDS.keys():
        tools.append(
            Tool(
                name=f"fetch_{field}_news",
                description=f"Fetch latest {field} news from RSS feeds",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Max number of articles to return",
                            "default": 10,
                        }
                    },
                },
            )
        )
    return tools


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Esegue il tool richiesto."""
    # Estrai campo dal nome (es. "fetch_tech_news" → "tech")
    field = name.replace("fetch_", "").replace("_news", "")

    if field not in RSS_FEEDS:
        return [TextContent(type="text", text=json.dumps({"error": f"Unknown field: {field}"}))]

    limit = arguments.get("limit", 10) if isinstance(arguments, dict) else 10

    articles = []
    for feed_url in RSS_FEEDS[field]:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:limit]:
                # 🔒 FIX: Usa "or" per evitare None
                summary = (entry.get("summary") or "")[:500]

                articles.append({
                    "title": entry.get("title", "No title"),
                    "link": entry.get("link", ""),
                    "published": entry.get("published", ""),
                    "summary": summary,
                    "source": feed.feed.get("title", feed_url),
                })
        except Exception as e:
            print(f"Error parsing {feed_url}: {e}")
            continue

    # Ordina per data (più recenti prima) e limita
    articles = articles[:limit]

    return [TextContent(type="text", text=json.dumps({
        "field": field,
        "count": len(articles),
        "articles": articles,
    }, ensure_ascii=False))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())