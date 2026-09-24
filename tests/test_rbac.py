import pytest
from fastapi.testclient import TestClient

import auth
from main import app
from mock_data import TICKETS

client = TestClient(app)


def _login(employee_id: str) -> dict:
    r = client.post("/login", json={"employee_id": employee_id, "password": auth.DEMO_PASSWORD})
    assert r.status_code == 200, r.text
    # drop the session cookie so identity comes only from the Bearer header
    # (the cookie would otherwise leak the last-logged-in user into later tests)
    client.cookies.clear()
    return {"Authorization": f"Bearer {r.json()['token']}"}


EMP_H = _login("EMP001")       # Software Engineer — regular employee
ADMIN_H = _login("EMP009")     # System Administrator — admin


# --- role flags -------------------------------------------------------------

def test_is_admin_by_role():
    assert auth.is_admin("EMP009") is True      # System Administrator
    assert auth.is_admin("EMP014") is True      # IT Operations Manager
    assert auth.is_admin("EMP001") is False
    assert auth.is_admin("EMP999") is False


def test_me_exposes_is_admin():
    assert client.get("/me", headers=EMP_H).json()["is_admin"] is False
    assert client.get("/me", headers=ADMIN_H).json()["is_admin"] is True


# --- admin endpoints --------------------------------------------------------

@pytest.mark.parametrize("path", ["/stats", "/tickets", "/employees", "/static/admin.html"])
def test_admin_endpoints_forbidden_for_employee(path):
    assert client.get(path, headers=EMP_H).status_code == 403


@pytest.mark.parametrize("path", ["/stats", "/tickets", "/employees", "/static/admin.html"])
def test_admin_endpoints_allowed_for_admin(path):
    assert client.get(path, headers=ADMIN_H).status_code == 200


@pytest.mark.parametrize("path", ["/stats", "/tickets", "/static/admin.html"])
def test_admin_endpoints_unauthenticated_401(path):
    assert client.get(path).status_code == 401


# --- audit scoping ----------------------------------------------------------

def test_employee_audit_scoped_to_self():
    # generate an EMP001 audit row first (tool calls are logged per session)
    client.post("/tools/get_user_profile", headers=EMP_H, json={"arguments": {"employee_id": "EMP001"}})
    r = client.get("/audit?limit=500", headers=EMP_H)
    assert r.status_code == 200
    entries = r.json()["entries"]
    assert entries, "expected at least one own audit entry"
    assert all(e["employee_id"] == "EMP001" for e in entries)


def test_employee_cannot_query_other_employee_audit():
    r = client.get("/audit?employee_id=EMP002", headers=EMP_H)
    assert r.status_code == 403


def test_admin_can_query_any_employee_audit():
    r = client.get("/audit?employee_id=EMP002", headers=ADMIN_H)
    assert r.status_code == 200


# --- ticket updates: session identity + admin bypass ------------------------

def _create_ticket() -> str:
    r = client.post(
        "/tools/create_ticket",
        headers=EMP_H,
        json={"arguments": {
            "employee_id": "EMP001", "title": "RBAC test ticket",
            "priority": "low", "description": "testing lifecycle guard",
        }},
    )
    assert r.status_code == 200
    return r.json()["result"]["ticket_id"]


def test_employee_resolves_own_ticket():
    tid = _create_ticket()
    r = client.post("/tools/update_ticket_status", headers=EMP_H, json={"arguments": {
        "ticket_id": tid, "status": "resolved", "resolution": "fixed",
    }})
    assert r.status_code == 200
    assert r.json()["result"]["status"] == "resolved"
    assert TICKETS[tid]["status"] == "resolved"


def test_employee_cannot_resolve_someone_elses_ticket():
    tid = "TKT-1029"  # belongs to EMP020
    r = client.post("/tools/update_ticket_status", headers=EMP_H, json={"arguments": {
        "ticket_id": tid, "employee_id": "EMP020", "status": "resolved",
        "resolution": "spoof attempt",
    }})
    assert r.status_code == 200
    assert "error" in r.json()["result"]
    assert TICKETS[tid]["status"] == "open", "spoofed update must not apply"


def test_session_identity_overrides_body_employee_id():
    # body claims EMP020 owns it; session is EMP001 -> must still be rejected
    tid = _create_ticket()
    r = client.post("/tools/update_ticket_status", headers=EMP_H, json={"arguments": {
        "ticket_id": tid, "employee_id": "EMP002", "status": "closed",
        "resolution": "nope",
    }})
    # session identity (EMP001) is the owner, so this one IS allowed
    assert "error" not in r.json()["result"]
    # and the opposite: EMP001 cannot resolve EMP020's ticket even naming EMP020
    r = client.post("/tools/update_ticket_status", headers=EMP_H, json={"arguments": {
        "ticket_id": "TKT-1029", "employee_id": "EMP020", "status": "closed",
        "resolution": "nope",
    }})
    assert "error" in r.json()["result"]
    assert TICKETS["TKT-1029"]["status"] == "open"


def test_admin_can_resolve_any_ticket():
    tid = "TKT-1029"  # belongs to EMP020
    original = TICKETS[tid]["status"]
    r = client.post("/tools/update_ticket_status", headers=ADMIN_H, json={"arguments": {
        "ticket_id": tid, "status": "resolved", "resolution": "replaced under warranty",
    }})
    assert r.status_code == 200
    assert r.json()["result"]["status"] == "resolved"
    assert TICKETS[tid]["status"] == "resolved"
    TICKETS[tid]["status"] = original  # restore for other tests
