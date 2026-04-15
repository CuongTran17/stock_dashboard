"""
Payment API Router – Sepay Webhook Integration
Receives IPN (Instant Payment Notification) from Sepay when a bank transfer
is completed, then upgrades the user to 'premium' role.

Based on the Sepay webhook pattern from ptit-learning-mobile project,
adapted for FastAPI + SQLAlchemy.
"""
import hashlib
import hmac
import logging
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.api.auth import require_auth
from src.database.db import get_db
from src.database.models import User, UserSubscription

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/payment", tags=["Payment"])

# ── Sepay Config ────────────────────────────────────────────────────
SEPAY_SECRET_KEY = os.getenv("SEPAY_SECRET_KEY", "")
SEPAY_BANK_ACCOUNT = os.getenv("SEPAY_BANK_ACCOUNT", "")
SEPAY_BANK_NAME = os.getenv("SEPAY_BANK_NAME", "MB")
SEPAY_ACCOUNT_NAME = os.getenv("SEPAY_ACCOUNT_NAME", "")

# Premium subscription price (VND)
PREMIUM_PRICE = int(os.getenv("PREMIUM_PRICE", "99000"))
PREMIUM_DURATION_DAYS = int(os.getenv("PREMIUM_DURATION_DAYS", "30"))


# ── Schemas ──────────────────────────────────────────────────────────
class PaymentInfoResponse(BaseModel):
    bank_name: str
    account_number: str
    account_name: str
    amount: int
    transfer_content: str
    qr_url: str


class SepayWebhookPayload(BaseModel):
    """Payload sent by Sepay IPN callback."""
    id: Optional[int] = None
    gateway: Optional[str] = None
    transaction_date: Optional[str] = None
    account_number: Optional[str] = None
    sub_account: Optional[str] = None
    amount_in: Optional[float] = None
    amount_out: Optional[float] = None
    accumulated: Optional[float] = None
    code: Optional[str] = None
    transaction_content: Optional[str] = None
    reference_number: Optional[str] = None
    body: Optional[str] = None
    transferType: Optional[str] = None


# ── Helper ───────────────────────────────────────────────────────────
def _generate_transfer_content(user_id: int) -> str:
    """Create a unique transfer description so webhook can identify the user."""
    return f"STOCKAI PREMIUM {user_id}"


def _extract_user_id_from_content(content: str) -> Optional[int]:
    """Parse user_id from bank transfer content like 'STOCKAI PREMIUM 42'."""
    if not content:
        return None
    # Normalize: uppercase, remove extra spaces
    normalized = re.sub(r"\s+", " ", content.strip().upper())
    match = re.search(r"STOCKAI\s*PREMIUM\s*(\d+)", normalized)
    if match:
        return int(match.group(1))
    return None


def _generate_vietqr_url(
    bank_name: str,
    account_number: str,
    account_name: str,
    amount: int,
    description: str,
) -> str:
    """Generate a VietQR quick-link that renders as a scannable QR code.
    Uses the public img.vietqr.io API."""
    # VietQR format: https://img.vietqr.io/image/<BANK_ID>-<ACCOUNT_NO>-<TEMPLATE>.png?amount=<AMT>&addInfo=<DESC>&accountName=<NAME>
    from urllib.parse import quote

    template = "compact2"
    base = f"https://img.vietqr.io/image/{bank_name}-{account_number}-{template}.png"
    params = f"amount={amount}&addInfo={quote(description)}&accountName={quote(account_name)}"
    return f"{base}?{params}"


# ── Endpoints ────────────────────────────────────────────────────────
@router.get("/premium-info", response_model=PaymentInfoResponse)
def get_premium_payment_info(current_user: User = Depends(require_auth)):
    """Return payment info + VietQR code for the current user to pay for Premium."""
    transfer_content = _generate_transfer_content(current_user.id)
    qr_url = _generate_vietqr_url(
        bank_name=SEPAY_BANK_NAME,
        account_number=SEPAY_BANK_ACCOUNT,
        account_name=SEPAY_ACCOUNT_NAME,
        amount=PREMIUM_PRICE,
        description=transfer_content,
    )
    return PaymentInfoResponse(
        bank_name=SEPAY_BANK_NAME,
        account_number=SEPAY_BANK_ACCOUNT,
        account_name=SEPAY_ACCOUNT_NAME,
        amount=PREMIUM_PRICE,
        transfer_content=transfer_content,
        qr_url=qr_url,
    )


