from fastapi import APIRouter

from app.models.schemas import CardSearchRequest, CardSearchResponse
from app.services.stats import calculate_listing_stats

router = APIRouter()


@router.post("/search", response_model=CardSearchResponse)
async def search_card_prices(payload: CardSearchRequest):
    sold_listings = []
    stats = calculate_listing_stats(sold_listings)

    return CardSearchResponse(
        query_used=payload.card_name,
        sold_listings=sold_listings,
        sold_stats=stats,
        unsold_listings=[],
    )