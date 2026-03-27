"""
Alerts API Router
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc, update
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from backend.database import get_db
from backend.models.models import Alert

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("/")
async def get_alerts(
    unread_only: bool = Query(False),
    priority: str = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Get alerts."""
    conditions = []
    if unread_only:
        conditions.append(Alert.is_read == False)
    if priority:
        conditions.append(Alert.priority == priority)

    query = select(Alert).order_by(desc(Alert.created_at)).limit(limit)
    if conditions:
        from sqlalchemy import and_
        query = query.where(and_(*conditions))

    result = await db.execute(query)
    alerts = result.scalars().all()

    return {
        "count": len(alerts),
        "alerts": [
            {
                "id": a.id,
                "signal_id": a.signal_id,
                "symbol": a.symbol,
                "alert_type": a.alert_type,
                "message": a.message,
                "priority": a.priority,
                "is_read": a.is_read,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in alerts
        ],
    }


@router.post("/{alert_id}/read")
async def mark_alert_read(alert_id: str, db: AsyncSession = Depends(get_db)):
    """Mark an alert as read."""
    await db.execute(update(Alert).where(Alert.id == alert_id).values(is_read=True))
    await db.commit()
    return {"status": "ok"}


@router.post("/read-all")
async def mark_all_read(db: AsyncSession = Depends(get_db)):
    """Mark all alerts as read."""
    await db.execute(update(Alert).values(is_read=True))
    await db.commit()
    return {"status": "ok"}
