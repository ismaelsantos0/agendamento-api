import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text

from app.config import get_settings
from app.database import AsyncSessionLocal, engine, Base
from app.models import User
from app.routers import auth, appointments, users, professionals, availability, settings as settings_router, blockouts
from app.security import hash_password

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
log = logging.getLogger(__name__)
settings = get_settings()

async def seed_master() -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.username == settings.admin_username))
        user = result.scalar_one_or_none()
        from app.security import get_password_hash
        
        if not user:
            log.info(f"[DB] Criando usuário admin: {settings.admin_username}")
            new_user = User(
                username=settings.admin_username,
                password_hash=get_password_hash(settings.admin_password),
                role="master"
            )
            db.add(new_user)
            await db.commit()
        else:
            # Atualiza a senha caso ela tenha mudado no código
            log.info(f"[DB] Atualizando senha do admin: {settings.admin_username}")
            user.password_hash = get_password_hash(settings.admin_password)
            await db.commit()

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("=== Iniciando Sistema de Agendamento ===")
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
        log.info("[DB] Conexão com PostgreSQL estabelecida.")
    except Exception as exc:
        log.error(f"[DB] Falha ao conectar: {exc}")
        raise

    log.info("[DB] Sincronizando tabelas no PostgreSQL...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await seed_master()
    yield

app = FastAPI(
    title="Agendamentos API",
    description="API do Sistema de Agendamentos",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(professionals.router)
app.include_router(availability.router)
app.include_router(blockouts.router)
app.include_router(appointments.router)
app.include_router(settings_router.router)

@app.get("/health", tags=["Sistema"])
async def health_check():
    return {"status": "ok", "service": "agendamentos-api"}

@app.get("/reset-db-danger", tags=["Sistema"])
async def reset_db():
    log.warning("ZERANDO O BANCO DE DADOS...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await seed_master()
    return {"status": "Banco recriado com sucesso! Volte ao painel e crie o profissional novamente."}
