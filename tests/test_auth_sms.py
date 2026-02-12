"""Unit tests for Twilio SMS OTP delivery behavior."""

import pytest
from fastapi import HTTPException

from plugin_boutique_price_checker.web import auth


class DummyResponse:
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code


def test_send_sms_otp_requires_twilio_credentials(monkeypatch) -> None:
    monkeypatch.delenv("TWILIO_ACCOUNT_SID", raising=False)
    monkeypatch.delenv("TWILIO_AUTH_TOKEN", raising=False)
    monkeypatch.setenv("TWILIO_FROM_NUMBER", "+15551112222")
    monkeypatch.delenv("TWILIO_MESSAGING_SERVICE_SID", raising=False)

    with pytest.raises(HTTPException, match="Twilio credentials are missing"):
        auth.send_sms_otp("+15551234567", "123456")


def test_send_sms_otp_requires_sender_or_messaging_service(monkeypatch) -> None:
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "AC_test")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.delenv("TWILIO_FROM_NUMBER", raising=False)
    monkeypatch.delenv("TWILIO_MESSAGING_SERVICE_SID", raising=False)

    with pytest.raises(HTTPException, match="TWILIO_FROM_NUMBER or TWILIO_MESSAGING_SERVICE_SID"):
        auth.send_sms_otp("+15551234567", "123456")


def test_send_sms_otp_posts_to_twilio_with_from_number(monkeypatch) -> None:
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "AC_test")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv("TWILIO_FROM_NUMBER", "+15551112222")
    monkeypatch.delenv("TWILIO_MESSAGING_SERVICE_SID", raising=False)

    captured = {}

    def fake_post(url, data, auth, timeout):
        captured["url"] = url
        captured["data"] = data
        captured["auth"] = auth
        captured["timeout"] = timeout
        return DummyResponse(status_code=201)

    monkeypatch.setattr(auth.httpx, "post", fake_post)

    auth.send_sms_otp("+15551234567", "123456")

    assert "/Accounts/AC_test/Messages.json" in captured["url"]
    assert captured["data"]["To"] == "+15551234567"
    assert captured["data"]["From"] == "+15551112222"
    assert "MessagingServiceSid" not in captured["data"]
    assert captured["auth"] == ("AC_test", "token")
    assert captured["timeout"] == 10.0


def test_send_sms_otp_posts_to_twilio_with_messaging_service(monkeypatch) -> None:
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "AC_test")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.delenv("TWILIO_FROM_NUMBER", raising=False)
    monkeypatch.setenv("TWILIO_MESSAGING_SERVICE_SID", "MG_test")

    captured = {}

    def fake_post(url, data, auth, timeout):
        captured["url"] = url
        captured["data"] = data
        captured["auth"] = auth
        captured["timeout"] = timeout
        return DummyResponse(status_code=201)

    monkeypatch.setattr(auth.httpx, "post", fake_post)

    auth.send_sms_otp("+15551234567", "123456")

    assert captured["data"]["To"] == "+15551234567"
    assert captured["data"]["MessagingServiceSid"] == "MG_test"
    assert "From" not in captured["data"]


def test_send_sms_otp_raises_on_twilio_error_response(monkeypatch) -> None:
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "AC_test")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv("TWILIO_FROM_NUMBER", "+15551112222")
    monkeypatch.delenv("TWILIO_MESSAGING_SERVICE_SID", raising=False)

    monkeypatch.setattr(auth.httpx, "post", lambda *args, **kwargs: DummyResponse(status_code=401))

    with pytest.raises(HTTPException, match="Twilio SMS send failed"):
        auth.send_sms_otp("+15551234567", "123456")
