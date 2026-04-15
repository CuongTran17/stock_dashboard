"""
Admin API Router
Provides endpoints for admin dashboard: sales stats, user management,
and customer portfolio overview for advisory purposes.
"""
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.api.auth import require_auth, require_role
from src.database.db import get_db
from src.database.models import AIPrediction, User, UserPortfolio, UserSubscription

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Admin"])


# ── Dependencies ─────────────────────────────────────────────────────
_require_admin = require_role("admin")


# ── Endpoints ────────────────────────────────────────────────────────
@router.get("/sales-stats")
def get_sales_stats(
    current_user: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """
    Return revenue statistics for Premium subscriptions.
    Includes: total revenue, total subscribers, active subs, monthly breakdown.
    """
    # Total revenue from completed subscriptions
    total_revenue = (
        db.query(func.coalesce(func.sum(UserSubscription.amount), 0))
        .filter(UserSubscription.status == "completed")
        .scalar()
    )

    # Total completed subscriptions
    total_subscriptions = (
        db.query(func.count(UserSubscription.id))
        .filter(UserSubscription.status == "completed")
        .scalar()
    )

    # Currently active premium users
    now = datetime.now(timezone.utc)
    active_premium_count = (
        db.query(func.count(User.id))
        .filter(User.role.in_(["premium", "admin"]))
        .scalar()
    )

    # Total registered users
    total_users = db.query(func.count(User.id)).scalar()

    # Pending subscriptions (awaiting payment)
    pending_count = (
        db.query(func.count(UserSubscription.id))
        .filter(UserSubscription.status == "pending")
        .scalar()
    )

    # Monthly revenue breakdown (last 12 months)
    monthly_revenue = (
        db.query(
            func.date_format(UserSubscription.created_at, "%Y-%m").label("month"),
            func.sum(UserSubscription.amount).label("revenue"),
            func.count(UserSubscription.id).label("count"),
        )
        .filter(UserSubscription.status == "completed")
        .group_by(func.date_format(UserSubscription.created_at, "%Y-%m"))
        .order_by(func.date_format(UserSubscription.created_at, "%Y-%m").desc())
        .limit(12)
        .all()
    )

    return {
        "total_revenue": float(total_revenue),
        "total_subscriptions": total_subscriptions,
        "active_premium_count": active_premium_count,
        "total_users": total_users,
        "pending_count": pending_count,
        "monthly_revenue": [
            {"month": row.month, "revenue": float(row.revenue), "count": row.count}
            for row in monthly_revenue
        ],
    }


@router.get("/users")
def list_users(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    role: Optional[str] = Query(default=None),
    current_user: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """List all users with pagination and optional role filter."""
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)

    total = query.count()
    users = (
        query.order_by(User.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "phone": u.phone,
                "fullname": u.fullname,
                "role": u.role,
                "is_locked": u.is_locked,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ],
    }


@router.get("/user-portfolios")
def get_all_user_portfolios(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """
    Return all users' portfolios for admin advisory.
    Grouped by user, showing their stock holdings.
    """
    # Get distinct users who have portfolios
    portfolio_user_ids = (
        db.query(UserPortfolio.user_id)
        .distinct()
        .order_by(UserPortfolio.user_id)
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    user_ids = [row[0] for row in portfolio_user_ids]

    if not user_ids:
        return {"total": 0, "page": page, "per_page": per_page, "portfolios": []}

    # Fetch users and their portfolios
    users = db.query(User).filter(User.id.in_(user_ids)).all()
    user_map = {u.id: u for u in users}

    portfolios_by_user: dict[int, list[dict[str, Any]]] = {}
    all_portfolios = (
        db.query(UserPortfolio)
        .filter(UserPortfolio.user_id.in_(user_ids))
        .order_by(UserPortfolio.symbol)
        .all()
    )

    for p in all_portfolios:
        if p.user_id not in portfolios_by_user:
            portfolios_by_user[p.user_id] = []
        portfolios_by_user[p.user_id].append({
            "symbol": p.symbol,
            "quantity": p.quantity,
            "avg_price": p.avg_price,
            "note": p.note,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        })

    total = db.query(func.count(func.distinct(UserPortfolio.user_id))).scalar()

    result = []
    for uid in user_ids:
        user = user_map.get(uid)
        if not user:
            continue
        result.append({
            "user": {
                "id": user.id,
                "email": user.email,
                "fullname": user.fullname,
                "role": user.role,
            },
            "holdings": portfolios_by_user.get(uid, []),
            "total_symbols": len(portfolios_by_user.get(uid, [])),
        })

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "portfolios": result,
    }


@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    role: str = Query(..., pattern="^(user|premium|admin)$"),
    current_user: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """Admin: manually update a user's role."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")

    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Không thể thay đổi role của chính mình")

    user.role = role
    db.commit()
    return {"message": f"Đã cập nhật role thành '{role}' cho {user.email}"}


@router.put("/users/{user_id}/lock")
def lock_user(
    user_id: int,
    reason: str = Query(default="Vi phạm quy định"),
    current_user: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """Admin: lock a user account."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")

    user.is_locked = True
    user.locked_reason = reason
    db.commit()
    return {"message": f"Đã khóa tài khoản {user.email}"}


@router.put("/users/{user_id}/unlock")
def unlock_user(
    user_id: int,
    current_user: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """Admin: unlock a user account."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")

    user.is_locked = False
    user.locked_reason = None
    db.commit()
    return {"message": f"Đã mở khóa tài khoản {user.email}"}
