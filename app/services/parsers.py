import re
from bs4 import BeautifulSoup
from app.models.schemas import EbayListing

def parse_price(price_text: str) -> tuple[float, str]:
    # Convert strings like '£123.45' into (123.45, 'GBP')
    
    if not price_text:
        return 0.0, "GBP"

    currency = "GBP"
    cleaned = price_text.strip()

    if "£" in cleaned:
        currency = "GBP"

    match = re.search(r"(\d[\d,]*\.?\d*)", cleaned.replace(",", ""))
    if not match:
        return 0.0, currency

    return float(match.group(1)), currency


def parse_sold_listings_from_html(html: str, max_results: int) -> list[EbayListing]:
    soup = BeautifulSoup(html, "html.parser")
    listings = []

    item_cards = soup.select("li.s-item")
    
    for card in item_cards:
        title_el = card.select_one(".s-item__title")
        price_el = card.select_one(".s-item__price")
        link_el = card.select_one(".s-item__link")
        image_el = card.select_one(".s-item__image-img")
        subtitle_el = card.select_one(".SECONDARY_INFO")
        date_el = card.select_one(".s-item__title--tagblock .POSITIVE")
        shipping_el = card.select_one(".s-item__shipping, .s-item__logisticsCost")

        if not title_el or not price_el or not link_el:
            continue
        
        title = title_el.get_text(strip=True)

        # Skip placeholder/ad cards
        if not title or title.lower() == "shop on ebay":
            continue

        price, currency = parse_price(price_el.get_text(" ", strip=True))
        listing_url = link_el.get("href", "").strip()
        image_url = image_el.get("src", "").strip() if image_el else None
        condition_text = subtitle_el.get_text(strip=True) if subtitle_el else None
        date_text = date_el.get_text(strip=True) if date_el else None
        shipping_text = shipping_el.get_text(" ", strip=True) if shipping_el else None

        # Ignore broken price rows
        if price <= 0:
            continue

        listings.append(
            EbayListing(
                title=title,
                price=price,
                currency=currency,
                listing_url=listing_url,
                image_url=image_url,
                condition_text=condition_text,
                date_text=date_text,
                shipping_text=shipping_text,
                sold=True,
            )
        )

        if len(listings) >= max_results:
            break

    return listings