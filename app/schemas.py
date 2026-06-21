from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime, time, date
from typing import Optional, List

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
    otp_code: Optional[str] = None
    service_name: Optional[str] = None

class OTPRequest(BaseModel):
    customer_phone: str
    customer_name: str
    professional_id: UUID

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
    service_name: Optional[str] = None
    clinical_notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class AppointmentStatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None

class AppointmentReschedule(BaseModel):
    start_time: datetime

class AppointmentComplete(BaseModel):
    clinical_notes: str


# ─── Settings ───
class ClinicSettingsUpdate(BaseModel):
    clinic_name: Optional[str] = None
    address: Optional[str] = None
    opening_hours: Optional[str] = None
    appointment_duration_minutes: int
    msg_created: Optional[str] = None
    msg_confirmation: Optional[str] = None
    msg_feedback_confirmed: Optional[str] = None
    msg_feedback_cancelled: Optional[str] = None
    services: Optional[str] = None

class ClinicSettingsResponse(ClinicSettingsUpdate):
    id: str
    model_config = ConfigDict(from_attributes=True)

class ClinicServiceCreate(BaseModel):
    name: str
    duration_minutes: int
    price: Optional[str] = None
    professional_ids: Optional[List[str]] = None

class ClinicServiceResponse(BaseModel):
    id: UUID
    name: str
    duration_minutes: int
    price: Optional[str] = None
    professional_ids: Optional[List[str]] = None
    
    model_config = ConfigDict(from_attributes=True)

class TestConfirmationMessagePayload(BaseModel):
    telefone: str
    msg_confirmation: Optional[str] = None

class TestConfirmationMessageResponse(BaseModel):
    status: str
    preview: str
    appointment_id: str
    professional_name: str

class PatientResponse(BaseModel):
    name: str
    phone: str
    last_visit: Optional[datetime] = None
