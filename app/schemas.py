from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime, time, date
from typing import Optional


# ─── Auth ───
class Token(BaseModel):
    access_token: str
    token_type: str

# ─── Users ───
class UserCreate(BaseModel):
    username: str
    password: str
    role: Optional[str] = "standard"

class UserOut(BaseModel):
    id: UUID
    username: str
    role: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


# ─── Professional ───
class ProfessionalCreate(BaseModel):
    name: str
    is_active: bool = True

class ProfessionalResponse(ProfessionalCreate):
    id: UUID
    model_config = ConfigDict(from_attributes=True)


# ─── Availability Rule ───
class AvailabilityRuleCreate(BaseModel):
    professional_id: UUID
    day_of_week: int
    start_time: time
    end_time: time

class AvailabilityRuleResponse(AvailabilityRuleCreate):
    id: UUID
    model_config = ConfigDict(from_attributes=True)


# ─── Blockouts ───
class BlockoutCreate(BaseModel):
    professional_id: UUID
    date: date
    start_time: time
    end_time: time

class BlockoutResponse(BlockoutCreate):
    id: UUID
    model_config = ConfigDict(from_attributes=True)


# ─── Appointment ───
class AppointmentCreate(BaseModel):
    professional_id: UUID
    customer_name: str
    customer_phone: str
    start_time: datetime
    notes: Optional[str] = None

class AppointmentResponse(BaseModel):
    id: UUID
    professional_id: UUID
    professional_name: Optional[str] = None
    customer_name: str
    customer_phone: str
    start_time: datetime
    end_time: datetime
    status: str
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class AppointmentStatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None


# ─── Settings ───
class ClinicSettingsUpdate(BaseModel):
    appointment_duration_minutes: int
    msg_created: Optional[str] = None
    msg_confirmation: Optional[str] = None

class ClinicSettingsResponse(ClinicSettingsUpdate):
    id: str
    model_config = ConfigDict(from_attributes=True)

class TestConfirmationMessagePayload(BaseModel):
    telefone: str
    msg_confirmation: Optional[str] = None

class TestConfirmationMessageResponse(BaseModel):
    status: str
    preview: str
    appointment_id: str
    professional_name: str
    customer_name: str
