"""
Portfolio API Router
Allows authenticated users to manage their personal stock portfolio (watchlist).
Admin can also view any user's portfolio via the Admin API.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.api.auth import require_auth
from src.database.db import get_db
from src.database.models import User, UserPortfolio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/portfolio", tags=["Portfolio"])


# ── Schemas ──────────────────────────────────────────────────────────
class AddPortfolioItem(BaseModel):
    symbol: str = Field(min_length=1, max_length=50)
    quantity: int = Field(default=0, ge=0)
    avg_price: Optional[float] = None
    note: Optional[str] = None


class UpdatePortfolioItem(BaseModel):
    quantity: Optional[int] = Field(default=None, ge=0)
    avg_price: Optional[float] = None
    note: Optional[str] = None


# ── Endpoints ────────────────────────────────────────────────────────
@router.get("/")
def get_my_portfolio(
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Get all stocks in the current user's portfolio."""
    items = (
        db.query(UserPortfolio)
        .filter(UserPortfolio.user_id == current_user.id)
        .order_by(UserPortfolio.symbol)
        .all()
    )
    return {
        "count": len(items),
        "items": [
            {
                "id": item.id,
                "symbol": item.symbol,
                "quantity": item.quantity,
                "avg_price": item.avg_price,
                "note": item.note,
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "updated_at": item.updated_at.isoformat() if item.updated_at else None,
            }
            for item in items
        ],
    }


@router.post("/", status_code=201)
def add_to_portfolio(
    body: AddPortfolioItem,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Add a stock symbol to the user's portfolio."""
    symbol = body.symbol.strip().upper()

    # Check if symbol already exists
    existing = (
        db.query(UserPortfolio)
        .filter(UserPortfolio.user_id == current_user.id, UserPortfolio.symbol == symbol)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail=f"Mã {symbol} đã có trong danh mục")

    portfolio_item = UserPortfolio(
        user_id=current_user.id,
        symbol=symbol,
        quantity=body.quantity,
        avg_price=body.avg_price,
        note=body.note,
    )
    db.add(portfolio_item)
    db.commit()
    db.refresh(portfolio_item)

    return {
        "message": f"Đã thêm {symbol} vào danh mục",
        "item": {
            "id": portfolio_item.id,
            "symbol": portfolio_item.symbol,
            "quantity": portfolio_item.quantity,
            "avg_price": portfolio_item.avg_price,
            "note": portfolio_item.note,
        },
    }


@router.put("/{symbol}")
def update_portfolio_item(
    symbol: str,
    body: UpdatePortfolioItem,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Update quantity, avg_price, or note for a portfolio item."""
    normalized = symbol.strip().upper()
    item = (
        db.query(UserPortfolio)
        .filter(UserPortfolio.user_id == current_user.id, UserPortfolio.symbol == normalized)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail=f"Mã {normalized} không có trong danh mục")

    if body.quantity is not None:
        item.quantity = body.quantity
    if body.avg_price is not None:
        item.avg_price = body.avg_price
    if body.note is not None:
        item.note = body.note

    db.commit()
    return {
        "message": f"Đã cập nhật {normalized}",
        "item": {
            "id": item.id,
            "symbol": item.symbol,
            "quantity": item.quantity,
            "avg_price": item.avg_price,
            "note": item.note,
        },
    }


@router.delete("/{symbol}")
def remove_from_portfolio(
    symbol: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Remove a stock symbol from the user's portfolio."""
    normalized = symbol.strip().upper()
    item = (
        db.query(UserPortfolio)
        .filter(UserPortfolio.user_id == current_user.id, UserPortfolio.symbol == normalized)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail=f"Mã {normalized} không có trong danh mục")

    db.delete(item)
    db.commit()
    return {"message": f"Đã xóa {normalized} khỏi danh mục"}
