"""Secure, provider-backed billing endpoints for ZENTRIX AI.

All payment secrets stay server-side. Entitlements are written only after a
verified Paddle webhook. The module is inert until its environment is configured.
"""
import hashlib
import hmac
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/billing", tags=["billing"])
MAX_WEBHOOK_BYTES = 256_000


def _config():
    return {
        "supabase_url": os.getenv("SUPABASE_URL", "").rstrip("/"),
        "anon": os.getenv("SUPABASE_ANON_KEY", ""),
        "service": os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""),
        "paddle_key": os.getenv("PADDLE_API_KEY", ""),
        "webhook_secret": os.getenv("PADDLE_WEBHOOK_SECRET_KEY", ""),
        "monthly": os.getenv("PADDLE_PRICE_ID_MONTHLY", ""),
        "lifetime": os.getenv("PADDLE_PRICE_ID_LIFETIME", ""),
        "donation": os.getenv("PADDLE_PRICE_ID_DONATION", ""),
        "checkout_url": os.getenv("PADDLE_CHECKOUT_URL", ""),
        "environment": os.getenv("PADDLE_ENVIRONMENT", "sandbox").lower(),
    }


def _billing_ready(cfg):
    return all((cfg["supabase_url"], cfg["service"], cfg["paddle_key"],
                cfg["webhook_secret"], cfg["checkout_url"]))


def _http_json(url, method="GET", headers=None, payload=None, timeout=12):
    data = None if payload is None else json.dumps(payload, separators=(",", ":")).encode()
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read(1_000_001)
            if len(raw) > 1_000_000:
                raise HTTPException(502, "Billing provider returned an oversized response.")
            return json.loads(raw.decode("utf-8")) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read(2048).decode("utf-8", "replace")
        raise HTTPException(502, "Billing service request failed: " + detail[:500])
    except urllib.error.URLError:
        raise HTTPException(503, "Billing service is temporarily unavailable.")
    except (ValueError, UnicodeDecodeError):
        raise HTTPException(502, "Billing service returned an invalid response.")


def _service_headers(cfg, prefer=None):
    headers = {
        "apikey": cfg["service"],
        "Authorization": "Bearer " + cfg["service"],
        "Content-Type": "application/json",
    }
    if prefer:
        headers["Prefer"] = prefer
    return headers


def _supabase_rest(cfg, table, query="", method="GET", payload=None, prefer=None):
    url = cfg["supabase_url"] + "/rest/v1/" + table
    if query:
        url += "?" + query
    return _http_json(url, method, _service_headers(cfg, prefer), payload)


def _authenticated_user(cfg, authorization):
    if not cfg["supabase_url"] or not cfg["anon"]:
        raise HTTPException(503, "Account authentication is not configured.")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Sign in to manage a ZENTRIX plan.")
    token = authorization[7:].strip()
    if not token or len(token) > 5000:
        raise HTTPException(401, "Invalid account session.")
    user = _http_json(
        cfg["supabase_url"] + "/auth/v1/user",
        headers={"apikey": cfg["anon"], "Authorization": "Bearer " + token},
    )
    user_id = user.get("id")
    if not isinstance(user_id, str) or not re.fullmatch(
        r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
        user_id,
    ):
        raise HTTPException(401, "Could not verify your account.")
    return user


class CheckoutRequest(BaseModel):
    plan: str = Field(pattern=r"^(monthly|lifetime|donation)$")


@router.get("/status")
def billing_status(authorization: str | None = Header(default=None)):
    cfg = _config()
    user = _authenticated_user(cfg, authorization)
    if not cfg["service"]:
        return {"configured": False, "plan": "free", "status": "inactive"}
    rows = _supabase_rest(
        cfg, "zentrix_billing",
        "select=plan,status,current_period_end&user_id=eq." + urllib.parse.quote(user["id"], safe=""),
    )
    row = rows[0] if isinstance(rows, list) and rows else None
    if not row:
        return {"configured": _billing_ready(cfg), "plan": "free", "status": "inactive"}
    return {
        "configured": _billing_ready(cfg),
        "plan": row.get("plan", "free"),
        "status": row.get("status", "inactive"),
        "current_period_end": row.get("current_period_end"),
    }


@router.post("/checkout")
def create_checkout(body: CheckoutRequest, authorization: str | None = Header(default=None)):
    cfg = _config()
    user = _authenticated_user(cfg, authorization)
    if not _billing_ready(cfg):
        raise HTTPException(503, "Payments are not enabled yet. The site owner must finish Paddle and Supabase setup.")
    price_id = {"monthly": cfg["monthly"], "lifetime": cfg["lifetime"], "donation": cfg["donation"]}[body.plan]
    if not re.fullmatch(r"pri_[a-z0-9]{26}", price_id):
        raise HTTPException(503, "This checkout option is not configured yet.")
    if not cfg["checkout_url"].startswith("https://"):
        raise HTTPException(503, "The approved secure checkout URL is not configured.")
    base = "https://api.paddle.com" if cfg["environment"] == "live" else "https://sandbox-api.paddle.com"
    result = _http_json(
        base + "/transactions",
        method="POST",
        headers={"Authorization": "Bearer " + cfg["paddle_key"], "Content-Type": "application/json"},
        payload={
            "items": [{"price_id": price_id, "quantity": 1}],
            "custom_data": {"zentrix_user_id": user["id"], "zentrix_plan": body.plan},
            "checkout": {"url": cfg["checkout_url"]},
        },
    )
    checkout_url = (result.get("data") or {}).get("checkout", {}).get("url")
    if not isinstance(checkout_url, str) or not checkout_url.startswith("https://"):
        raise HTTPException(502, "Paddle did not return a secure checkout URL.")
    return {"checkout_url": checkout_url, "transaction_id": (result.get("data") or {}).get("id")}


