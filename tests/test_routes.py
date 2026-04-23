from fastapi.testclient import TestClient

from app.api import routes
from app.main import app
from app.services import ebay_search


client = TestClient(app)


def test_status_endpoint_reports_config(monkeypatch):
    monkeypatch.setattr(routes, "has_ebay_api_credentials", lambda: True)
    monkeypatch.setattr(routes, "get_marketplace_id", lambda: "EBAY_US")

    response = client.get("/status")

    assert response.status_code == 200
    assert response.json() == {
        "ebay_api_credentials_configured": True,
        "ebay_marketplace": "EBAY_US",
    }


def test_search_endpoint_maps_ebay_api_errors_to_502(monkeypatch):
    async def fake_search_ebay_listings(_payload):
        raise ebay_search.EbayApiError("eBay Browse API search failed")

    monkeypatch.setattr(routes, "search_ebay_listings", fake_search_ebay_listings)

    response = client.post(
        "/search",
        json={
            "card_name": "Pikachu",
            "condition_type": "raw",
            "include_unsold": False,
            "max_results": 5,
        },
    )

    assert response.status_code == 502
    assert "eBay Browse API search failed" in response.json()["detail"]
