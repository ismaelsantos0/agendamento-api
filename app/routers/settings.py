from datetime import datetime, timedelta, timezone

import pytz
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import AsyncSessionLocal, get_db
from app.models import ClinicSettings, Appointment, Professional
from app.schemas import (
    ClinicSettingsUpdate,
    ClinicSettingsResponse,
    TestConfirmationMessagePayload,
    TestConfirmationMessageResponse,
)
from app.dependencies import get_current_user
from app.utils.phone import normalize_phone

DEFAULT_MSG_CONFIRMATION = (
    "Olá {cliente}! Você tem um agendamento com {profissional} para {data}.\n\n"
    "Responda *1* para CONFIRMAR ou *2* para CANCELAR."
)
TEST_NOTE = "[TESTE WhatsApp] Agendamento criado para teste de resposta 1/2"

router = APIRouter(prefix="/settings", tags=["Configurações"])

@router.get("", response_model=ClinicSettingsResponse)
async def get_settings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ClinicSettings).where(ClinicSettings.id == "default"))
    settings = result.scalar_one_or_none()
    if not settings:
        settings = ClinicSettings(
            id="default",
            appointment_duration_minutes=60,
            msg_created=None,
            msg_confirmation=None,
            msg_feedback_confirmed=None,
            msg_feedback_cancelled=None
        )
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
        settings = ClinicSettings(
            id="default",
            appointment_duration_minutes=60,
            msg_created=None,
            msg_confirmation=None,
            msg_feedback_confirmed=None,
            msg_feedback_cancelled=None
        )
        db.add(settings)
    
    settings.appointment_duration_minutes = settings_in.appointment_duration_minutes
    if settings_in.msg_created is not None:
        settings.msg_created = settings_in.msg_created
    if settings_in.msg_confirmation is not None:
        settings.msg_confirmation = settings_in.msg_confirmation
    if settings_in.msg_feedback_confirmed is not None:
        settings.msg_feedback_confirmed = settings_in.msg_feedback_confirmed
    if settings_in.msg_feedback_cancelled is not None:
        settings.msg_feedback_cancelled = settings_in.msg_feedback_cancelled
        
    await db.commit()
    await db.refresh(settings)
    return settings

@router.post("/test-confirmation", response_model=TestConfirmationMessageResponse)
async def test_confirmation_message(
    payload: TestConfirmationMessagePayload,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    if current_user.role != "master":
        raise HTTPException(status_code=403, detail="Apenas admin pode testar mensagens")

    telefone = normalize_phone(payload.telefone)
    if len(telefone) < 12:
        raise HTTPException(status_code=400, detail="Informe o número com DDI e DDD (ex: 5511999999999)")

    result = await db.execute(select(ClinicSettings).where(ClinicSettings.id == "default"))
    settings = result.scalar_one_or_none()

    prof_result = await db.execute(
        select(Professional).where(Professional.is_active == True).limit(1)
    )
    prof = prof_result.scalar_one_or_none()
    if not prof:
        raise HTTPException(status_code=400, detail="Cadastre um profissional ativo antes de testar")

    duration_minutes = settings.appointment_duration_minutes if settings else 60

    old_tests = await db.execute(
        select(Appointment).where(
            Appointment.customer_phone == telefone,
            Appointment.status == "pending",
            Appointment.notes.contains("[TESTE WhatsApp]"),
        )
    )
    for old in old_tests.scalars():
        old.status = "cancelled"
        old.notes = f"{old.notes or ''}\n[Cancelado]: substituído por novo teste"

    tz = pytz.timezone("America/Sao_Paulo")
    sample_date = (datetime.now(tz) + timedelta(days=1)).replace(hour=14, minute=30, second=0, microsecond=0)
    start_time = sample_date.astimezone(timezone.utc)
    data_formatada = sample_date.strftime("%d/%m/%Y às %H:%M")
    customer_name = "João Silva (TESTE)"

    template = payload.msg_confirmation
    if template is None and settings:
        template = settings.msg_confirmation
    if not template:
        template = DEFAULT_MSG_CONFIRMATION

    texto = (
        template
        .replace("{cliente}", customer_name)
        .replace("{profissional}", prof.name)
        .replace("{data}", data_formatada)
    )

    new_appt = Appointment(
        professional_id=prof.id,
        customer_name=customer_name,
        customer_phone=telefone,
        start_time=start_time,
        end_time=start_time + timedelta(minutes=duration_minutes),
        status="pending",
        notes=TEST_NOTE,
    )
    db.add(new_appt)
    await db.commit()
    await db.refresh(new_appt)

    from app.services.whatsapp import enviar_mensagem

    sucesso, err_msg = await enviar_mensagem(telefone, texto)
    if not sucesso:
        raise HTTPException(status_code=500, detail=f"Falha ao enviar: {err_msg}")

    return TestConfirmationMessageResponse(
        status="success",
        preview=texto,
        appointment_id=str(new_appt.id),
        professional_name=prof.name,
        customer_name=customer_name,
    )
