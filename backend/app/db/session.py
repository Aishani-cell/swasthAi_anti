"""
SwasthAI SQLite Database Session and Context Manager
Enforces active foreign-key constraints (PRAGMA foreign_keys = ON) and WAL mode.
"""
import sqlite3
import contextlib
from pathlib import Path
from typing import Generator
from backend.app.core.config import settings
from backend.app.core.security import hash_password
from backend.app.db.schema import CREATE_TABLES_SQL

def get_db_path() -> str:
    Path(settings.DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    return settings.DB_PATH

def init_db(db_path: str = None) -> None:
    """Initializes tables, indexes, and default administrative / clinical accounts."""
    path = db_path or get_db_path()
    conn = sqlite3.connect(path)
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.executescript(CREATE_TABLES_SQL)
        
        # Ensure any newly added patient columns exist on existing DBs
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(patients);")
        existing_cols = {row[1] for row in cursor.fetchall()}
        new_cols = [
            ("full_name", "TEXT"),
            ("phone_number", "TEXT"),
            ("email", "TEXT"),
            ("dob", "TEXT"),
            ("hashed_password", "TEXT")
        ]
        for col_name, col_type in new_cols:
            if col_name not in existing_cols:
                try:
                    conn.execute(f"ALTER TABLE patients ADD COLUMN {col_name} {col_type};")
                except Exception:
                    pass

        # Ensure vitals table supports height, weight, and calculated BMI
        cursor.execute("PRAGMA table_info(vitals);")
        existing_vitals_cols = {row[1] for row in cursor.fetchall()}
        vitals_new_cols = [
            ("weight_kg", "REAL"),
            ("height_cm", "REAL"),
            ("bmi", "REAL")
        ]
        for col_name, col_type in vitals_new_cols:
            if col_name not in existing_vitals_cols:
                try:
                    conn.execute(f"ALTER TABLE vitals ADD COLUMN {col_name} {col_type};")
                except Exception:
                    pass

        # Seed default clinical users if empty
        cursor.execute("SELECT COUNT(*) FROM users;")
        if cursor.fetchone()[0] == 0:
            default_users = [
                ("usr-admin-01", "admin", hash_password("SwasthAdmin@2026"), "System Administrator", "admin"),
                ("usr-doc-01", "dr.sharma", hash_password("Clinician@2026"), "Dr. Rajesh Sharma, MD", "clinician"),
                ("usr-asha-01", "asha.sunita", hash_password("AshaWorker@2026"), "Sunita Devi (ASHA)", "asha"),
                ("usr-anm-01", "anm.priya", hash_password("AnmWorker@2026"), "Priya Patel (ANM)", "anm"),
                ("usr-tech-01", "tech.rahul", hash_password("Technician@2026"), "Rahul Verma (Telemed Tech)", "technician")
            ]
            cursor.executemany(
                "INSERT INTO users (id, username, hashed_password, full_name, role) VALUES (?, ?, ?, ?, ?);",
                default_users
            )

        # Seed demo patient account if none exists
        cursor.execute("SELECT COUNT(*) FROM patients WHERE phone_number IS NOT NULL;")
        if cursor.fetchone()[0] == 0:
            import uuid
            from backend.app.core.privacy import hash_identifier
            demo_phone = "9876543210"
            demo_phone_hash = hash_identifier(demo_phone)
            demo_patient_id = "pat-demo-01"
            cursor.execute(
                """INSERT OR REPLACE INTO patients 
                   (id, phone_hash, pseudonym_id, full_name, phone_number, email, dob, hashed_password, age, sex, is_pregnant)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);""",
                (
                    demo_patient_id,
                    demo_phone_hash,
                    "SATNAVARI-DEMO",
                    "Aarav Patel",
                    demo_phone,
                    "aarav.patel@satnavari.in",
                    "1994-06-15",
                    hash_password("Patient@2026"),
                    30,
                    "MALE",
                    0
                )
            )
        conn.commit()
    finally:
        conn.close()

@contextlib.contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """Yields a SQLite connection configured with Row factory and foreign keys enabled."""
    path = get_db_path()
    conn = sqlite3.connect(path, timeout=15.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
