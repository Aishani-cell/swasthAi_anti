"""
SwasthAI Security & Authentication Module
Implements user authentication, role-based access control (RBAC), and session tokens.
Roles: 'asha', 'anm', 'technician', 'clinician', 'admin'
"""
import hashlib
import hmac
import os
import json
import base64
import time
from typing import Optional, Dict, Any
from backend.app.core.config import settings

def hash_password(password: str) -> str:
    """Secure PBKDF2-HMAC-SHA256 password hashing with random salt."""
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return f"{base64.b64encode(salt).decode('utf-8')}:{base64.b64encode(dk).decode('utf-8')}"

def verify_password(password: str, hashed: str) -> bool:
    """Verifies a password against its PBKDF2 hash."""
    try:
        salt_str, hash_str = hashed.split(":")
        salt = base64.b64decode(salt_str.encode('utf-8'))
        expected_dk = base64.b64decode(hash_str.encode('utf-8'))
        actual_dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return hmac.compare_digest(actual_dk, expected_dk)
    except Exception:
        return False

def create_access_token(data: Dict[str, Any], expires_delta_seconds: Optional[int] = None) -> str:
    """Generates a secure HMAC-SHA256 signed JSON Web Token without external library bloat."""
    header = {"alg": "HS256", "typ": "JWT"}
    payload = data.copy()
    now = int(time.time())
    exp = now + (expires_delta_seconds or (settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60))
    payload["iat"] = now
    payload["exp"] = exp
    
    encoded_header = base64.urlsafe_b64encode(json.dumps(header).encode('utf-8')).decode('utf-8').rstrip("=")
    encoded_payload = base64.urlsafe_b64encode(json.dumps(payload).encode('utf-8')).decode('utf-8').rstrip("=")
    
    signing_input = f"{encoded_header}.{encoded_payload}".encode('utf-8')
    signature = hmac.new(settings.SECRET_KEY.encode('utf-8'), signing_input, hashlib.sha256).digest()
    encoded_signature = base64.urlsafe_b64encode(signature).decode('utf-8').rstrip("=")
    
    return f"{encoded_header}.{encoded_payload}.{encoded_signature}"

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and validates a signed JWT token."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        encoded_header, encoded_payload, encoded_signature = parts
        
        signing_input = f"{encoded_header}.{encoded_payload}".encode('utf-8')
        expected_sig = hmac.new(settings.SECRET_KEY.encode('utf-8'), signing_input, hashlib.sha256).digest()
        actual_sig = base64.urlsafe_b64decode(encoded_signature + "=="[:(4 - len(encoded_signature) % 4) % 4])
        
        if not hmac.compare_digest(actual_sig, expected_sig):
            return None
            
        payload_bytes = base64.urlsafe_b64decode(encoded_payload + "=="[:(4 - len(encoded_payload) % 4) % 4])
        payload = json.loads(payload_bytes.decode('utf-8'))
        
        if payload.get("exp", 0) < int(time.time()):
            return None  # Expired
            
        return payload
    except Exception:
        return None