def _verify_paddle_signature(raw_body, signature_header, secret):
    if not signature_header or not secret:
        return False
    fields = {}
    for part in signature_header.split(";"):
        if "=" in part:
            key, value = part.split("=", 1)
            fields.setdefault(key.strip(), []).append(value.strip())
    timestamps = fields.get("ts", [])
    signatures = fields.get("h1", [])
    if not timestamps or not signatures or not timestamps[0].isdigit():
        return False
    timestamp = int(timestamps[0])
    if abs(time.time() - timestamp) > 300:
        return False
    signed = str(timestamp).encode() + b":" + raw_body
    expected = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    return any(hmac.compare_digest(expected, candidate) for candidate in signatures)


def _write_entitlement(cfg, user_id, plan, status, subscription_id=None,
                      customer_id=None, current_period_end=None):
    payload = {
        "user_id": user_id,
        "plan": plan,
        "status": status,
        "paddle_subscription_id": subscription_id,
        "paddle_customer_id": customer_id,
        "current_period_end": current_period_end,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _supabase_rest(cfg, "zentrix_billing", "on_conflict=user_id", "POST",
                   payload, "resolution=merge-duplicates,return=minimal")


@router.post("/webhook")
async def paddle_webhook(request: Request, paddle_signature: str | None = Header(default=None, alias="Paddle-Signature")):
    cfg = _config()
    if not cfg["webhook_secret"] or not cfg["service"] or not cfg["supabase_url"]:
        raise HTTPException(503, "Billing webhook is not configured.")
    raw = await request.body()
    if len(raw) > MAX_WEBHOOK_BYTES:
        raise HTTPException(413, "Webhook payload is too large.")
    if not _verify_paddle_signature(raw, paddle_signature, cfg["webhook_secret"]):
        raise HTTPException(401, "Invalid or expired Paddle signature.")
    try:
        event = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        raise HTTPException(400, "Invalid webhook JSON.")
    event_id = event.get("event_id")
    event_type = event.get("event_type")
    data = event.get("data") or {}
    if not isinstance(event_id, str) or not isinstance(event_type, str) or not isinstance(data, dict):
        raise HTTPException(400, "Malformed Paddle event.")
    # Idempotency: ignore event IDs already recorded after a successful update.
    prior = _supabase_rest(cfg, "zentrix_billing_events",
                           "select=event_id&event_id=eq." + urllib.parse.quote(event_id, safe=""))
    if isinstance(prior, list) and prior:
        return {"received": True, "duplicate": True}

    custom = data.get("custom_data") or {}
    user_id = custom.get("zentrix_user_id")
    plan = custom.get("zentrix_plan")
    if not isinstance(user_id, str) or not re.fullmatch(
        r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", user_id
    ):
        # Events unrelated to a ZENTRIX checkout are acknowledged but never grant access.
        _supabase_rest(cfg, "zentrix_billing_events", "", "POST",
                       {"event_id": event_id, "event_type": event_type},
                       "resolution=ignore-duplicates,return=minimal")
        return {"received": True, "ignored": True}

    subscription_id = data.get("id") if event_type.startswith("subscription.") else data.get("subscription_id")
    customer_id = data.get("customer_id")
    period = data.get("current_billing_period") or {}
    period_end = period.get("ends_at") if isinstance(period, dict) else None

    if event_type in {"subscription.created", "subscription.updated", "subscription.canceled", "subscription.paused", "subscription.resumed"}:
        if plan != "monthly":
            # For older Paddle records, infer monthly only from the configured price ID.
            item_ids = []
            for item in data.get("items", []):
                price = item.get("price") or {}
                item_ids.append(price.get("id") or item.get("price_id"))
            if cfg["monthly"] not in item_ids:
                return {"received": True, "ignored": True}
            plan = "monthly"
        status = data.get("status", "inactive")
        if event_type == "subscription.canceled":
            status = "canceled"
        _write_entitlement(cfg, user_id, "monthly", status, subscription_id, customer_id, period_end)

    elif event_type == "transaction.completed":
        items = data.get("items") or []
        item_ids = []
        for item in items:
            price = item.get("price") or {}
            item_ids.append(price.get("id") or item.get("price_id"))
        if plan == "lifetime" and cfg["lifetime"] in item_ids:
            _write_entitlement(cfg, user_id, "lifetime", "active", None, customer_id, None)
        # Donation transactions intentionally never change plan access.

    _supabase_rest(cfg, "zentrix_billing_events", "", "POST",
                   {"event_id": event_id, "event_type": event_type},
                   "resolution=ignore-duplicates,return=minimal")
    return {"received": True}
