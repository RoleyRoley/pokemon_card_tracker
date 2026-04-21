from app.services.parsers import parse_price, parse_sold_listings_from_html


SAMPLE_HTML = """
<ul>
  <li class="s-item">
    <div class="s-item__title">Charizard 4/102 Base Set</div>
    <span class="s-item__price">£123.45</span>
    <a class="s-item__link" href="https://example.com/listing-1">View</a>
    <img class="s-item__image-img" src="https://example.com/image-1.jpg" />
    <span class="SECONDARY_INFO">Used</span>
    <div class="s-item__title--tagblock">
      <span class="POSITIVE">Sold Apr 20, 2026</span>
    </div>
    <span class="s-item__shipping">+£2.99 postage</span>
  </li>
  <li class="s-item">
    <div class="s-item__title">Shop on eBay</div>
    <span class="s-item__price">£9.99</span>
    <a class="s-item__link" href="https://example.com/ad">View</a>
  </li>
  <li class="s-item">
    <div class="s-item__title">Blastoise Base Set</div>
    <span class="s-item__price">Invalid</span>
    <a class="s-item__link" href="https://example.com/listing-2">View</a>
  </li>
  <li class="s-item">
    <div class="s-item__title">Venusaur Base Set</div>
    <span class="s-item__price">£88.00</span>
    <a class="s-item__link" href="https://example.com/listing-3">View</a>
  </li>
</ul>
"""


def test_parse_price_extracts_numeric_value_and_gbp_currency():
    price, currency = parse_price("£1,234.56")

    assert price == 1234.56
    assert currency == "GBP"


def test_parse_price_returns_zero_for_unparseable_values():
    price, currency = parse_price("not a price")

    assert price == 0.0
    assert currency == "GBP"


def test_parse_sold_listings_from_html_skips_ads_and_invalid_prices():
    listings = parse_sold_listings_from_html(SAMPLE_HTML, max_results=10)

    assert len(listings) == 2

    first_listing = listings[0]
    assert first_listing.title == "Charizard 4/102 Base Set"
    assert first_listing.price == 123.45
    assert first_listing.currency == "GBP"
    assert first_listing.listing_url == "https://example.com/listing-1"
    assert first_listing.image_url == "https://example.com/image-1.jpg"
    assert first_listing.condition_text == "Used"
    assert first_listing.date_text == "Sold Apr 20, 2026"
    assert first_listing.shipping_text == "+£2.99 postage"
    assert first_listing.sold is True

    second_listing = listings[1]
    assert second_listing.title == "Venusaur Base Set"
    assert second_listing.price == 88.0


def test_parse_sold_listings_from_html_respects_max_results():
    listings = parse_sold_listings_from_html(SAMPLE_HTML, max_results=1)

    assert len(listings) == 1
    assert listings[0].title == "Charizard 4/102 Base Set"