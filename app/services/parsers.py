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

    # Try multiple selector approaches for eBay's various HTML structures
    
    # Approach 1: Standard s-item class (older eBay)
    item_cards = soup.select("li.s-item")
    
    # Approach 2: Modern div-based layout
    if not item_cards:
        item_cards = soup.select("div[data-component-type='s-search-result']")
    
    # Approach 3: Look for common eBay listing patterns
    if not item_cards:
        # Find divs/lis containing both a price and an item link
        possible_cards = soup.find_all(['div', 'li'], limit=200)
        item_cards = []
        for card in possible_cards:
            # Check if this element likely contains listing data
            price_el = card.find(['span', 'div'], string=lambda s: s and ('£' in str(s) or '$' in str(s)))
            link_el = card.find('a', href=lambda h: h and '/itm/' in h) if price_el else None
            if price_el and link_el:
                item_cards.append(card)
                if len(item_cards) >= max_results * 2:
                    break
    
    print(f"DEBUG: Found {len(item_cards)} potential listing cards")
    
    for card in item_cards:
        try:
            # Try to find title
            title_el = card.select_one(".s-item__title") or card.find(['a', 'h3'])
            
            # Try to find price
            price_el = card.select_one(".s-item__price") or card.find(string=lambda s: s and ('£' in str(s) or '$' in str(s)))
            
            # Try to find link
            link_el = card.select_one(".s-item__link") or card.find('a', href=lambda h: h and '/itm/' in h)
            
            # Try to find image
            image_el = card.select_one(".s-item__image-img") or card.find('img')
            
            # Try to find shipping
            shipping_el = card.select_one(".s-item__shipping") or card.find(string=lambda s: s and 'shipping' in str(s).lower())
            
            # Try to find date
            date_el = card.select_one(".s-item__date") or card.find(string=lambda s: s and ('day' in str(s).lower() or 'hour' in str(s).lower() or 'sold' in str(s).lower()))
            
            # Basic validation
            if not title_el or not price_el or not link_el:
                continue
            
            title = title_el.get_text(strip=True)
            if not title or len(title) < 3:
                continue
            
            # Skip ads and non-product cards
            if 'shop on ebay' in title.lower() or 'sponsored' in str(card).lower():
                continue
            
            price, currency = parse_price(price_el.get_text(strip=True) if isinstance(price_el, type(title_el)) else str(price_el))
            
            listing_url = link_el.get('href', '').strip() if hasattr(link_el, 'get') else ''
            if not listing_url:
                continue
            
            image_url = image_el.get('src', '').strip() if image_el and hasattr(image_el, 'get') else None
            shipping_text = shipping_el.get_text(strip=True) if shipping_el else None
            date_text = date_el.get_text(strip=True) if date_el else None
            
            listing = EbayListing(
                title=title,
                price=price,
                currency=currency,
                listing_url=listing_url,
                image_url=image_url,
                condition_text=None,
                date_text=date_text,
                shipping_text=shipping_text,
                sold=True,
            )
            
            listings.append(listing)
            
            if len(listings) >= max_results:
                break
                
        except Exception as e:
            print(f"DEBUG: Error parsing card: {str(e)}")
            continue
    
    print(f"DEBUG: Successfully parsed {len(listings)} listings")
    return listings