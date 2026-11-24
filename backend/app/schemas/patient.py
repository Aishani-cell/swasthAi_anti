"""
Patient Pydantic Schemas
Strictly enforces privacy boundaries and data minimization.
"""
from typing import Optional, List
from pydantic import BaseModel, Field

class PatientCreate(BaseModel):
    phone_number: str = Field(..., description="Phone number (will be immediately hashed via SHA-256)")
    full_name: Optional[str] = Field(None, description="Patient name for local display only; scrubbed from models")
    age: Optional[int] = Field(None, ge=0, le=125, description="Patient age in years")
    sex: str = Field(..., pattern="^(MALE|FEMALE|OTHER|UNKNOWN)$", description="Gender identity")
    is_pregnant: bool = Field(False, description="Pregnancy status where applicable")
    aadhaar_number: Optional[str] = Field(None, description="National ID (will be hashed)")
    email: Optional[str] = Field(None, description="Optional patient email")
    dob: Optional[str] = Field(None, description="Optional date of birth YYYY-MM-DD")

class PatientResponse(BaseModel):
    id: str
    pseudonym_id: str
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    age: Optional[int]
    sex: str
    is_pregnant: bool
    created_at: str

class MedicalHistoryEntry(BaseModel):
    condition_name: str
    icd10_code: Optional[str] = None
    status: str = "ACTIVE"
    allergies: List[str] = []
    current_medications: List[str] = []
    diagnosed_date: Optional[str] = None
