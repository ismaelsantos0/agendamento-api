from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import AsyncSessionLocal
from app.models import Professional
from app.schemas import ProfessionalCreate, ProfessionalResponse, ProfessionalUpdate
from app.dependencies import get_current_user

router = APIRouter(prefix="/professionals", tags=["Profissionais"])

async def get_db():
    async with AsyncSessionLocal() as db:
        yield db

@router.get("", response_model=List[ProfessionalResponse])
async def list_professionals(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Professional).where(Professional.is_active == True))
    return result.scalars().all()

@router.post("", response_model=ProfessionalResponse, status_code=status.HTTP_201_CREATED)
async def create_professional(
    prof: ProfessionalCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if current_user.role != "master":
        raise HTTPException(status_code=403, detail="Apenas admin pode criar profissionais")
    
    new_prof = Professional(**prof.model_dump())
    db.add(new_prof)
    await db.commit()
    await db.refresh(new_prof)
    return new_prof

@router.put("/{prof_id}", response_model=ProfessionalResponse)
async def update_professional(
    prof_id: str,
    prof_update: ProfessionalUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if current_user.role != "master":
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    result = await db.execute(select(Professional).where(Professional.id == prof_id))
    prof = result.scalar_one_or_none()
    if not prof:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")
    
    update_data = prof_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(prof, key, value)
        
    await db.commit()
    await db.refresh(prof)
    return prof
