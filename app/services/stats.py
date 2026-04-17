from statistics import mean, median
from app.models.schemas import ListingStats

# Service function to calculate statistics for a list of eBay listings
def calculate_listing_stats(listings):
    if not listings:
        return ListingStats(count=0)

    prices = [listing.price for listing in listings if listing.price is not None]

    if not prices:
        return ListingStats(count=len(listings))

    return ListingStats(
        count=len(listings),
        lowest_price=min(prices),
        highest_price=max(prices),
        average_price=round(mean(prices), 2),
        median_price=round(median(prices), 2)
    )