@router.get("/subscription-status")
def get_subscription_status(
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Check if user's Premium subscription is active."""
    now = datetime.now(timezone.utc)

    active_sub = (
        db.query(UserSubscription)
        .filter(
            UserSubscription.user_id == current_user.id,
            UserSubscription.status == "completed",
            UserSubscription.expires_at > now,
        )
        .first()
    )

    return {
        "is_premium": current_user.role in ("premium", "admin"),
        "role": current_user.role,
        "active_subscription": {
            "plan": active_sub.plan_name,
            "expires_at": active_sub.expires_at.isoformat() if active_sub.expires_at else None,
        } if active_sub else None,
    }


@router.post("/sepay/webhook")
async def sepay_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Receive IPN from Sepay server when a bank transfer is completed.
    Flow:
    1. (Optional) Verify HMAC signature for production security
    2. Parse transfer content to extract user_id
    3. Validate amount >= PREMIUM_PRICE
    4. Create UserSubscription record & upgrade user role to 'premium'
    """
    try:
        body = await request.json()
        logger.info("[Sepay IPN] Received webhook: %s", body)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    # ── 1. Signature verification (production only) ──
    signature = request.headers.get("x-sepay-signature") or body.get("signature")
    if SEPAY_SECRET_KEY and signature:
        # Build payload string: sort keys, join as key=value
        filtered = {k: v for k, v in body.items() if k != "signature"}
        payload_str = "&".join(f"{k}={filtered[k]}" for k in sorted(filtered.keys()))

        expected_hex = hmac.new(
            SEPAY_SECRET_KEY.encode(), payload_str.encode(), hashlib.sha256
        ).hexdigest()

        if signature.strip() != expected_hex:
            logger.warning("[Sepay IPN] Invalid signature! received=%s expected=%s", signature, expected_hex)
            raise HTTPException(status_code=401, detail="Invalid signature")
        logger.info("[Sepay IPN] Signature verified OK")
    else:
        logger.warning("[Sepay IPN] No signature verification (OK in sandbox)")

    # ── 2. Parse transfer content ──
    transfer_content = body.get("transaction_content") or body.get("content") or body.get("body") or ""
    amount_in = float(body.get("amount_in") or body.get("amount") or 0)

    user_id = _extract_user_id_from_content(transfer_content)
    if user_id is None:
        logger.warning("[Sepay IPN] Could not parse user_id from content: %s", transfer_content)
        return {"success": True, "message": "IPN received but user not identified"}

    # ── 3. Validate amount ──
    if amount_in < PREMIUM_PRICE:
        logger.warning(
            "[Sepay IPN] Amount too low for user %s: %.0f < %d",
            user_id, amount_in, PREMIUM_PRICE,
        )
        return {"success": True, "message": "IPN received but amount insufficient"}

    # ── 4. Upgrade user ──
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning("[Sepay IPN] User %s not found", user_id)
        return {"success": True, "message": "IPN received but user not found"}

    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=PREMIUM_DURATION_DAYS)

    # Create subscription record
    subscription = UserSubscription(
        user_id=user.id,
        plan_name="premium_monthly",
        amount=amount_in,
        currency="VND",
        status="completed",
        payment_method="sepay",
        transaction_ref=body.get("reference_number") or body.get("code") or transfer_content,
        started_at=now,
        expires_at=expires,
    )
    db.add(subscription)

    # Upgrade role (only if not already admin)
    if user.role != "admin":
        user.role = "premium"

    db.commit()
    logger.info(
        "[Sepay IPN] User #%d upgraded to premium until %s (amount=%.0f)",
        user.id, expires.isoformat(), amount_in,
    )

    return {"success": True, "message": "IPN received, user upgraded to premium"}
