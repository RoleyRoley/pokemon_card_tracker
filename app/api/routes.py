import hashlib
import os

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from app.models.schemas import CardSearchRequest, CardSearchResponse
from app.services.ebay_search import EbayBlockedError
from app.services.ebay_search import EbayApiAuthError, EbayApiError
from app.services.ebay_search import get_marketplace_id, has_ebay_api_credentials
from app.services.stats import calculate_listing_stats
from app.services.ebay_search import search_ebay_listings

EBAY_DELETION_ENDPOINT = "https://pokemon-card-tracker-api.onrender.com/webhooks/ebay/account-deletion"

router = APIRouter()


@router.get("/webhooks/ebay/account-deletion")
async def ebay_account_deletion_challenge(challenge_code: str = Query(...)):
    verification_token = os.getenv("EBAY_VERIFICATION_TOKEN", "")
    if not verification_token:
        raise HTTPException(status_code=500, detail="EBAY_VERIFICATION_TOKEN is not configured")

    hash_input = challenge_code + verification_token + EBAY_DELETION_ENDPOINT
    challenge_response = hashlib.sha256(hash_input.encode()).hexdigest()
    return JSONResponse(content={"challengeResponse": challenge_response})


@router.post("/webhooks/ebay/account-deletion")
async def ebay_account_deletion_notification():
    # Acknowledge the notification — no user data stored so nothing to delete
    return JSONResponse(status_code=200, content={})


@router.get("/status")
async def api_status():
    return {
        "ebay_api_credentials_configured": has_ebay_api_credentials(),
        "ebay_marketplace": get_marketplace_id(),
    }


@router.get("/debug/search")
async def debug_search(
    card_name: str = "Charizard",
    condition_type: str = "raw",
    bypass_challenge: bool = False,
):
    """Debug endpoint to see what's being returned"""
    try:
        from app.utils.query_builder import build_ebay_query
        from app.services.ebay_search import build_sold_search_url, fetch_html, is_ebay_challenge_page
        from bs4 import BeautifulSoup
        import re
        
        query_used = build_ebay_query(
            card_name=card_name,
            condition_type=condition_type,
            grader=None,
            grade=None,
        )
        
        url = build_sold_search_url(query_used)
        
        # Try to get HTML
        try:
            html = await fetch_html(url)
        except Exception as e:
            if bypass_challenge and "EbayBlockedError" in str(type(e)):
                # For debugging, fetch anyway by circumventing the check
                import httpx
                headers = {
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/124.0.0.0 Safari/537.36"
                    ),
                }
                async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                    response = await client.get(url, headers=headers)
                    html = response.text
            else:
                raise
        
        soup = BeautifulSoup(html, "html.parser")
        
        # Find listing patterns
        all_links = soup.find_all('a', href=True)
        item_links = [a for a in all_links if '/itm/' in a['href']]
        
        # Find prices
        price_patterns = re.findall(r'[£$]\s*[\d,]+\.?\d*', html)
        
        return {
            "card_name": card_name,
            "query_used": query_used,
            "search_url": url,
            "html_length": len(html),
            "item_links_found": len(item_links),
            "sample_item_links": [a['href'][:100] for a in item_links[:3]],
            "prices_found": len(price_patterns),
            "sample_prices": price_patterns[:5],
            "html_title": soup.title.string if soup.title else "NO TITLE",
            "has_s_item_class": "s-item" in html,
            "has_listing_container": "listing" in html.lower()[:10000],
        }
    except Exception as exc:
        import traceback
        return {
            "error": str(exc),
            "error_type": type(exc).__name__,
            "traceback": traceback.format_exc(),
        }


@router.post("/debug/search")
async def debug_search_post(payload: CardSearchRequest):
    """Debug endpoint to see what's being returned"""
    try:
        from app.utils.query_builder import build_ebay_query
        from app.services.ebay_search import build_sold_search_url, fetch_html
        
        query_used = build_ebay_query(
            card_name=payload.card_name,
            condition_type=payload.condition_type,
            grader=payload.grader,
            grade=payload.grade,
        )
        
        url = build_sold_search_url(query_used)
        html = await fetch_html(url)
        
        return {
            "card_name": payload.card_name,
            "query_used": query_used,
            "search_url": url,
            "html_length": len(html),
            "html_preview": html[:1000] if html else "NO HTML",
        }
    except Exception as exc:
        return {
            "error": str(exc),
            "error_type": type(exc).__name__,
        }


@router.post("/search", response_model=CardSearchResponse)
async def search_card_prices(payload: CardSearchRequest):
    try:
        sold_results, unsold_results, query_used = await search_ebay_listings(payload)
        stats = calculate_listing_stats(sold_results)

        return CardSearchResponse(
            query_used=query_used,
            sold_listings=sold_results,
            sold_stats=stats,
            unsold_listings=unsold_results,
        )
    except EbayBlockedError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except EbayApiAuthError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except EbayApiError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
