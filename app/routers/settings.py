from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import AsyncSessionLocal, get_db
from app.models import ClinicSettings
from app.schemas import ClinicSettingsUpdate, ClinicSettingsResponse
from app.dependencies import get_current_user

router = APIRouter(prefix="/settings", tags=["Configurações"])

@router.get("", response_model=ClinicSettingsResponse)
async def get_settings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ClinicSettings).where(ClinicSettings.id == "default"))
    settings = result.scalar_one_or_none()
    if not settings:
        settings = ClinicSettings(id="default", appointment_duration_minutes=60, msg_created=None, msg_confirmation=None)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    return settings

@router.put("", response_model=ClinicSettingsResponse)
async def update_settings(
    settings_in: ClinicSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if current_user.role != "master":
        raise HTTPException(status_code=403, detail="Apenas admin pode alterar configurações")
    
    result = await db.execute(select(ClinicSettings).where(ClinicSettings.id == "default"))
    settings = result.scalar_one_or_none()
    if not settings:
        settings = ClinicSettings(id="default", appointment_duration_minutes=60, msg_created=None, msg_confirmation=None)
        db.add(settings)
    
    settings.appointment_duration_minutes = settings_in.appointment_duration_minutes
    if settings_in.msg_created is not None:
        settings.msg_created = settings_in.msg_created
    if settings_in.msg_confirmation is not None:
        settings.msg_confirmation = settings_in.msg_confirmation
        
    await db.commit()
    await db.refresh(settings)
    return settings
