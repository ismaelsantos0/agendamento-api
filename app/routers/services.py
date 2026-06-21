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
