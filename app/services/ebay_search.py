from urllib.parse import quote_plus

import httpx

from app.models.schemas import CardSearchRequest, EbayListing
from app.services.parsers import parse_sold_listings_from_html
from app.utils.query_builder import build_ebay_query


EBAY_UK_SEARCH_URL = "https://www.ebay.co.uk/sch/i.html"


class EbayBlockedError(RuntimeError):
    pass


def build_sold_search_url(query: str) -> str:
    """
    _nkw = keyword
    LH_Sold = sold items
    LH_Complete = completed listings
    _sop = sort order (recently ended often works for sold-style searches)
    """
    return (
        f"{EBAY_UK_SEARCH_URL}"
        f"?_nkw={quote_plus(query)}"
        f"&LH_Sold=1"
        f"&LH_Complete=1"
        f"&_sop=13"
    )


async def fetch_html(url: str) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-GB,en;q=0.9",
    }

    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        html = response.text

        if is_ebay_challenge_page(html, str(response.url)):
            raise EbayBlockedError(
                "eBay blocked the automated request with a browser challenge. "
                "Try again later or use a browser-assisted scraping approach."
            )

        return html


def is_ebay_challenge_page(html: str, final_url: str) -> bool:
    lowered_html = html.lower()
    lowered_url = final_url.lower()

    return any(
        marker in lowered_html or marker in lowered_url
        for marker in (
            "pardon our interruption",
            "checking your browser before you access ebay",
            "/splashui/challenge",
        )
    )


async def fetch_sold_listings(query: str, max_results: int) -> list[EbayListing]:
    url = build_sold_search_url(query)
    html = await fetch_html(url)
    return parse_sold_listings_from_html(html, max_results)


async def search_ebay_listings(
    payload: CardSearchRequest,
) -> tuple[list[EbayListing], list[EbayListing], str]:
    query_used = build_ebay_query(
        card_name=payload.card_name,
        condition_type=payload.condition_type,
        grader=payload.grader,
        grade=payload.grade,
    )

    sold_results = await fetch_sold_listings(
        query=query_used,
        max_results=payload.max_results,
    )

    # Unsold comes in Stage 3
    unsold_results: list[EbayListing] = []

    return sold_results, unsold_results, query_used