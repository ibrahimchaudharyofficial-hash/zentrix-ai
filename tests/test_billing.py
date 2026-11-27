import hashlib
import hmac
import os
import sys
import time
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
import billing


def _signed_header(raw, timestamp, secret="test-secret"):
    digest = hmac.new(
        secret.encode(), str(timestamp).encode() + b":" + raw, hashlib.sha256
    ).hexdigest()
    return f"ts={timestamp};h1={digest}"


def test_paddle_signature_accepts_fresh_valid_signature():
    raw = b'{"event_id":"evt_test"}'
    with patch.object(billing.time, "time", return_value=1_700_000_000):
        header = _signed_header(raw, 1_700_000_000)
        assert billing._verify_paddle_signature(raw, header, "test-secret")


def test_paddle_signature_rejects_old_signature():
    raw = b'{"event_id":"evt_test"}'
    with patch.object(billing.time, "time", return_value=1_700_000_000):
        header = _signed_header(raw, 1_699_999_994)
        assert not billing._verify_paddle_signature(raw, header, "test-secret")


def test_paddle_signature_rejects_tampered_body():
    raw = b'{"event_id":"evt_test"}'
    with patch.object(billing.time, "time", return_value=1_700_000_000):
        header = _signed_header(raw, 1_700_000_000)
        assert not billing._verify_paddle_signature(raw + b" ", header, "test-secret")


def test_paddle_signature_supports_multiple_h1_values():
    raw = b'{"event_id":"evt_test"}'
    with patch.object(billing.time, "time", return_value=1_700_000_000):
        header = _signed_header(raw, 1_700_000_000)
        assert billing._verify_paddle_signature(raw, header + ";h1=rotated-invalid", "test-secret")


def test_price_ids_are_extracted_from_paddle_items():
    data = {"items": [
        {"price": {"id": "pri_monthly"}, "quantity": 1},
        {"price_id": "pri_lifetime", "quantity": 1},
    ]}
    assert billing._price_ids(data) == ["pri_monthly", "pri_lifetime"]


def test_paddle_event_timestamp_requires_timezone():
    assert billing._parse_occurred_at("2026-11-27T12:00:00Z").endswith("+00:00")
    try:
        billing._parse_occurred_at("2026-11-27T12:00:00")
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 400
    else:
        raise AssertionError("Timezone-naive event timestamp must be rejected")

def test_billing_ready_requires_monthly_and_lifetime_prices():
    cfg = {
        "supabase_url": "https://example.supabase.co",
        "anon": "anon",
        "service": "service",
        "paddle_key": "paddle",
        "client_token": "test_" + "a" * 27,
        "webhook_secret": "secret",
        "monthly": "",
        "lifetime": "pri_12345678901234567890123456",
        "donation": "",
        "checkout_url": "https://checkout.example.com",
        "environment": "sandbox",
    }
    assert not billing._billing_ready(cfg)
    cfg["monthly"] = "pri_12345678901234567890123456"
    assert billing._billing_ready(cfg)


def test_billing_ready_rejects_unknown_environment():
    cfg = {
        "supabase_url": "https://example.supabase.co",
        "anon": "anon",
        "service": "service",
        "paddle_key": "paddle",
        "webhook_secret": "secret",
        "monthly": "pri_12345678901234567890123456",
        "lifetime": "pri_12345678901234567890123456",
        "donation": "",
        "checkout_url": "https://checkout.example.com",
        "environment": "production",
    }
    assert not billing._billing_ready(cfg)
