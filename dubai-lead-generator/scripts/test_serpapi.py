"""
Test script: runs ONE SerpApi Google Maps query.
Query: 'salons in Deira Dubai'
Does NOT start a full job. Safe to run for API verification.
"""

import sys
import os
import json

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app.config import settings
from app.api.serpapi_maps import GoogleMapsClient


def main():
    print("=" * 60)
    print("Dubai Lead Generator - SerpApi Maps Test")
    print("=" * 60)

    if not settings.has_serpapi():
        print("ERROR: SERPAPI_API_KEY not set in .env")
        print("Set it in your .env file and try again.")
        sys.exit(1)

    print(f"SerpApi key detected: {'*' * 8}{settings.serpapi_api_key[-4:]}")
    print()

    client = GoogleMapsClient()
    query = "salons in Deira Dubai"
    print(f"Running query: '{query}'")
    print("Calling SerpApi Google Maps...")

    results = client.search_businesses(query=query, max_results=5)

    if not results:
        print("No results returned. Check your API key and quota.")
        sys.exit(1)

    print(f"\n{len(results)} results found:")
    print("-" * 60)
    for i, biz in enumerate(results, 1):
        print(f"\n[{i}] {biz.get('business_name', 'N/A')}")
        print(f"    Address : {biz.get('address', 'N/A')}")
        print(f"    Phone   : {biz.get('phone', 'N/A')}")
        print(f"    Website : {biz.get('website', 'N/A')}")
        print(f"    Rating  : {biz.get('google_rating', 'N/A')}")
        print(f"    Reviews : {biz.get('google_review_count', 'N/A')}")
        print(f"    Maps URL: {biz.get('google_maps_url', 'N/A')}")
        print(f"    Place ID: {biz.get('place_id', 'N/A')}")
        print(f"    Data ID : {biz.get('data_id', 'N/A')}")

    print("\n" + "=" * 60)
    print("Test PASSED. SerpApi is working correctly.")
    print("=" * 60)


if __name__ == "__main__":
    main()
