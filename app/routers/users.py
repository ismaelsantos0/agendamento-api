from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_master
from app.models import User
from app.schemas import UserCreate, UserOut
from app.security import hash_password

router = APIRouter(prefix="/users", tags=["Usuários"])

@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_master)])
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.username == payload.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Username já existe.")

    if payload.role == "master":
        admin_check = await db.execute(select(User.id).where(User.role == "master").limit(1))
        if admin_check.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Já existe um master.")

    user = User(username=payload.username, password_hash=hash_password(payload.password), role=payload.role)
    db.add(user)
    await db.flush()
    return user

@router.get("", response_model=list[UserOut], dependencies=[Depends(require_master)])
async def list_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).order_by(User.created_at))
    return result.scalars().all()
