"""Pacote de routers da API."""
from app.routers import auth, appointments, users, services, availability

__all__ = ["auth", "appointments", "users", "services", "availability"]
