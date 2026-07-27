# test_orchestrator.py
from app.agents import generate_briefing

briefing = generate_briefing()

print("\n" + "=" * 50)
print("📰 FINAL BRIEFING")
print("=" * 50)

for story in briefing:
    print(f"\n🔥 [{story['field'].upper()}] {story['title']}")
    print(f"   Source: {story['source_name']}")
    print(f"   URL: {story['url']}")
    print(f"   Summary: {story['summary'][:100]}...")
    print(f"   Why: {story['why_matters'][:100]}...")