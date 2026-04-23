import os
import re
from datetime import datetime, timezone
from urllib.parse import quote_plus

import httpx

from app.models.schemas import CardSearchRequest, EbayListing
from app.services.parsers import parse_sold_listings_from_html
from app.utils.query_builder import build_ebay_query


# Constants for eBay API and scraping

EBAY_UK_SEARCH_URL = "https://www.ebay.co.uk/sch/i.html"
EBAY_OAUTH_URL = "https://api.ebay.com/identity/v1/oauth2/token"
EBAY_BROWSE_SEARCH_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"

EBAY_CLIENT_ID_ENV = "EBAY_CLIENT_ID"
EBAY_CLIENT_SECRET_ENV = "EBAY_CLIENT_SECRET"
EBAY_MARKETPLACE_ID_ENV = "EBAY_MARKETPLACE_ID"


class EbayBlockedError(RuntimeError):
    pass


class EbayApiAuthError(RuntimeError):
    pass


class EbayApiError(RuntimeError):
    pass


def _extract_ebay_error_details(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        text = (response.text or "").strip()
        return text[:300] if text else "No response body"

    if isinstance(payload, dict):
        errors = payload.get("errors")
        if isinstance(errors, list) and errors:
            first = errors[0] if isinstance(errors[0], dict) else {}
            code = first.get("errorId") or first.get("errorCode") or "unknown"
            message = first.get("message") or first.get("longMessage") or str(first)
            return f"code={code}, message={message}"

        error = payload.get("error")
        description = payload.get("error_description")
        if error or description:
            return f"error={error}, description={description}"

        return str(payload)[:300]

    return str(payload)[:300]


def _tokenize_text(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _required_card_terms(card_name: str) -> set[str]:
    stop_words = {
        "pokemon",
        "card",
        "cards",
        "tcg",
        "the",
        "and",
        "for",
        "with",
    }
    terms = _tokenize_text(card_name)
    # Keep meaningful tokens and set numbers while avoiding overly broad words.
    return {
        term
        for term in terms
        if term not in stop_words and (len(term) >= 3 or term.isdigit())
    }


def _is_relevant_listing_title(title: str, required_terms: set[str]) -> bool:
    if not required_terms:
        return True
    title_terms = _tokenize_text(title)
    return required_terms.issubset(title_terms)


def _filter_relevant_listings(listings: list[EbayListing], card_name: str) -> list[EbayListing]:
    required_terms = _required_card_terms(card_name)
    return [
        listing
        for listing in listings
        if _is_relevant_listing_title(listing.title, required_terms)
    ]


def _parse_iso_datetime(date_text: str | None) -> datetime:
    if not date_text:
        return datetime.min.replace(tzinfo=timezone.utc)

    normalized = date_text.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _sort_listings_by_date_desc(listings: list[EbayListing]) -> list[EbayListing]:
    return sorted(
        listings,
        key=lambda listing: _parse_iso_datetime(listing.date_text),
        reverse=True,
    )




def _get_api_credentials() -> tuple[str | None, str | None]:
    return os.getenv(EBAY_CLIENT_ID_ENV), os.getenv(EBAY_CLIENT_SECRET_ENV)


def has_ebay_api_credentials() -> bool:
    client_id, client_secret = _get_api_credentials()
    return bool(client_id and client_secret)


def get_marketplace_id() -> str:
    return os.getenv(EBAY_MARKETPLACE_ID_ENV, "EBAY_GB")


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

# Oauth token fetching and API search functions
async def fetch_oauth_token(client_id: str, client_secret: str) -> str:
    data = {
        "grant_type": "client_credentials",
        "scope": "https://api.ebay.com/oauth/api_scope",
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(
            EBAY_OAUTH_URL,
            data=data,
            headers=headers,
            auth=(client_id, client_secret),
        )

    if response.status_code >= 400:
        details = _extract_ebay_error_details(response)
        raise EbayApiAuthError(
            "Unable to authenticate with eBay API. Check EBAY_CLIENT_ID and "
            f"EBAY_CLIENT_SECRET. HTTP {response.status_code}. eBay response: {details}"
        )

    token = response.json().get("access_token")
    if not token:
        raise EbayApiAuthError("eBay OAuth response did not include access_token")

    return token


def _price_to_float(price_data: dict | None) -> tuple[float, str]:
    # Convert eBay API price dicts like {"value": "123.45", "currency": "GBP"} into (123.45, "GBP")
    if not price_data:
        return 0.0, "GBP"

    value = price_data.get("value")
    currency = price_data.get("currency", "GBP")

    try:
        return float(value), str(currency)
    except (TypeError, ValueError):
        return 0.0, str(currency)


def _shipping_text(item: dict) -> str | None:
    shipping_options = item.get("shippingOptions") or []
    if not shipping_options:
        return None

    first_option = shipping_options[0]
    shipping_cost = first_option.get("shippingCost") or {}
    value, currency = _price_to_float(shipping_cost)
    if value <= 0:
        return "Free shipping"
    return f"{currency} {value:.2f} shipping"


def _listing_date_text(item: dict, sold: bool) -> str | None:
    # eBay responses are inconsistent across listing types; use a safe fallback chain.
    if sold:
        return (
            item.get("itemEndDate")
            or item.get("itemCreationDate")
            or item.get("itemOriginDate")
            or item.get("listingDate")
        )
    return (
        item.get("itemCreationDate")
        or item.get("itemOriginDate")
        or item.get("listingDate")
    )


def parse_browse_items(items: list[dict], sold: bool) -> list[EbayListing]:
    parsed: list[EbayListing] = []

    for item in items:
        title = (item.get("title") or "").strip()
        listing_url = (item.get("itemWebUrl") or "").strip()
        image_url = (item.get("image") or {}).get("imageUrl")
        condition_text = item.get("condition")
        date_text = _listing_date_text(item, sold)
        price, currency = _price_to_float(item.get("price"))

        if not title or not listing_url or price <= 0:
            continue

        parsed.append(
            EbayListing(
                title=title,
                price=price,
                currency=currency,
                listing_url=listing_url,
                image_url=image_url,
                condition_text=condition_text,
                date_text=date_text,
                shipping_text=_shipping_text(item),
                sold=sold,
            )
        )

    return parsed


async def browse_search(
    # This function is used by both sold and unsold API search functions, with the sold_only flag controlling the filter.
    token: str,
    query: str,
    sold_only: bool,
    max_results: int,
) -> list[EbayListing]:
    headers = {
        "Authorization": f"Bearer {token}",
        "X-EBAY-C-MARKETPLACE-ID": get_marketplace_id(),
        "Accept": "application/json",
    }
    params = {
        "q": query,
        "limit": max(1, min(max_results, 200)),
        "filter": f"soldItemsOnly:{str(sold_only).lower()}",
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(EBAY_BROWSE_SEARCH_URL, headers=headers, params=params)

    if response.status_code >= 400:
        details = _extract_ebay_error_details(response)
        raise EbayApiError(
            f"eBay Browse API search failed. HTTP {response.status_code}. eBay response: {details}"
        )

    data = response.json()
    item_summaries = data.get("itemSummaries") or []
    return parse_browse_items(item_summaries, sold=sold_only)


async def fetch_sold_listings_via_api(query: str, max_results: int) -> list[EbayListing]:
    # fetch sold listings using the eBay Browse API. 
    client_id, client_secret = _get_api_credentials()
    if not client_id or not client_secret:
        raise EbayApiAuthError("Missing eBay API credentials")

    token = await fetch_oauth_token(client_id, client_secret)
    return await browse_search(
        token=token,
        query=query,
        sold_only=True,
        max_results=max_results,
    )


async def fetch_unsold_listings_via_api(query: str, max_results: int) -> list[EbayListing]:
    client_id, client_secret = _get_api_credentials()
    if not client_id or not client_secret:
        raise EbayApiAuthError("Missing eBay API credentials")

    token = await fetch_oauth_token(client_id, client_secret)
    return await browse_search(
        token=token,
        query=query,
        sold_only=False,
        max_results=max_results,
    )


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

    if has_ebay_api_credentials():
        sold_results = await fetch_sold_listings_via_api(
            query=query_used,
            max_results=payload.max_results,
        )
        sold_results = _sort_listings_by_date_desc(
            _filter_relevant_listings(sold_results, payload.card_name)
        )[: payload.max_results]

        unsold_results: list[EbayListing] = []
        if payload.include_unsold:
            unsold_results = await fetch_unsold_listings_via_api(
                query=query_used,
                max_results=payload.max_results,
            )
            unsold_results = _sort_listings_by_date_desc(
                _filter_relevant_listings(unsold_results, payload.card_name)
            )[: payload.max_results]
        return sold_results, unsold_results, query_used

    sold_results = await fetch_sold_listings(query=query_used, max_results=payload.max_results)
    sold_results = _filter_relevant_listings(sold_results, payload.card_name)[: payload.max_results]
    unsold_results = []

    return sold_results, unsold_results, query_used
