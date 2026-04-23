import hashlib

from fastapi.testclient import TestClient

from app.api import routes
from app.main import app
from app.services import ebay_search


client = TestClient(app)


def test_ebay_account_deletion_challenge_returns_correct_hash(monkeypatch):
    monkeypatch.setenv("EBAY_VERIFICATION_TOKEN", "test_token_abc123")

    challenge_code = "abc123challenge"
    hash_input = challenge_code + "test_token_abc123" + routes.EBAY_DELETION_ENDPOINT
    expected = hashlib.sha256(hash_input.encode()).hexdigest()

    response = client.get(
        "/webhooks/ebay/account-deletion",
        params={"challenge_code": challenge_code},
    )

    assert response.status_code == 200
    assert response.json() == {"challengeResponse": expected}


def test_ebay_account_deletion_challenge_returns_500_when_token_missing(monkeypatch):
    monkeypatch.delenv("EBAY_VERIFICATION_TOKEN", raising=False)

    response = client.get(
        "/webhooks/ebay/account-deletion",
        params={"challenge_code": "somecode"},
    )

    assert response.status_code == 500


def test_ebay_account_deletion_post_returns_200():
    response = client.post("/webhooks/ebay/account-deletion")
    assert response.status_code == 200


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
