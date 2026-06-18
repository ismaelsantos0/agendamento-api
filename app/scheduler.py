"""
backend/app/scheduler.py
────────────────────────
Gerencia o APScheduler para tarefas em background.
"""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore

log = logging.getLogger(__name__)

# Configuração simples em memória (pois rodaremos apenas 1 worker principal ou o agendamento será recriado se o servidor reiniciar?
# Idealmente, o scheduler na memória se perde se o container reiniciar. 
# Para um sistema robusto, seria melhor usar o SQLAlchemyJobStore, mas MemoryJobStore atende para início imediato.
jobstores = {
    'default': MemoryJobStore()
}

scheduler = AsyncIOScheduler(jobstores=jobstores, timezone="UTC")

def start_scheduler():
    if not scheduler.running:
        scheduler.start()
        log.info("APScheduler iniciado.")

def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        log.info("APScheduler finalizado.")
