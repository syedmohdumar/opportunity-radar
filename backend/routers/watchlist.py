"""
Watchlist API Router
"""
from fastapi import APIRouter, Depends, Body
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db
from backend.models.models import WatchlistItem
from pydantic import BaseModel
from typing import Optional
import uuid

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])


class WatchlistAdd(BaseModel):
    symbol: str
    company_name: str
    notes: Optional[str] = None


@router.get("/")
async def get_watchlist(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(WatchlistItem).order_by(WatchlistItem.added_at.desc()))
    items = result.scalars().all()
    return {
        "count": len(items),
        "items": [
            {
                "id": i.id,
                "symbol": i.symbol,
                "company_name": i.company_name,
                "notes": i.notes,
                "added_at": i.added_at.isoformat() if i.added_at else None,
            }
            for i in items
        ],
    }


@router.post("/")
async def add_to_watchlist(item: WatchlistAdd, db: AsyncSession = Depends(get_db)):
    # Check if already exists
    result = await db.execute(select(WatchlistItem).where(WatchlistItem.symbol == item.symbol.upper()))
    existing = result.scalar_one_or_none()
    if existing:
        return {"status": "already_exists", "id": existing.id}

    new_item = WatchlistItem(
        id=str(uuid.uuid4()),
        symbol=item.symbol.upper(),
        company_name=item.company_name,
        notes=item.notes,
    )
    db.add(new_item)
    await db.commit()
    return {"status": "added", "id": new_item.id}


@router.delete("/{symbol}")
async def remove_from_watchlist(symbol: str, db: AsyncSession = Depends(get_db)):
    await db.execute(delete(WatchlistItem).where(WatchlistItem.symbol == symbol.upper()))
    await db.commit()
    return {"status": "removed"}
