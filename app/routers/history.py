from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.database import get_db
from app.db.models import User, Prediction
from app.core.deps import get_current_user
from app.schemas.complaint import HistoryItem

router = APIRouter(tags=["history"])


@router.get("/history", response_model=list[HistoryItem])
def get_history(
    label: Optional[str] = Query(None, description="Filter by 'Relief' or 'No Relief'"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Prediction).filter(Prediction.user_id == current_user.id)

    if label:
        query = query.filter(Prediction.predicted_label == label)

    predictions = query.order_by(desc(Prediction.created_at)).all()
    return predictions