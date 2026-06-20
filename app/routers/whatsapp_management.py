from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import httpx
import logging

from app.config import get_settings
from app.dependencies import get_current_user

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp Management"])
log = logging.getLogger(__name__)

class TestMessagePayload(BaseModel):
    telefone: str
    texto: str

@router.get("/status")
async def get_whatsapp_status(current_user = Depends(get_current_user)):
    if current_user.role != "master":
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    settings = get_settings()
    if not settings.evolution_api_url or not settings.evolution_api_key or not settings.evolution_instance:
        return {"status": "unconfigured"}

    url = f"{settings.evolution_api_url.rstrip('/')}/instance/connectionState/{settings.evolution_instance}"
    headers = {"apikey": settings.evolution_api_key}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                state = data.get("instance", {}).get("state", "disconnected")
                return {"status": state}
            return {"status": "error", "detail": response.text}
    except Exception as e:
        log.error(f"Erro ao checar status do WhatsApp: {e}")
        return {"status": "offline"}

@router.get("/qr")
async def get_whatsapp_qr(current_user = Depends(get_current_user)):
    if current_user.role != "master":
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    settings = get_settings()
    if not settings.evolution_api_url or not settings.evolution_api_key or not settings.evolution_instance:
        raise HTTPException(status_code=400, detail="Credenciais não configuradas")

    base_url = settings.evolution_api_url.rstrip('/')
    headers = {"apikey": settings.evolution_api_key}
    
    # 1. Deslogar primeiro para forçar geração de novo QR Code
    logout_url = f"{base_url}/instance/logout/{settings.evolution_instance}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.delete(logout_url, headers=headers)
    except Exception:
        pass # Ignora erro no logout, pois pode já estar deslogado

    # 2. Requisitar novo QR
    connect_url = f"{base_url}/instance/connect/{settings.evolution_instance}"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(connect_url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if "base64" in data:
                    return {"base64": data["base64"]}
                return {"error": "QR Code não retornado", "data": data}
            return {"error": "Erro ao gerar QR Code", "detail": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test")
async def send_test_message(payload: TestMessagePayload, current_user = Depends(get_current_user)):
    if current_user.role != "master":
        raise HTTPException(status_code=403, detail="Acesso negado")
        
    from app.services.whatsapp import enviar_mensagem
    sucesso, err_msg = await enviar_mensagem(payload.telefone, payload.texto)
    if not sucesso:
        raise HTTPException(status_code=500, detail=f"Falha ao enviar: {err_msg}")
    return {"status": "success"}
