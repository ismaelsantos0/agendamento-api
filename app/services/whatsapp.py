"""
backend/app/services/whatsapp.py
─────────────────────────────────
Integração com a Evolution API para disparo de mensagens.
"""
import logging
import httpx
from app.config import get_settings

log = logging.getLogger(__name__)
settings = get_settings()

async def enviar_mensagem(telefone: str, texto: str) -> bool:
    """
    Envia uma mensagem de texto via Evolution API.
    O telefone deve conter o DDI e DDD (ex: 5511999999999).
    """
    if not settings.evolution_api_url or not settings.evolution_api_key or not settings.evolution_instance:
        log.warning("Credenciais da Evolution API ausentes. Simulando envio no log.")
        log.info(f"[WPP SIMULADO -> {telefone}]: {texto}")
        return True

    # Formatar URL
    base_url = settings.evolution_api_url.rstrip('/')
    url = f"{base_url}/message/sendText/{settings.evolution_instance}"
    
    headers = {
        "apikey": settings.evolution_api_key,
        "Content-Type": "application/json"
    }
    
    payload = {
        "number": telefone,
        "text": texto
    }
    
    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            log.info(f"[WPP ENVIADO -> {telefone}] Status: {response.status_code}")
            return True
    except httpx.HTTPStatusError as exc:
        log.error(f"[WPP ERRO HTTP -> {telefone}] Status: {exc.response.status_code} - Body: {exc.response.text}")
        return False
    except Exception as exc:
        log.error(f"[WPP ERRO REDE -> {telefone}] Erro: {str(exc)}")
        return False
