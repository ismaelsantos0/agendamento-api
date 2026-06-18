"""
backend/app/routers/webhooks.py
───────────────────────────────
Escuta eventos da Evolution API.
"""
import logging
from fastapi import APIRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.database import get_db
from app.models import Appointment, Professional
from app.services.whatsapp import enviar_mensagem
from app.config import get_settings

log = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["Webhooks"])
settings = get_settings()

@router.post("/whatsapp")
async def receber_resposta_wpp(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Recebe os eventos (messages.upsert) da Evolution API e
    atualiza o status do agendamento se o cliente responder 1 ou 2.
    """
    try:
        payload = await request.json()
    except Exception:
        return {"status": "ok"} # Ignora se não for JSON

    # Verifica se é um evento de mensagem recebida
    if payload.get("event") == "messages.upsert":
        data = payload.get("data", {})
        message_data = data.get("message", {})
        
        # Pega o texto da mensagem. Pode vir em text, conversation ou extendedTextMessage
        texto_msg = message_data.get("conversation") or message_data.get("extendedTextMessage", {}).get("text", "")
        texto_msg = texto_msg.strip()
        
        remote_jid = data.get("key", {}).get("remoteJid", "")
        telefone = remote_jid.split("@")[0] # extrai 5595999999999
        
        if not telefone or not texto_msg:
            return {"status": "ok"}
            
        # Verifica se respondeu 1 ou 2
        if texto_msg == "1":
            novo_status = "confirmed"
            msg_feedback = "Seu agendamento foi *CONFIRMADO* com sucesso! Aguardamos você."
        elif texto_msg == "2":
            novo_status = "cancelled"
            msg_feedback = "Seu agendamento foi *CANCELADO*."
        else:
            # Resposta não reconhecida, ignora (ou poderia mandar "Opção inválida")
            return {"status": "ok"}
            
        # Busca o agendamento mais recente desse telefone que esteja como 'pending'
        # Em um sistema avançado, buscaria pela data mais próxima no futuro
        query = select(Appointment, Professional).join(Professional).where(
            and_(
                Appointment.customer_phone == telefone,
                Appointment.status == "pending"
            )
        ).order_by(Appointment.start_time.asc()).limit(1)
        
        result = await db.execute(query)
        row = result.first()
        
        if row:
            appt, prof = row
            appt.status = novo_status
            
            if novo_status == "cancelled":
                appt.notes = (appt.notes + "\n[WhatsApp]: Cliente cancelou via robô.") if appt.notes else "[WhatsApp]: Cliente cancelou via robô."
                
            await db.commit()
            
            # Avisa o cliente que deu certo
            await enviar_mensagem(telefone, msg_feedback)
            
            # Se for cancelado, avisa o admin
            if novo_status == "cancelled" and settings.admin_phone:
                import pytz
                data_formatada = appt.start_time.astimezone(pytz.timezone('America/Sao_Paulo')).strftime('%d/%m/%Y às %H:%M')
                aviso_admin = f"⚠️ *ATENÇÃO: CANCELAMENTO*\nO cliente {appt.customer_name} cancelou a consulta com {prof.name} do dia {data_formatada}."
                await enviar_mensagem(settings.admin_phone, aviso_admin)
                
    # Sempre retorne status 200 rápido
    return {"status": "ok"}
