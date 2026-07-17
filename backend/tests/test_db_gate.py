import os
import sqlite3
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.core.db_gate import get_db_gate_status

def test_db_gate_default_locked(monkeypatch):
    monkeypatch.delenv("ALLOW_PRODUCTION_DB", raising=False)
    monkeypatch.delenv("ENABLE_PRODUCTION_DB_READONLY_GATE", raising=False)
    monkeypatch.delenv("PRODUCTION_DB_PATH", raising=False)
    
    status = get_db_gate_status()
    assert status["gate_locked"] is True
    assert status["can_attempt_readonly_connection"] is False
    assert status["error_category"] == "LOCKED"

def test_db_gate_blank_path_locked(monkeypatch):
    monkeypatch.setenv("ALLOW_PRODUCTION_DB", "true")
    monkeypatch.setenv("ENABLE_PRODUCTION_DB_READONLY_GATE", "true")
    monkeypatch.setenv("PRODUCTION_DB_PATH", "   ")
    
    status = get_db_gate_status()
    assert status["gate_locked"] is True

def test_db_gate_readonly_false_rejected(monkeypatch):
    monkeypatch.setenv("ALLOW_PRODUCTION_DB", "true")
    monkeypatch.setenv("ENABLE_PRODUCTION_DB_READONLY_GATE", "true")
    monkeypatch.setenv("PRODUCTION_DB_PATH", "dummy.db")
    monkeypatch.setenv("PRODUCTION_DB_READONLY_REQUIRED", "false")
    
    status = get_db_gate_status()
    assert status["gate_locked"] is True
    assert status["error_category"] == "UNSAFE_READONLY_NOT_REQUIRED"

def test_db_gate_successful_readonly_connection(monkeypatch, tmp_path):
    db_file = tmp_path / "prod_fake.db"
    conn = sqlite3.connect(str(db_file))
    conn.execute("CREATE TABLE positions (id INTEGER PRIMARY KEY);")
    conn.execute("CREATE TABLE unknown_table (id INTEGER);")
    conn.close()
    
    monkeypatch.setenv("ALLOW_PRODUCTION_DB", "true")
    monkeypatch.setenv("ENABLE_PRODUCTION_DB_READONLY_GATE", "true")
    monkeypatch.setenv("PRODUCTION_DB_PATH", str(db_file))
    monkeypatch.setenv("PRODUCTION_DB_READONLY_REQUIRED", "true")
    
    status = get_db_gate_status()
    assert status["gate_locked"] is False
    assert status["readonly_connection_ok"] is True
    assert status["production_db_basename"] == "prod_fake.db"
    assert "positions" in status["detected_known_legacy_tables"]
    assert status["detected_tables_count"] == 2
    assert str(tmp_path) not in status.get("production_db_basename") # basename shouldn't have full path

def test_safety_matrix_unsafe_on_bad_db_path(monkeypatch):
    # Simulate DB_PATH set to something dangerous without gate being locked securely
    monkeypatch.setenv("ALLOW_PRODUCTION_DB", "true")
    monkeypatch.setenv("DB_PATH", "dangerous_prod.db")
    
    with TestClient(app) as client:
        response = client.get("/api/system/safety-matrix")
        assert response.status_code == 200
        data = response.json()
        assert data["safety_state"] == "UNSAFE"
        
def test_safety_matrix_unsafe_on_gate_write_mode_attempt(monkeypatch):
    monkeypatch.setenv("ALLOW_PRODUCTION_DB", "true")
    monkeypatch.setenv("DB_PATH", "tasi_ledger_test.db")
    monkeypatch.setenv("ENABLE_PRODUCTION_DB_READONLY_GATE", "true")
    monkeypatch.setenv("PRODUCTION_DB_READONLY_REQUIRED", "false")
    monkeypatch.setenv("PRODUCTION_DB_PATH", "dummy.db")
    
    with TestClient(app) as client:
        response = client.get("/api/system/safety-matrix")
        assert response.status_code == 200
        data = response.json()
        assert data["safety_state"] == "UNSAFE"

def test_db_gate_endpoint_no_leak(monkeypatch):
    monkeypatch.setenv("ALLOW_PRODUCTION_DB", "true")
    monkeypatch.setenv("ENABLE_PRODUCTION_DB_READONLY_GATE", "true")
    monkeypatch.setenv("PRODUCTION_DB_PATH", "/secret/folder/path/prod.db")
    monkeypatch.setenv("PRODUCTION_DB_READONLY_REQUIRED", "true")
    
    with TestClient(app) as client:
        response = client.get("/api/system/db-gate-status")
        assert response.status_code == 200
        data = response.json()
        assert data["production_db_basename"] == "prod.db"
        assert "/secret/folder/path" not in response.text

