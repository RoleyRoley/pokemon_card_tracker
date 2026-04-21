from app.models.schemas import EbayListing
from app.services.stats import calculate_listing_stats


def test_calculate_listing_stats_returns_empty_stats_for_no_listings():
    stats = calculate_listing_stats([])

    assert stats.count == 0
    assert stats.lowest_price is None
    assert stats.highest_price is None
    assert stats.average_price is None
    assert stats.median_price is None


def test_calculate_listing_stats_computes_summary_values():
    listings = [
        EbayListing(
            title="Card A",
            price=10.0,
            currency="GBP",
            listing_url="https://example.com/a",
            sold=True,
        ),
        EbayListing(
            title="Card B",
            price=20.0,
            currency="GBP",
            listing_url="https://example.com/b",
            sold=True,
        ),
        EbayListing(
            title="Card C",
            price=30.0,
            currency="GBP",
            listing_url="https://example.com/c",
            sold=True,
        ),
    ]

    stats = calculate_listing_stats(listings)

    assert stats.count == 3
    assert stats.lowest_price == 10.0
    assert stats.highest_price == 30.0
    assert stats.average_price == 20.0
    assert stats.median_price == 20.0