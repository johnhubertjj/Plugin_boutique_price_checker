"""Integration tests for auth and protected API endpoints."""

from __future__ import annotations

import importlib

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch, tmp_path):
    """Create an isolated API client with temp SQLite DB and dev auth mode."""
    db_path = tmp_path / "api_auth_test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("AUTH_DEV_MODE", "true")
    monkeypatch.setenv("AUTH_OTP_MAX_ATTEMPTS", "3")
    monkeypatch.setenv("AUTH_OTP_WINDOW_MINUTES", "15")
    monkeypatch.setenv("AUTH_OTP_BLOCK_MINUTES", "15")

    import plugin_boutique_price_checker.web.api as api_module
    import plugin_boutique_price_checker.web.auth as auth_module
    import plugin_boutique_price_checker.web.database as database_module
    import plugin_boutique_price_checker.web.deps as deps_module
    import plugin_boutique_price_checker.web.orm_models as orm_models_module
    import plugin_boutique_price_checker.web.schemas as schemas_module
    import plugin_boutique_price_checker.web.settings as settings_module

    importlib.reload(settings_module)
    importlib.reload(database_module)
    importlib.reload(orm_models_module)
    importlib.reload(deps_module)
    importlib.reload(auth_module)
    importlib.reload(schemas_module)
    importlib.reload(api_module)

    with TestClient(api_module.app) as test_client:
        yield test_client


def _register_and_get_token(client: TestClient, email: str, phone_number: str) -> str:
    start_response = client.post(
        "/auth/register/start",
        json={"email": email, "phone_number": phone_number},
    )
    assert start_response.status_code == 200
    email_code = start_response.json()["dev_code"]

    verify_email_response = client.post(
        "/auth/register/verify-email",
        json={"email": email, "code": email_code},
    )
    assert verify_email_response.status_code == 200
    phone_code = verify_email_response.json()["dev_code"]

    verify_phone_response = client.post(
        "/auth/register/verify-phone",
        json={"email": email, "code": phone_code},
    )
    assert verify_phone_response.status_code == 200
    return verify_phone_response.json()["access_token"]


def test_registration_login_and_me_watchlist_flow(client: TestClient) -> None:
    token = _register_and_get_token(client, "alice@example.com", "+15551234567")
    auth_headers = {"Authorization": f"Bearer {token}"}

    me_response = client.get("/me", headers=auth_headers)
    assert me_response.status_code == 200
    me_body = me_response.json()
    assert me_body["email"] == "alice@example.com"
    assert me_body["two_factor_enabled"] is True

    create_item_response = client.post(
        "/me/watchlist-items",
        headers=auth_headers,
        json={
            "product_url": "https://www.pluginboutique.com/product/example",
            "threshold": 99.99,
            "is_active": True,
        },
    )
    assert create_item_response.status_code == 201
    item_id = create_item_response.json()["id"]

    list_items_response = client.get("/me/watchlist-items", headers=auth_headers)
    assert list_items_response.status_code == 200
    assert len(list_items_response.json()) == 1

    update_item_response = client.patch(
        f"/me/watchlist-items/{item_id}",
        headers=auth_headers,
        json={"threshold": 49.99, "is_active": False},
    )
    assert update_item_response.status_code == 200
    assert float(update_item_response.json()["threshold"]) == 49.99
    assert update_item_response.json()["is_active"] is False

    delete_item_response = client.delete(f"/me/watchlist-items/{item_id}", headers=auth_headers)
    assert delete_item_response.status_code == 204

    list_after_delete = client.get("/me/watchlist-items", headers=auth_headers)
    assert list_after_delete.status_code == 200
    assert list_after_delete.json() == []


def test_login_flow_after_registration(client: TestClient) -> None:
    _register_and_get_token(client, "bob@example.com", "+15557654321")

    login_start_response = client.post("/auth/login/start", json={"email": "bob@example.com"})
    assert login_start_response.status_code == 200
    login_code = login_start_response.json()["dev_code"]

    login_verify_response = client.post(
        "/auth/login/verify",
        json={"email": "bob@example.com", "code": login_code},
    )
    assert login_verify_response.status_code == 200
    assert login_verify_response.json()["token_type"] == "bearer"
    token = login_verify_response.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    logout_response = client.post("/auth/logout", headers=auth_headers)
    assert logout_response.status_code == 204

    me_after_logout = client.get("/me", headers=auth_headers)
    assert me_after_logout.status_code == 401


def test_otp_bruteforce_protection_blocks_after_threshold(client: TestClient) -> None:
    start_response = client.post(
        "/auth/register/start",
        json={"email": "charlie@example.com", "phone_number": "+15550000000"},
    )
    assert start_response.status_code == 200
    real_code = start_response.json()["dev_code"]
    assert real_code

    for attempt in range(2):
        invalid_response = client.post(
            "/auth/register/verify-email",
            json={"email": "charlie@example.com", "code": "000000"},
        )
        assert invalid_response.status_code == 400, f"attempt {attempt + 1} should be invalid"

    blocked_response = client.post(
        "/auth/register/verify-email",
        json={"email": "charlie@example.com", "code": "000000"},
    )
    assert blocked_response.status_code == 429

    still_blocked_with_valid_code = client.post(
        "/auth/register/verify-email",
        json={"email": "charlie@example.com", "code": real_code},
    )
    assert still_blocked_with_valid_code.status_code == 429
