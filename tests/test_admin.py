from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from core.database import get_db
from dependencies.rbac import require_admin
from main import app
from models.payment import CoachPaymentHistory
from models.user import Client, Coach, CoachStatus, User
from unittest.mock import MagicMock


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def admin_client(db):
    """TestClient with get_db and require_admin overridden — no real DB or Auth0."""
    mock_admin = MagicMock()
    mock_admin.role = "admin"

    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[require_admin] = lambda: mock_admin

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def payment_actors(db):
    """One client user, one coach user, their profiles, and an Active CoachStatus."""
    status = CoachStatus(status_name="Active")
    db.add(status)
    db.flush()

    client_user = User(auth0_sub="user|client1", email="client@fin.test",
                       first_name="Carol", last_name="Client", role="client")
    coach_user = User(auth0_sub="user|coach1", email="coach@fin.test",
                      first_name="Dave", last_name="Coach", role="coach")
    db.add_all([client_user, coach_user])
    db.flush()

    client = Client(user_id=client_user.user_id)
    coach = Coach(user_id=coach_user.user_id, status_id=status.status_id)
    db.add_all([client, coach])
    db.flush()

    return {"client": client, "coach": coach,
            "client_user": client_user, "coach_user": coach_user}


# ── GET /admin/financial-summary ──────────────────────────────────────────────

# No payments in DB → all aggregates are zero and has_transactions is False.
def test_financial_summary_empty(admin_client):
    resp = admin_client.get("/admin/financial-summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_revenue"] == 0.0
    assert body["platform_revenue"] == 0.0
    assert body["coach_payout_total"] == 0.0
    assert body["refunded_amount"] == 0.0
    assert body["transaction_count"] == 0
    assert body["average_transaction"] == 0.0
    assert body["has_transactions"] is False
    assert body["chart"] == []
    assert body["recent_transactions"] == []


# One completed payment with explicit fee fields → totals match those fields.
def test_financial_summary_single_completed_explicit_fees(admin_client, db, payment_actors):
    client = payment_actors["client"]
    coach = payment_actors["coach"]
    db.add(CoachPaymentHistory(
        client_id=client.client_id,
        coach_id=coach.coach_id,
        amount=100.00,
        platform_fee=10.00,
        coach_payout_amount=90.00,
        status="Completed",
        payment_date=datetime(2025, 6, 15, tzinfo=timezone.utc),
    ))
    db.flush()

    resp = admin_client.get("/admin/financial-summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_revenue"] == 100.0
    assert body["platform_revenue"] == 10.0
    assert body["coach_payout_total"] == 90.0
    assert body["transaction_count"] == 1
    assert body["average_transaction"] == 100.0
    assert body["has_transactions"] is True


