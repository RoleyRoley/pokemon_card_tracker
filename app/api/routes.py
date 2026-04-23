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
