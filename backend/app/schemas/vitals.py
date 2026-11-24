"""
Vital Signs Pydantic Schemas
Includes physiologic ranges and data quality indicators.
"""
from typing import Optional
from pydantic import BaseModel, Field

class VitalsInput(BaseModel):
    systolic_bp: Optional[float] = Field(None, ge=40, le=300, description="Systolic Blood Pressure (mmHg)")
    diastolic_bp: Optional[float] = Field(None, ge=20, le=200, description="Diastolic Blood Pressure (mmHg)")
    heart_rate: Optional[float] = Field(None, ge=20, le=250, description="Pulse / Heart Rate (bpm)")
    respiratory_rate: Optional[float] = Field(None, ge=5, le=80, description="Respiratory Rate (breaths/min)")
    temperature_c: Optional[float] = Field(None, ge=30.0, le=45.0, description="Core Body Temperature (°C)")
    spo2: Optional[float] = Field(None, ge=40.0, le=100.0, description="Oxygen Saturation SpO2 (%)")
    blood_glucose_mg_dl: Optional[float] = Field(None, ge=10, le=1000, description="Random Blood Glucose (mg/dL)")

class VitalsResponse(VitalsInput):
    id: str
    encounter_id: str
    is_valid: bool
    recorded_at: str
