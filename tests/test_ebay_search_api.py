import asyncio

from app.models.schemas import CardSearchRequest, EbayListing
from app.services import ebay_search


def test_parse_browse_items_maps_valid_items():
    items = [
        {
            "title": "Charizard PSA 10",
            "itemWebUrl": "https://www.ebay.co.uk/itm/123",
            "price": {"value": "199.99", "currency": "GBP"},
            "image": {"imageUrl": "https://example.com/img.jpg"},
            "condition": "Used",
            "itemEndDate": "2026-04-20T12:00:00.000Z",
            "shippingOptions": [
                {"shippingCost": {"value": "4.99", "currency": "GBP"}}
            ],
        }
    ]

    listings = ebay_search.parse_browse_items(items, sold=True)

    assert len(listings) == 1
    listing = listings[0]
    assert listing.title == "Charizard PSA 10"
    assert listing.price == 199.99
    assert listing.currency == "GBP"
    assert listing.listing_url == "https://www.ebay.co.uk/itm/123"
    assert listing.image_url == "https://example.com/img.jpg"
    assert listing.condition_text == "Used"
    assert listing.date_text == "2026-04-20T12:00:00.000Z"
    assert listing.shipping_text == "GBP 4.99 shipping"
    assert listing.sold is True


def test_search_ebay_listings_uses_api_when_credentials_present(monkeypatch):
    monkeypatch.setenv("EBAY_CLIENT_ID", "id")
    monkeypatch.setenv("EBAY_CLIENT_SECRET", "secret")

    sold_listing = EbayListing(
        title="Sold Item",
        price=50.0,
        currency="GBP",
        listing_url="https://example.com/sold",
        sold=True,
    )
    active_listing = EbayListing(
        title="Active Item",
        price=55.0,
        currency="GBP",
        listing_url="https://example.com/active",
        sold=False,
    )

    async def fake_fetch_sold_listings_via_api(query: str, max_results: int):
        assert "Pikachu" in query
        assert max_results == 5
        return [sold_listing]

    async def fake_fetch_unsold_listings_via_api(query: str, max_results: int):
        assert "Pikachu" in query
        assert max_results == 5
        return [active_listing]

    monkeypatch.setattr(
        ebay_search,
        "fetch_sold_listings_via_api",
        fake_fetch_sold_listings_via_api,
    )
    monkeypatch.setattr(
        ebay_search,
        "fetch_unsold_listings_via_api",
        fake_fetch_unsold_listings_via_api,
    )

    payload = CardSearchRequest(
        card_name="Pikachu",
        condition_type="raw",
        include_unsold=True,
        max_results=5,
    )

    sold, unsold, query = asyncio.run(ebay_search.search_ebay_listings(payload))

    assert "Pikachu" in query
    assert sold == [sold_listing]
    assert unsold == [active_listing]


def test_search_ebay_listings_falls_back_to_scraping_without_credentials(monkeypatch):
    monkeypatch.delenv("EBAY_CLIENT_ID", raising=False)
    monkeypatch.delenv("EBAY_CLIENT_SECRET", raising=False)

    sold_listing = EbayListing(
        title="Sold Item",
        price=50.0,
        currency="GBP",
        listing_url="https://example.com/sold",
        sold=True,
    )

    async def fake_fetch_sold_listings(query: str, max_results: int):
        assert "Charizard" in query
        assert max_results == 3
        return [sold_listing]

    monkeypatch.setattr(ebay_search, "fetch_sold_listings", fake_fetch_sold_listings)

    payload = CardSearchRequest(
        card_name="Charizard",
        condition_type="raw",
        include_unsold=True,
        max_results=3,
    )

    sold, unsold, query = asyncio.run(ebay_search.search_ebay_listings(payload))

    assert "Charizard" in query
    assert sold == [sold_listing]
    assert unsold == []
