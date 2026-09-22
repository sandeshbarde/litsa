"""
Test script: runs ONE Google Search API query.
Query: 'Salon Dubai Deira official website'
Safe for API key verification.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app.config import settings
from app.api.serpapi_google import GoogleSearchClient


def main():
    print("=" * 60)
    print("Dubai Lead Generator - SerpApi Google Search Test")
    print("=" * 60)

    if not settings.has_serpapi():
        print("ERROR: SERPAPI_API_KEY not set in .env")
        sys.exit(1)

    client = GoogleSearchClient()
    query = '"Salon" "Deira" Dubai official website'
    print(f"Running query: {query}")

    results = client.get_organic_results(query, num=5)

    if not results:
        print("No results returned.")
    else:
        print(f"\n{len(results)} organic results found:")
        print("-" * 60)
        for i, r in enumerate(results, 1):
            print(f"[{i}] {r.get('title', 'N/A')}")
            print(f"    URL: {r.get('link', 'N/A')}")
            print(f"    Snippet: {r.get('snippet', 'N/A')[:80]}...")
            print()

    print("=" * 60)
    print("Google Search test complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()
