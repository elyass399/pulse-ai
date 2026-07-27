#!/usr/bin/env python3
"""
Test script per verificare che tutte le librerie di Pulse siano installate correttamente.
"""

import sys

def test_import(name, import_path=None):
    """Prova a importare un modulo e stampa il risultato."""
    if import_path is None:
        import_path = name
    try:
        module = __import__(import_path)
        version = getattr(module, "__version__", "N/A")
        print(f"  ✅ {name:<25} v{version}")
        return True
    except ImportError as e:
        print(f"  ❌ {name:<25} ERRORE: {e}")
        return False
    except Exception as e:
        print(f"  ⚠️  {name:<25} IMPORT OK ma ERRORE: {e}")
        return True

def main():
    print("=" * 60)
    print("  PULSE — Test Import Librerie")
    print("=" * 60)

    results = []

    # --- API / runtime ---
    print("\n📡 API / Runtime:")
    results.append(test_import("fastapi"))
    results.append(test_import("uvicorn"))
    results.append(test_import("python-multipart", "multipart"))

    # --- Config / schemi ---
    print("\n⚙️  Config / Schemi:")
    results.append(test_import("pydantic"))
    results.append(test_import("pydantic-settings", "pydantic_settings"))
    results.append(test_import("python-dotenv", "dotenv"))

    # --- LLM ---
    print("\n🤖 LLM:")
    results.append(test_import("openai"))
    results.append(test_import("tenacity"))

    # --- Agent Framework ---
    print("\n🧠 Agent Framework:")
    results.append(test_import("langgraph"))
    results.append(test_import("langchain"))
    results.append(test_import("langchain-core", "langchain_core"))

    # --- MCP Protocol ---
    print("\n🔌 MCP Protocol:")
    results.append(test_import("mcp"))

    # --- Database ---
    print("\n🗄️  Database:")
    results.append(test_import("sqlalchemy"))
    results.append(test_import("alembic"))
    results.append(test_import("aiosqlite"))

    # --- Web Scraping & RSS ---
    print("\n🌐 Web Scraping & RSS:")
    results.append(test_import("feedparser"))
    results.append(test_import("requests"))
    results.append(test_import("beautifulsoup4", "bs4"))
    results.append(test_import("lxml"))

    # --- Async & HTTP ---
    print("\n⚡ Async & HTTP:")
    results.append(test_import("httpx"))
    results.append(test_import("aiohttp"))

    # --- Scheduler ---
    print("\n⏰ Scheduler:")
    results.append(test_import("apscheduler"))

    # --- Utilities ---
    print("\n🛠️  Utilities:")
    results.append(test_import("python-dateutil", "dateutil"))
    results.append(test_import("pytz"))
    results.append(test_import("numpy"))

    # --- Dev & Testing ---
    print("\n🧪 Dev & Testing:")
    results.append(test_import("pytest"))
    results.append(test_import("pytest-asyncio", "pytest_asyncio"))
    results.append(test_import("black"))
    results.append(test_import("isort"))

    # --- Riassunto ---
    print("\n" + "=" * 60)
    total = len(results)
    passed = sum(results)
    failed = total - passed

    print(f"  Totale:  {total}")
    print(f"  ✅ OK:    {passed}")
    print(f"  ❌ FAIL:  {failed}")

    if failed == 0:
        print("\n  🎉 TUTTE LE LIBRERIE SONO INSTALLATE CORRETTAMENTE!")
    else:
        print(f"\n  ⚠️  {failed} librerie mancanti. Installale con: pip install -r requirements.txt")

    print("=" * 60)

    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())