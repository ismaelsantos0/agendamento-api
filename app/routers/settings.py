from datetime import datetime, timedelta

import pytz
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import AsyncSessionLocal, get_db
from app.models import ClinicSettings
from app.schemas import ClinicSettingsUpdate, ClinicSettingsResponse, TestConfirmationMessagePayload
from app.dependencies import get_current_user

DEFAULT_MSG_CONFIRMATION = (
    "Olá {cliente}! Você tem um agendamento com {profissional} para {data}.\n\n"
    "Responda *1* para CONFIRMAR ou *2* para CANCELAR."
)

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

@router.post("/test-confirmation")
async def test_confirmation_message(
    payload: TestConfirmationMessagePayload,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    if current_user.role != "master":
        raise HTTPException(status_code=403, detail="Apenas admin pode testar mensagens")

    result = await db.execute(select(ClinicSettings).where(ClinicSettings.id == "default"))
    settings = result.scalar_one_or_none()

    template = payload.msg_confirmation
    if template is None and settings:
        template = settings.msg_confirmation
    if not template:
        template = DEFAULT_MSG_CONFIRMATION

    tz = pytz.timezone("America/Sao_Paulo")
    sample_date = (datetime.now(tz) + timedelta(days=1)).replace(hour=14, minute=30, second=0, microsecond=0)
    data_formatada = sample_date.strftime("%d/%m/%Y às %H:%M")

    texto = (
        template
        .replace("{cliente}", "João Silva")
        .replace("{profissional}", "Dr. Carlos")
        .replace("{data}", data_formatada)
    )

    from app.services.whatsapp import enviar_mensagem

    sucesso = await enviar_mensagem(payload.telefone, texto)
    if not sucesso:
        raise HTTPException(status_code=500, detail="Falha ao enviar mensagem. Verifique a conexão do WhatsApp.")
    return {"status": "success", "preview": texto}
