"""
Laboratory Pydantic Schemas
"""
from typing import Optional
from pydantic import BaseModel, Field

class ExtractedLabItem(BaseModel):
    analyte_name: str
    raw_value: str
    numeric_value: Optional[float] = None
    unit: Optional[str] = None
    reference_interval: Optional[str] = None
    specimen: Optional[str] = None
    qualifiers: Optional[str] = None
    confidence: float = 1.0

class ResolvedLabItem(BaseModel):
    analyte_name: str
    canonical_name: str
    loinc_code: Optional[str] = None
    raw_value: str
    numeric_value: Optional[float] = None
    unit: Optional[str] = None
    canonical_unit: Optional[str] = None
    reference_interval: Optional[str] = None
    verification_status: str = Field(..., pattern="^(VERIFIED|NEEDS_REVIEW|UNRESOLVED|INVALID_UNIT|IMPLAUSIBLE|INCOMPLETE)$")
    plausibility_flag: Optional[str] = None  # e.g., 'CRITICAL_HIGH', 'HIGH', 'NORMAL', 'LOW', 'CRITICAL_LOW'
    provenance: str = "DETERMINISTIC_LOINC_RESOLVER"
    notes: Optional[str] = None
