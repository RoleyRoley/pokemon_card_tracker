from fastapi import APIRouter, HTTPException

from app.models.schemas import CardSearchRequest, CardSearchResponse
from app.services.ebay_search import EbayBlockedError
from app.services.ebay_search import EbayApiAuthError, EbayApiError
from app.services.ebay_search import get_marketplace_id, has_ebay_api_credentials
from app.services.stats import calculate_listing_stats
from app.services.ebay_search import search_ebay_listings

router = APIRouter()


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
