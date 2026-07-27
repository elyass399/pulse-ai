"""
Test rapido per i MCP servers senza avviarli come processi separati.
"""

import json
import feedparser
import requests
from bs4 import BeautifulSoup

# --- Test RSS ---
print("=" * 50)
print("TEST RSS - TechCrunch")
print("=" * 50)

feed = feedparser.parse("https://techcrunch.com/feed/")
for i, entry in enumerate(feed.entries[:3]):
    print(f"\n{i+1}. {entry.title}")
    print(f"   Link: {entry.link}")
    print(f"   Published: {entry.get('published', 'N/A')}")
    print(f"   Summary: {entry.get('summary', '')[:100]}...")

# --- Test Web Scraping ---
print("\n" + "=" * 50)
print("TEST WEB SCRAPER - Hacker News")
print("=" * 50)

url = "https://news.ycombinator.com"
headers = {"User-Agent": "Pulse/1.0"}

response = requests.get(url, headers=headers, timeout=10)
soup = BeautifulSoup(response.text, "html.parser")

headlines = []
for link in soup.find_all("a", href=True):
    text = link.get_text(strip=True)
    if text and 15 < len(text) < 200:
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

for i, h in enumerate(unique[:5]):
    print(f"\n{i+1}. {h['title']}")
    print(f"   URL: {h['url']}")

print("\n✅ Test completato!")