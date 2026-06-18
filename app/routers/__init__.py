"""Pacote de routers da API."""
from app.routers import auth, appointments, users, professionals, availability, settings, blockouts

__all__ = ["auth", "appointments", "users", "professionals", "availability", "settings", "blockouts"]
