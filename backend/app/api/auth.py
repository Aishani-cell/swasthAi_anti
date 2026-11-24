"""
Authentication API Endpoints
"""
import uuid
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from backend.app.core.security import verify_password, create_access_token
from backend.app.db.session import get_db_connection
router = APIRouter(prefix="/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    username: str
    password: str

class PatientLoginRequest(BaseModel):
    identifier: str  # Phone number or email
    password: str

class PatientRegisterRequest(BaseModel):
    full_name: str
    phone_number: str
    password: str
    email: str = ""
    dob: str = ""
    age: int = 25
    sex: str = "FEMALE"
    is_pregnant: bool = False

class OperatorRegisterRequest(BaseModel):
    username: str  # Operator ID / employee code used for login
    password: str
    full_name: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    full_name: str
    role: str
    patient_id: str = ""

@router.post("/patient/login", response_model=TokenResponse)
def patient_login(req: PatientLoginRequest):
    from backend.app.core.privacy import hash_identifier
    ident = req.identifier.strip()
    ident_hash = hash_identifier(ident)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT id, pseudonym_id, full_name, phone_number, email, dob, hashed_password, age, sex, is_pregnant
               FROM patients 
               WHERE phone_hash = ? OR phone_number = ? OR email = ?;""",
            (ident_hash, ident, ident)
        )
        patient = cursor.fetchone()
        if not patient or not patient["hashed_password"]:
            raise HTTPException(status_code=401, detail="Invalid phone number, email or password")
        
        if not verify_password(req.password, patient["hashed_password"]):
            raise HTTPException(status_code=401, detail="Invalid phone number, email or password")
        
        token = create_access_token({
            "sub": patient["id"],
            "patient_id": patient["id"],
            "role": "patient",
            "name": patient["full_name"] or patient["pseudonym_id"]
        })
        
        return TokenResponse(
            access_token=token,
            user_id=patient["id"],
            full_name=patient["full_name"] or patient["pseudonym_id"],
            role="patient",
            patient_id=patient["id"]
        )

@router.post("/patient/register", response_model=TokenResponse)
def patient_register(req: PatientRegisterRequest):
    import uuid
    from backend.app.core.privacy import hash_identifier
    from backend.app.core.security import hash_password
    
    phone = req.phone_number.strip()
    if not phone or len(phone) < 10:
        raise HTTPException(status_code=400, detail="A valid 10-digit phone number is required")
        
    p_hash = hash_identifier(phone)
    p_id = f"pat-{uuid.uuid4().hex[:10]}"
    pseudonym = f"SATNAVARI-{uuid.uuid4().hex[:6].upper()}"
    hashed_pwd = hash_password(req.password)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM patients WHERE phone_hash = ? OR phone_number = ?;", (p_hash, phone))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="A patient with this phone number is already registered")
            
        cursor.execute(
            """INSERT INTO patients (id, phone_hash, pseudonym_id, full_name, phone_number, email, dob, hashed_password, age, sex, is_pregnant)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);""",
            (
                p_id,
                p_hash,
                pseudonym,
                req.full_name.strip(),
                phone,
                req.email.strip() if req.email else None,
                req.dob.strip() if req.dob else None,
                hashed_pwd,
                int(req.age),
                req.sex.upper(),
                int(req.is_pregnant)
            )
        )
        conn.commit()
        
    token = create_access_token({
        "sub": p_id,
        "patient_id": p_id,
        "role": "patient",
        "name": req.full_name.strip()
    })
    
    return TokenResponse(
        access_token=token,
        user_id=p_id,
        full_name=req.full_name.strip(),
        role="patient",
        patient_id=p_id
    )

@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, hashed_password, full_name, role FROM users WHERE username = ?;", (req.username,))
        user = cursor.fetchone()
        if not user or not verify_password(req.password, user["hashed_password"]):
            raise HTTPException(status_code=401, detail="Invalid username or password")

        token = create_access_token({
            "sub": user["id"],
            "username": user["username"],
            "role": user["role"]
        })

        return TokenResponse(
            access_token=token,
            user_id=user["id"],
            full_name=user["full_name"],
            role=user["role"]
        )

@router.post("/logout")
def logout():
    return {"status": "SUCCESS", "message": "Logged out successfully"}


@router.post("/register", response_model=TokenResponse)
def register_operator(req: OperatorRegisterRequest):
    """Register a new Healthpod Operator account.

    Internally the operator is created with an existing authorized worker
    role (technician); the frontend always presents the collective term
    "Healthpod Operator" and never exposes individual worker categories.
    """
    username = (req.username or "").strip()
    full_name = (req.full_name or "").strip()
    password = req.password or ""

    if not username or not full_name or len(password) < 6:
        raise HTTPException(status_code=400, detail="Username, full name and a password (min 6 characters) are required")

    from backend.app.core.security import hash_password

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?;", (username,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="An operator with this username is already registered")

        operator_id = f"usr-op-{uuid.uuid4().hex[:8]}"
        cursor.execute(
            """INSERT INTO users (id, username, hashed_password, full_name, role)
               VALUES (?, ?, ?, ?, 'technician');""",
            (operator_id, username, hash_password(password), full_name),
        )
        conn.commit()

    token = create_access_token({"sub": operator_id, "username": username, "role": "technician"})

    return TokenResponse(
        access_token=token,
        user_id=operator_id,
        full_name=full_name,
        role="technician",
    )
