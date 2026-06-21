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
    
    # 1. Requisitar novo QR
    connect_url = f"{base_url}/instance/connect/{settings.evolution_instance}"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(connect_url, headers=headers)
            
            # Se deu 404, significa que a instância não existe! Vamos criá-la.
            if response.status_code == 404:
                create_url = f"{base_url}/instance/create"
                create_payload = {
                    "instanceName": settings.evolution_instance,
                    "integration": "WHATSAPP-BAILEYS"
                }
                create_resp = await client.post(create_url, json=create_payload, headers=headers)
                if create_resp.status_code not in [200, 201]:
                    return {"error": f"Falha ao criar instância: {create_resp.status_code}", "detail": create_resp.text}
                
                # Aguarda 1 segundo e tenta conectar de novo para pegar o QR
                import asyncio
                await asyncio.sleep(1.5)
                response = await client.get(connect_url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                if "base64" in data:
                    # EV API v2 sometimes returns pure base64 without prefix, sometimes with prefix.
                    b64 = data["base64"]
                    if not b64.startswith("data:image"):
                        b64 = f"data:image/png;base64,{b64}"
                    return {"base64": b64}
                elif "qrcode" in data:
                    b64 = data["qrcode"]
                    if not b64.startswith("data:image"):
                        b64 = f"data:image/png;base64,{b64}"
                    return {"base64": b64}
                return {"error": "QR Code não retornado", "data": data}
            
            return {"error": f"Erro HTTP {response.status_code}", "detail": response.text}
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

@router.post("/logout")
async def logout_whatsapp_instance(current_user = Depends(get_current_user)):
    if current_user.role != "master":
        raise HTTPException(status_code=403, detail="Acesso negado")
        
    settings = get_settings()
    if not settings.evolution_api_url or not settings.evolution_api_key or not settings.evolution_instance:
        raise HTTPException(status_code=400, detail="Credenciais não configuradas")

    base_url = settings.evolution_api_url.rstrip('/')
    # Alterado de /logout/ para /delete/ para limpar sessões corrompidas do Baileys
    delete_url = f"{base_url}/instance/delete/{settings.evolution_instance}"
    headers = {"apikey": settings.evolution_api_key}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.delete(delete_url, headers=headers)
            if resp.status_code in [200, 201]:
                return {"success": True}
            # Se deu 404, significa que já está deletado ou não existe conexão, o que é sucesso para nós
            if resp.status_code == 404:
                return {"success": True}
            raise HTTPException(status_code=resp.status_code, detail="Erro ao deletar aparelho")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

