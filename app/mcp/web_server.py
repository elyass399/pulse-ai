"""
MCP Server: Web Scraper
Espone tool per scraping di articoli e homepage.
"""

import json
import requests
from typing import List, Any

from bs4 import BeautifulSoup
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent


app = Server("web-server")


@app.list_tools()
async def list_tools() -> List[Tool]:
    """Dichiara i tool disponibili."""
    return [
        Tool(
            name="scrape_article",
            description="Scrape full text from a news article URL",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL of the article to scrape",
                    }
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="extract_headlines",
            description="Extract headline links from a news homepage",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL of the homepage",
                    }
                },
                "required": ["url"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Esegue il tool richiesto."""
    if isinstance(arguments, dict):
        url = arguments.get("url", "")
    else:
        return [TextContent(type="text", text=json.dumps({"error": "Invalid arguments"}))]
    
    if not url:
        return [TextContent(type="text", text=json.dumps({"error": "URL required"}))]
    
    headers = {
        "User-Agent": "Pulse/1.0 (AI News Aggregator; Open Source)"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        if name == "scrape_article":
            # Estrai testo articolo
            # Prova vari selettori comuni
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
            text = text[:8000]  # limita per LLM
            
            result = {
                "url": url,
                "title": soup.title.get_text(strip=True) if soup.title else "No title",
                "text": text,
                "word_count": len(text.split()),
            }
            
        elif name == "extract_headlines":
            # Estrai headline links
            headlines = []
            for link in soup.find_all("a", href=True):
                text = link.get_text(strip=True)
                if text and len(text) > 15 and len(text) < 200:
                    headlines.append({
                        "title": text,
                        "url": link["href"] if link["href"].startswith("http") else url + link["href"],
                    })
            
            # Rimuovi duplicati
            seen = set()
            unique = []
            for h in headlines:
                if h["title"] not in seen:
                    seen.add(h["title"])
                    unique.append(h)
            
            result = {
                "url": url,
                "count": len(unique[:20]),
                "headlines": unique[:20],
            }
        else:
            result = {"error": f"Unknown tool: {name}"}
            
    except requests.RequestException as e:
        result = {"error": f"Request failed: {str(e)}"}
    except Exception as e:
        result = {"error": f"Scraping failed: {str(e)}"}
    
    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())