from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
import uuid

from app.database import get_db
from app.models import ClinicService, Professional
from app.schemas import ClinicServiceCreate, ClinicServiceResponse
from app.security import get_current_user

router = APIRouter(prefix="/services", tags=["Services"])

@router.get("", response_model=List[ClinicServiceResponse])
async def get_services(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ClinicService).options(selectinload(ClinicService.professionals)))
    services = result.scalars().all()
    # Map professionals to professional_ids
    for s in services:
        s.professional_ids = [str(p.id) for p in s.professionals]
    return services

@router.post("", response_model=ClinicServiceResponse)
async def create_service(
    service_in: ClinicServiceCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if current_user.role != "master":
        raise HTTPException(status_code=403, detail="Apenas admin pode gerenciar serviços")
    
    new_service = ClinicService(
        name=service_in.name,
        duration_minutes=service_in.duration_minutes,
        price=service_in.price
    )
    
    if service_in.professional_ids is not None:
        prof_res = await db.execute(select(Professional).where(Professional.id.in_(service_in.professional_ids)))
        profs = prof_res.scalars().all()
        new_service.professionals = list(profs)
        
    db.add(new_service)
    await db.commit()
    await db.refresh(new_service)
    
    new_service.professional_ids = [str(p.id) for p in new_service.professionals]
    return new_service

@router.put("/{service_id}", response_model=ClinicServiceResponse)
async def update_service(
    service_id: str,
    service_in: ClinicServiceCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if current_user.role != "master":
        raise HTTPException(status_code=403, detail="Apenas admin pode gerenciar serviços")
        
    result = await db.execute(select(ClinicService).options(selectinload(ClinicService.professionals)).where(ClinicService.id == service_id))
    service = result.scalar_one_or_none()
    
    if not service:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
        
    service.name = service_in.name
    service.duration_minutes = service_in.duration_minutes
    service.price = service_in.price
    
    if service_in.professional_ids is not None:
        prof_res = await db.execute(select(Professional).where(Professional.id.in_(service_in.professional_ids)))
        profs = prof_res.scalars().all()
        service.professionals = list(profs)
        
    await db.commit()
    await db.refresh(service)
    
    service.professional_ids = [str(p.id) for p in service.professionals]
    return service

from pydantic import BaseModel
from typing import Optional, List

class ClinicServiceSync(BaseModel):
    id: Optional[str] = None
    name: str
    duration_minutes: int
    price: Optional[str] = None
    professional_ids: Optional[List[str]] = None

@router.put("/sync", response_model=List[ClinicServiceResponse])
async def sync_services(
    services_in: List[ClinicServiceSync],
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if current_user.role != "master":
        raise HTTPException(status_code=403, detail="Apenas admin pode gerenciar serviços")
        
    # Get all current services
    result = await db.execute(select(ClinicService).options(selectinload(ClinicService.professionals)))
    current_services = result.scalars().all()
    current_services_dict = {str(s.id): s for s in current_services}
    
    incoming_ids = [s.id for s in services_in if s.id and len(s.id) > 10]
    
    # Delete services not in incoming list
    for s_id, s in current_services_dict.items():
        if s_id not in incoming_ids:
            await db.delete(s)
            
    # Update or Create
    final_services = []
    for s_in in services_in:
        if s_in.id and s_in.id in current_services_dict:
            # Update
            service = current_services_dict[s_in.id]
            service.name = s_in.name
            service.duration_minutes = s_in.duration_minutes
            service.price = s_in.price
        else:
            # Create
            service = ClinicService(
                name=s_in.name,
                duration_minutes=s_in.duration_minutes,
                price=s_in.price
            )
            db.add(service)
            
        # Update professionals
        if s_in.professional_ids is not None:
            prof_res = await db.execute(select(Professional).where(Professional.id.in_(s_in.professional_ids)))
            profs = prof_res.scalars().all()
            service.professionals = list(profs)
            
        final_services.append(service)
        
    await db.commit()
    
    # Refresh to return
    for s in final_services:
        s.professional_ids = [str(p.id) for p in s.professionals]
        
    return final_services

@router.delete("/{service_id}")
async def delete_service(
    service_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if current_user.role != "master":
        raise HTTPException(status_code=403, detail="Apenas admin pode gerenciar serviços")
        
    result = await db.execute(select(ClinicService).where(ClinicService.id == service_id))
    service = result.scalar_one_or_none()
    
    if not service:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
        
    await db.delete(service)
    await db.commit()
    return {"status": "ok"}