# When platform_fee is 0, the endpoint falls back to 10% of amount.
def test_financial_summary_default_fee_fallback(admin_client, db, payment_actors):
    client = payment_actors["client"]
    coach = payment_actors["coach"]
    db.add(CoachPaymentHistory(
        client_id=client.client_id,
        coach_id=coach.coach_id,
        amount=200.00,
        platform_fee=0.00,
        coach_payout_amount=0.00,
        status="Completed",
        payment_date=datetime(2025, 6, 15, tzinfo=timezone.utc),
    ))
    db.flush()

    resp = admin_client.get("/admin/financial-summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["platform_revenue"] == 20.0   # 10% of 200
    assert body["coach_payout_total"] == 180.0  # 200 - 20


# Refunded payment appears in refunded_amount but not in total_revenue or chart.
def test_financial_summary_refunded_payment(admin_client, db, payment_actors):
    client = payment_actors["client"]
    coach = payment_actors["coach"]
    db.add(CoachPaymentHistory(
        client_id=client.client_id,
        coach_id=coach.coach_id,
        amount=50.00,
        platform_fee=5.00,
        coach_payout_amount=45.00,
        status="Refunded",
        payment_date=datetime(2025, 6, 15, tzinfo=timezone.utc),
    ))
    db.flush()

    resp = admin_client.get("/admin/financial-summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["refunded_amount"] == 50.0
    assert body["total_revenue"] == 0.0
    assert body["transaction_count"] == 1
    assert body["chart"] == []


# Mix of completed and refunded: only completed count toward revenue.
def test_financial_summary_mixed_payments(admin_client, db, payment_actors):
    client = payment_actors["client"]
    coach = payment_actors["coach"]
    db.add_all([
        CoachPaymentHistory(
            client_id=client.client_id, coach_id=coach.coach_id,
            amount=100.00, platform_fee=10.00, coach_payout_amount=90.00,
            status="Completed", payment_date=datetime(2025, 6, 1, tzinfo=timezone.utc),
        ),
        CoachPaymentHistory(
            client_id=client.client_id, coach_id=coach.coach_id,
            amount=40.00, platform_fee=4.00, coach_payout_amount=36.00,
            status="Refunded", payment_date=datetime(2025, 6, 2, tzinfo=timezone.utc),
        ),
    ])
    db.flush()

    resp = admin_client.get("/admin/financial-summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_revenue"] == 100.0
    assert body["refunded_amount"] == 40.0
    assert body["transaction_count"] == 2


# An unrecognized period value returns 400.
def test_financial_summary_invalid_period(admin_client):
    resp = admin_client.get("/admin/financial-summary?period=last_week")
    assert resp.status_code == 400


# year filter: only payments from the given year are included.
def test_financial_summary_year_filter(admin_client, db, payment_actors):
    client = payment_actors["client"]
    coach = payment_actors["coach"]
    db.add_all([
        CoachPaymentHistory(
            client_id=client.client_id, coach_id=coach.coach_id,
            amount=100.00, platform_fee=10.00, coach_payout_amount=90.00,
            status="Completed", payment_date=datetime(2024, 3, 1, tzinfo=timezone.utc),
        ),
        CoachPaymentHistory(
            client_id=client.client_id, coach_id=coach.coach_id,
            amount=200.00, platform_fee=20.00, coach_payout_amount=180.00,
            status="Completed", payment_date=datetime(2025, 6, 1, tzinfo=timezone.utc),
        ),
    ])
    db.flush()

    resp = admin_client.get("/admin/financial-summary?year=2025")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_revenue"] == 200.0
    assert body["transaction_count"] == 1


# q filter: searching by coach name returns only matching payments.
def test_financial_summary_q_filter_by_name(admin_client, db, payment_actors):
    client = payment_actors["client"]
    coach = payment_actors["coach"]
    db.add(CoachPaymentHistory(
        client_id=client.client_id, coach_id=coach.coach_id,
        amount=75.00, platform_fee=7.50, coach_payout_amount=67.50,
        status="Completed", payment_date=datetime(2025, 6, 1, tzinfo=timezone.utc),
    ))
    db.flush()

    resp = admin_client.get("/admin/financial-summary?q=Dave")
    assert resp.status_code == 200
    body = resp.json()
    assert body["transaction_count"] == 1

    resp_no_match = admin_client.get("/admin/financial-summary?q=NoSuchPerson")
    assert resp_no_match.status_code == 200
    assert resp_no_match.json()["transaction_count"] == 0


# Chart groups completed payments by month label.
def test_financial_summary_chart_grouping(admin_client, db, payment_actors):
    client = payment_actors["client"]
    coach = payment_actors["coach"]
    db.add_all([
        CoachPaymentHistory(
            client_id=client.client_id, coach_id=coach.coach_id,
            amount=50.00, platform_fee=5.00, coach_payout_amount=45.00,
            status="Completed", payment_date=datetime(2025, 6, 1, tzinfo=timezone.utc),
        ),
        CoachPaymentHistory(
            client_id=client.client_id, coach_id=coach.coach_id,
            amount=50.00, platform_fee=5.00, coach_payout_amount=45.00,
            status="Completed", payment_date=datetime(2025, 6, 15, tzinfo=timezone.utc),
        ),
        CoachPaymentHistory(
            client_id=client.client_id, coach_id=coach.coach_id,
            amount=80.00, platform_fee=8.00, coach_payout_amount=72.00,
            status="Completed", payment_date=datetime(2025, 7, 1, tzinfo=timezone.utc),
        ),
    ])
    db.flush()

    resp = admin_client.get("/admin/financial-summary")
    assert resp.status_code == 200
    chart = resp.json()["chart"]
    assert len(chart) == 2
    labels = {pt["label"] for pt in chart}
    assert "Jun 2025" in labels
    assert "Jul 2025" in labels
    jun = next(pt for pt in chart if pt["label"] == "Jun 2025")
    assert jun["revenue"] == 100.0
    assert jun["transaction_count"] == 2


# recent_transactions includes client and coach names resolved from the DB.
def test_financial_summary_recent_transactions_names(admin_client, db, payment_actors):
    client = payment_actors["client"]
    coach = payment_actors["coach"]
    db.add(CoachPaymentHistory(
        client_id=client.client_id, coach_id=coach.coach_id,
        amount=120.00, platform_fee=12.00, coach_payout_amount=108.00,
        status="Completed", payment_date=datetime(2025, 6, 1, tzinfo=timezone.utc),
    ))
    db.flush()

    resp = admin_client.get("/admin/financial-summary")
    assert resp.status_code == 200
    txns = resp.json()["recent_transactions"]
    assert len(txns) == 1
    assert txns[0]["client_name"] == "Carol Client"
    assert txns[0]["coach_name"] == "Dave Coach"
    assert txns[0]["amount"] == 120.0
