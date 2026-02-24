from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from .. import models, database, auth

router = APIRouter()

class SettingsResponse(BaseModel):
    ai_provider: str
    default_model: str

class SettingsUpdate(BaseModel):
    ai_provider: str = "deepseek"
    deepseek_api_key: str | None = None
    openai_api_key: str | None = None
    default_model: str = "deepseek-chat"

@router.get("/settings", response_model=SettingsResponse)
def get_settings(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    settings = db.query(models.UserSettings).filter(
        models.UserSettings.user_id == current_user.id
    ).first()
    
    if not settings:
        settings = models.UserSettings(
            user_id=current_user.id,
            ai_provider="deepseek",
            default_model="deepseek-chat"
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    
    return {
        "ai_provider": settings.ai_provider,
        "default_model": settings.default_model
    }

@router.put("/settings")
def update_settings(
    settings: SettingsUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    user_settings = db.query(models.UserSettings).filter(
        models.UserSettings.user_id == current_user.id
    ).first()
    
    if not user_settings:
        user_settings = models.UserSettings(user_id=current_user.id)
        db.add(user_settings)
    
    user_settings.ai_provider = settings.ai_provider
    user_settings.default_model = settings.default_model
    
    if settings.deepseek_api_key:
        user_settings.deepseek_api_key = settings.deepseek_api_key
    if settings.openai_api_key:
        user_settings.openai_api_key = settings.openai_api_key
    
    db.commit()
    
    return {"message": "Settings updated successfully"}
