from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import timedelta, datetime, timezone
import uuid

from app.database import AsyncSessionLocal
from app.models import Appointment, Professional, ClinicSettings
from app.schemas import AppointmentCreate, AppointmentResponse, AppointmentStatusUpdate
from app.dependencies import get_current_user

router = APIRouter(prefix="/appointments", tags=["Agendamentos"])

async def get_db():
    async with AsyncSessionLocal() as db:
        yield db

@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(appt: AppointmentCreate, db: AsyncSession = Depends(get_db)):
    # Verifica se profissional existe
    prof = await db.get(Professional, appt.professional_id)
    if not prof or not prof.is_active:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")

    # Lê duração das configurações
    settings_res = await db.execute(select(ClinicSettings).where(ClinicSettings.id == "default"))
    settings = settings_res.scalar_one_or_none()
    duration_minutes = settings.appointment_duration_minutes if settings else 60

    # Duração dinâmica
    end_time = appt.start_time + timedelta(minutes=duration_minutes)

    # Verifica conflitos DESTE profissional
    conflict_query = select(Appointment).where(
        Appointment.professional_id == appt.professional_id,
        Appointment.status != "cancelled",
        Appointment.start_time < end_time,
        Appointment.end_time > appt.start_time
    )
    conflict = await db.execute(conflict_query)
    if conflict.scalars().first():
        raise HTTPException(status_code=400, detail="Profissional não tem disponibilidade neste horário")

    new_appt = Appointment(
        professional_id=appt.professional_id,
        customer_name=appt.customer_name,
        customer_phone=appt.customer_phone,
        start_time=appt.start_time,
        end_time=end_time,
        notes=appt.notes
    )
    db.add(new_appt)
    await db.commit()
    await db.refresh(new_appt)
    
    # Preenche o nome do prof pra retornar bonito
    response_data = AppointmentResponse.model_validate(new_appt)
    response_data.professional_name = prof.name
    
    # ─── AGENDAMENTO DE WHATSAPP ───────────────────────────────────────────────
    if appt.customer_phone:
        from app.scheduler import scheduler
        from app.services.whatsapp import enviar_mensagem
        import pytz
        from datetime import timezone
        
        # O start_time está em UTC
        hora_do_aviso = appt.start_time - timedelta(hours=2)
        agora = datetime.now(timezone.utc)
        
        data_formatada = appt.start_time.astimezone(pytz.timezone('America/Sao_Paulo')).strftime('%d/%m/%Y às %H:%M')
        texto_msg = (
            f"Olá {appt.customer_name}! Você tem um agendamento com {prof.name} "
            f"para {data_formatada}.\n\n"
            "Responda *1* para CONFIRMAR ou *2* para CANCELAR."
        )
        
        # Mensagem imediata de "Agendamento Criado"
        msg_criado = f"Olá {appt.customer_name}! 📅 Seu agendamento com {prof.name} para {data_formatada} foi registrado com sucesso!\n\n⏳ Nós enviaremos uma mensagem de confirmação 2 horas antes da consulta."
        scheduler.add_job(
            enviar_mensagem,
            trigger='date',
            run_date=agora,
            kwargs={"telefone": appt.customer_phone, "texto": msg_criado}
        )

        # Se faltar menos de 2 horas pro agendamento, NÃO precisamos agendar a confirmação para o passado,
        # enviaremos apenas a mensagem de "criado" que já serve como aviso.
        # Se for no futuro, agendamos a confirmação para 2 horas antes.
        if hora_do_aviso > agora:
            scheduler.add_job(
                enviar_mensagem,
                trigger='date',
                run_date=hora_do_aviso,
                kwargs={"telefone": appt.customer_phone, "texto": texto_msg}
            )
            
    return response_data

@router.get("", response_model=List[AppointmentResponse])
async def list_appointments(
    start_date: str = None, 
    end_date: str = None, 
    professional_id: uuid.UUID = None, 
    status: str = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Appointment, Professional.name.label("professional_name")).join(Professional)
    
    if professional_id:
        query = query.where(Appointment.professional_id == professional_id)
        
    if status:
        query = query.where(Appointment.status == status)
        
    if start_date:
        start_of_period = datetime.strptime(f"{start_date}T00:00:00", "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        query = query.where(Appointment.start_time >= start_of_period)
        
    if end_date:
        end_of_period = datetime.strptime(f"{end_date}T23:59:59", "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        query = query.where(Appointment.start_time <= end_of_period)
        
    query = query.order_by(Appointment.start_time.asc())
    
    result = await db.execute(query)
    
    response_list = []
    for appt, prof_name in result.all():
        resp = AppointmentResponse.model_validate(appt)
        resp.professional_name = prof_name
        response_list.append(resp)
        
    return response_list

@router.patch("/{appt_id}/status", response_model=AppointmentResponse)
async def update_status(
    appt_id: uuid.UUID,
    status_update: AppointmentStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if current_user.role != "master":
        raise HTTPException(status_code=403, detail="Apenas admin pode alterar status")
        
    appt = await db.get(Appointment, appt_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")
        
    appt.status = status_update.status
    if status_update.notes is not None:
        if appt.notes:
            appt.notes = appt.notes + "\n[Cancelamento]: " + status_update.notes
        else:
            appt.notes = "[Cancelamento]: " + status_update.notes
    await db.commit()
    await db.refresh(appt)
    return appt
