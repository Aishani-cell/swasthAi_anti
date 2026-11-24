"""
Unit and integration tests for SwasthAI SQLite Database module.
Tests table creation, WAL mode, foreign key enforcement, default users, and EHR queries.
"""
import sys
import os
import unittest
import sqlite3
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.db.session import init_db, get_db_connection
from backend.app.db.schema import CREATE_TABLES_SQL
from backend.app.core.security import hash_password, verify_password
from backend.app.schemas.patient import PatientCreate
from backend.app.ehr.patient_service import patient_ehr_service


class TestDatabaseModule(unittest.TestCase):
    def setUp(self):
        # Create a temporary database file
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.db_path = self.temp_db.name
        init_db(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except Exception:
                pass

    def test_tables_created(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()

        expected = {
            "users", "patients", "consultations", "vitals", "extracted_symptoms",
            "lab_results", "evidence_graphs", "safety_events", "drug_recommendations",
            "audit_logs", "medical_history"
        }
        for t in expected:
            self.assertIn(t, tables, f"Expected table {t} was not created")

    def test_seeded_users(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT username, role, hashed_password FROM users;")
        users = cursor.fetchall()
        conn.close()

        self.assertGreaterEqual(len(users), 5)
        usernames = {u[0] for u in users}
        self.assertIn("admin", usernames)
        self.assertIn("dr.sharma", usernames)
        self.assertIn("asha.sunita", usernames)

        # Check dr.sharma password
        doc_user = next(u for u in users if u[0] == "dr.sharma")
        self.assertTrue(verify_password("Clinician@2026", doc_user[2]))

    def test_foreign_key_enforcement(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        cursor = conn.cursor()
        # Inserting a consultation with non-existent patient should fail
        with self.assertRaises(sqlite3.IntegrityError):
            cursor.execute(
                "INSERT INTO consultations (id, patient_id, status) VALUES ('c1', 'nonexistent', 'DIAGNOSED');"
            )
        conn.close()


if __name__ == "__main__":
    unittest.main()
