"""Secure, provider-backed billing endpoints for ZENTRIX AI.

Payment secrets stay server-side. Entitlements are written only after a
verified Paddle webhook and an atomic, idempotent database operation.
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
from datetime import datetime

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/billing", tags=["billing"])
MAX_WEBHOOK_BYTES = 256_000
USER_ID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
PRICE_ID_RE = re.compile(r"^pri_[a-z0-9]{26}$")
ALLOWED_SUBSCRIPTION_STATUSES = {
    "active", "trialing", "past_due", "paused", "canceled", "inactive"
}


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
        "environment": os.getenv("PADDLE_ENVIRONMENT", "sandbox").strip().lower(),
    }


def _billing_ready(cfg):
    return all((
        cfg["supabase_url"], cfg["anon"], cfg["service"], cfg["paddle_key"],
        cfg["webhook_secret"], cfg["checkout_url"]
    )) and cfg["environment"] in {"sandbox", "live"}


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
        # Provider error bodies may contain customer/provider details; do not echo them.
        raise HTTPException(502, "Billing service rejected the request (HTTP %s)." % exc.code)
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


def _apply_billing_event(cfg, event_id, event_type, occurred_at, user_id=None,
                         plan=None, status=None, subscription_id=None,
                         customer_id=None, current_period_end=None):
    """Record the event and, if applicable, update entitlement in one DB transaction."""
    return _http_json(
        cfg["supabase_url"] + "/rest/v1/rpc/zentrix_apply_billing_event",
        method="POST",
        headers=_service_headers(cfg),
        payload={
            "p_event_id": event_id,
            "p_event_type": event_type,
            "p_occurred_at": occurred_at,
            "p_user_id": user_id,
            "p_plan": plan,
            "p_status": status,
            "p_subscription_id": subscription_id,
            "p_customer_id": customer_id,
            "p_current_period_end": current_period_end,
        },
    )


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
    if not isinstance(user_id, str) or not USER_ID_RE.fullmatch(user_id):
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

    price_id = {
        "monthly": cfg["monthly"],
        "lifetime": cfg["lifetime"],
        "donation": cfg["donation"],
    }[body.plan]
    if not PRICE_ID_RE.fullmatch(price_id):
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
    # Paddle's SDK default replay-protection tolerance is five seconds.
    if abs(time.time() - timestamp) > 5:
        return False
    signed = str(timestamp).encode() + b":" + raw_body
    expected = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    return any(hmac.compare_digest(expected, candidate) for candidate in signatures)


def _price_ids(data):
    found = []
    for item in data.get("items") or []:
        if not isinstance(item, dict):
            continue
        price = item.get("price") or {}
        if isinstance(price, dict):
            price_id = price.get("id")
        else:
            price_id = None
        price_id = price_id or item.get("price_id")
        if isinstance(price_id, str):
            found.append(price_id)
    return found


def _parse_occurred_at(value):
    if not isinstance(value, str) or not value:
        raise HTTPException(400, "Paddle event is missing its occurrence timestamp.")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("timezone required")
        return parsed.isoformat()
    except ValueError:
        raise HTTPException(400, "Paddle event has an invalid occurrence timestamp.")


@router.post("/webhook")
async def paddle_webhook(
    request: Request,
    paddle_signature: str | None = Header(default=None, alias="Paddle-Signature"),
):
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
    if not isinstance(event, dict):
        raise HTTPException(400, "Malformed Paddle event.")

    event_id = event.get("event_id")
    event_type = event.get("event_type")
    data = event.get("data") or {}
    if (not isinstance(event_id, str) or not event_id.startswith("evt_")
            or len(event_id) > 255 or not isinstance(event_type, str)
            or len(event_type) > 120 or not isinstance(data, dict)):
        raise HTTPException(400, "Malformed Paddle event.")
    occurred_at = _parse_occurred_at(event.get("occurred_at"))

    custom = data.get("custom_data") or {}
    if not isinstance(custom, dict):
        custom = {}
    user_id = custom.get("zentrix_user_id")
    if not isinstance(user_id, str) or not USER_ID_RE.fullmatch(user_id):
        user_id = None
    plan = custom.get("zentrix_plan")

    entitlement = {
        "user_id": None,
        "plan": None,
        "status": None,
        "subscription_id": None,
        "customer_id": data.get("customer_id") if isinstance(data.get("customer_id"), str) else None,
        "period_end": None,
    }

    if event_type in {
        "subscription.created", "subscription.updated", "subscription.canceled",
        "subscription.paused", "subscription.resumed", "subscription.activated",
        "subscription.trialing", "subscription.past_due"
    }:
        # A subscription is eligible only when its actual item matches our
        # configured monthly price. Never trust custom_data alone for access.
        if user_id and cfg["monthly"] and cfg["monthly"] in _price_ids(data):
            raw_status = data.get("status")
            status = raw_status if raw_status in ALLOWED_SUBSCRIPTION_STATUSES else "inactive"
            if event_type == "subscription.canceled":
                status = "canceled"
            elif event_type == "subscription.paused":
                status = "paused"
            elif event_type == "subscription.activated":
                status = "active"
            elif event_type == "subscription.trialing":
                status = "trialing"
            elif event_type == "subscription.past_due":
                status = "past_due"
            period = data.get("current_billing_period") or {}
            period_end = period.get("ends_at") if isinstance(period, dict) else None
            entitlement.update({
                "user_id": user_id,
                "plan": "monthly",
                "status": status,
                "subscription_id": data.get("id") if isinstance(data.get("id"), str) else None,
                "period_end": period_end,
            })

    elif event_type == "transaction.completed":
        # Only a completed transaction containing our configured lifetime
        # price grants lifetime. Donation transactions never grant Premium.
        if user_id and plan == "lifetime" and cfg["lifetime"] and cfg["lifetime"] in _price_ids(data):
            entitlement.update({
                "user_id": user_id,
                "plan": "lifetime",
                "status": "active",
                "subscription_id": None,
            })

    applied = _apply_billing_event(
        cfg, event_id, event_type, occurred_at,
        entitlement["user_id"], entitlement["plan"], entitlement["status"],
        entitlement["subscription_id"], entitlement["customer_id"], entitlement["period_end"],
    )
    return {"received": True, "processed": bool(applied), "duplicate": not bool(applied)}
