import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from core.database import get_db
from dependencies.rbac import require_client
from main import app
from models.payment import Card, CardType
from models.user import User, Client

# Standard test card numbers (Luhn-valid)
VISA_CARD = "4111111111111111"
MASTERCARD_CARD = "5500005555555559"


@pytest.fixture
def payment_setup(db):
    visa_type = CardType(card_type_name="Visa")
    mc_type = CardType(card_type_name="Mastercard")
    db.add_all([visa_type, mc_type])
    db.flush()

    user = User(auth0_sub="auth0|payer", email="payer@test.com",
                first_name="Pay", last_name="Er", role="client")
    db.add(user)
    db.flush()
    client = Client(user_id=user.user_id, weekly_streak=0)
    db.add(client)
    db.flush()
    return {"user": user, "client": client, "visa_type": visa_type}


@pytest.fixture
def payment_client(db, payment_setup):
    mock_user = MagicMock()
    mock_user.user_id = payment_setup["user"].user_id
    mock_user.role = "client"
    mock_user.client = payment_setup["client"]

    def _override_get_db():
        yield db
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[require_client] = lambda: mock_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# GET /payments/cards: no cards on file returns an empty list.
def test_list_cards_empty(payment_client):
    resp = payment_client.get("/payments/cards")
    assert resp.status_code == 200
    assert resp.json() == []


# POST /payments/cards: valid Visa card is saved and returned with masked number.
def test_add_valid_visa(payment_client):
    resp = payment_client.post("/payments/cards", json={
        "card_number": VISA_CARD,
        "expiry_month": 12,
        "expiry_year": 2030,
        "is_default": True,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["card_type_name"] == "Visa"
    assert data["last_four"] == "1111"


# POST /payments/cards: valid Mastercard is saved.
def test_add_valid_mastercard(payment_client):
    resp = payment_client.post("/payments/cards", json={
        "card_number": MASTERCARD_CARD,
        "expiry_month": 6,
        "expiry_year": 2028,
        "is_default": False,
    })
    assert resp.status_code == 200
    assert resp.json()["card_type_name"] == "Mastercard"


# POST /payments/cards: non-16-digit number is rejected with 400.
def test_add_card_wrong_length(payment_client):
    resp = payment_client.post("/payments/cards", json={
        "card_number": "411111111111",
        "expiry_month": 12,
        "expiry_year": 2030,
        "is_default": False,
    })
    assert resp.status_code == 400


# POST /payments/cards: expired card is rejected with 400.
def test_add_card_expired(payment_client):
    resp = payment_client.post("/payments/cards", json={
        "card_number": VISA_CARD,
        "expiry_month": 1,
        "expiry_year": 2020,
        "is_default": False,
    })
    assert resp.status_code == 400


# POST /payments/cards: saving the same card twice returns 409.
def test_add_card_duplicate(payment_client):
    payload = {"card_number": VISA_CARD, "expiry_month": 12, "expiry_year": 2030, "is_default": False}
    payment_client.post("/payments/cards", json=payload)
    resp = payment_client.post("/payments/cards", json=payload)
    assert resp.status_code == 409


# GET /payments/cards: after adding a card, it appears in the list.
def test_list_cards_after_add(payment_client):
    payment_client.post("/payments/cards", json={
        "card_number": VISA_CARD, "expiry_month": 12, "expiry_year": 2030, "is_default": True,
    })
    resp = payment_client.get("/payments/cards")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


# DELETE /payments/cards/{id}: deleting a non-existent card returns 404.
def test_delete_card_not_found(payment_client):
    resp = payment_client.delete("/payments/cards/9999")
    assert resp.status_code == 404


# DELETE /payments/cards/{id}: saved card is deleted and no longer appears in the list.
def test_delete_card_success(payment_client):
    add_resp = payment_client.post("/payments/cards", json={
        "card_number": VISA_CARD, "expiry_month": 12, "expiry_year": 2030, "is_default": True,
    })
    card_id = add_resp.json()["card_id"]
    assert payment_client.delete(f"/payments/cards/{card_id}").status_code == 204
    assert payment_client.get("/payments/cards").json() == []
