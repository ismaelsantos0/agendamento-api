from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, Time, DateTime, Date
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
import uuid
import datetime

from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="standard")
    is_active = Column(Boolean, default=True)


class Professional(Base):
    __tablename__ = "professionals"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    availability_rules = relationship("AvailabilityRule", back_populates="professional", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="professional")


class AvailabilityRule(Base):
    __tablename__ = "availability_rules"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    professional_id = Column(PG_UUID(as_uuid=True), ForeignKey("professionals.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0=Dom, 1=Seg...
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    professional = relationship("Professional", back_populates="availability_rules")

class ClinicSettings(Base):
    __tablename__ = "clinic_settings"

    id = Column(String, primary_key=True, default="default")
    clinic_name = Column(String, nullable=True)
    address = Column(String, nullable=True)
    opening_hours = Column(String, nullable=True)
    appointment_duration_minutes = Column(Integer, default=60, nullable=False)
    msg_created = Column(String, nullable=True)
    msg_confirmation = Column(String, nullable=True)
    msg_feedback_confirmed = Column(String, nullable=True)
    msg_feedback_cancelled = Column(String, nullable=True)
    services = Column(String, nullable=True)


class Blockout(Base):
    __tablename__ = "blockouts"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    professional_id = Column(PG_UUID(as_uuid=True), ForeignKey("professionals.id"), nullable=False)
    date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    professional = relationship("Professional")

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    professional_id = Column(PG_UUID(as_uuid=True), ForeignKey("professionals.id"), nullable=False)
    
    customer_name = Column(String, nullable=False)
    customer_phone = Column(String, nullable=False)
    
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    
    status = Column(String, default="pending") # pending, confirmed, cancelled, completed
    notes = Column(String, nullable=True)
    service_name = Column(String, nullable=True)

    professional = relationship("Professional", back_populates="appointments")

class OTPVerification(Base):
    __tablename__ = "otp_verifications"

    phone = Column(String, primary_key=True)
    code = Column(String, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
