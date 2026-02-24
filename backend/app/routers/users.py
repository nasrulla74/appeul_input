from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from .. import models, database, auth
from ..schemas import StatsResponse

router = APIRouter()

@router.get("/stats", response_model=StatsResponse)
def get_stats(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    total_invoices = db.query(func.count(models.Invoice.id)).filter(
        models.Invoice.owner_id == current_user.id
    ).scalar() or 0
    
    completed_invoices = db.query(func.count(models.Invoice.id)).filter(
        models.Invoice.owner_id == current_user.id,
        models.Invoice.status == "completed"
    ).scalar() or 0
    
    failed_invoices = db.query(func.count(models.Invoice.id)).filter(
        models.Invoice.owner_id == current_user.id,
        models.Invoice.status == "failed"
    ).scalar() or 0
    
    avg_confidence = db.query(func.avg(models.Invoice.confidence)).filter(
        models.Invoice.owner_id == current_user.id,
        models.Invoice.status == "completed"
    ).scalar() or 0
    
    success_rate = (completed_invoices / total_invoices * 100) if total_invoices > 0 else 0
    
    monthly_data = []
    for i in range(6):
        month_start = datetime.utcnow().replace(day=1) - timedelta(days=i*30)
        month_end = month_start + timedelta(days=30)
        count = db.query(func.count(models.Invoice.id)).filter(
            models.Invoice.owner_id == current_user.id,
            models.Invoice.created_at >= month_start,
            models.Invoice.created_at < month_end
        ).scalar() or 0
        monthly_data.append({
            "month": month_start.strftime("%Y-%m"),
            "count": count
        })
    monthly_data.reverse()
    
    return StatsResponse(
        total_invoices=total_invoices,
        completed_invoices=completed_invoices,
        failed_invoices=failed_invoices,
        average_confidence=round(avg_confidence, 2),
        success_rate=round(success_rate, 1),
        monthly_data=monthly_data
    )
