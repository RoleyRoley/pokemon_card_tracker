#!/usr/bin/env python3
"""Test script to diagnose eBay setup issues"""

import os
import sys
import asyncio

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

from app.services.ebay_search import has_ebay_api_credentials, _get_api_credentials


async def main():
    print("=" * 60)
    print("EBAY SETUP DIAGNOSTIC TEST")
    print("=" * 60)
    
    # Check credentials
    client_id, client_secret = _get_api_credentials()
    
    print(f"\n1. API Credentials:")
    print(f"   EBAY_CLIENT_ID set: {bool(client_id)}")
    print(f"   EBAY_CLIENT_SECRET set: {bool(client_secret)}")
    print(f"   Has both credentials: {has_ebay_api_credentials()}")
    
    if has_ebay_api_credentials():
        print(f"\n   ✓ Official eBay API will be used (more reliable)")
    else:
        print(f"\n   ✗ No API credentials found")
        print(f"     Will fall back to web scraping (eBay is blocking these)")
        print(f"\n2. TO FIX:")
        print(f"   You need to:")
        print(f"   a) Go to https://developer.ebay.com/")
        print(f"   b) Create an application")
        print(f"   c) Get your Client ID and Client Secret")
        print(f"   d) Set environment variables:")
        print(f"      - EBAY_CLIENT_ID")
        print(f"      - EBAY_CLIENT_SECRET")
        print(f"\n   Quick test: In PowerShell run:")
        print(f'      $env:EBAY_CLIENT_ID = "your_client_id"')
        print(f'      $env:EBAY_CLIENT_SECRET = "your_client_secret"')
        print(f"      uvicorn app.main:app --reload")
    
    # Test a search with retries
    if not has_ebay_api_credentials():
        print(f"\n3. Testing web scraping with retries...")
        print(f"   Attempting to fetch Charizard listings...")
        
        from app.services.ebay_search import fetch_sold_listings
        from app.utils.query_builder import build_ebay_query
        
        try:
            query = build_ebay_query("Charizard", "raw", None, None)
            listings = await fetch_sold_listings(query, 10)
            print(f"   ✓ Got {len(listings)} listings!")
            if listings:
                print(f"   First listing: {listings[0].title} - {listings[0].price}")
        except Exception as e:
            print(f"   ✗ Failed: {e}")
            print(f"\n   This means eBay is blocking our requests.")
            print(f"   You NEED to set up API credentials to make this work locally.")


if __name__ == "__main__":
    asyncio.run(main())
