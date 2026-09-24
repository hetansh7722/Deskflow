import json

from tools import (
    check_device_compliance,
    check_vpn_status,
    create_ticket,
    dispatch_tool,
    get_user_devices,
    get_ticket_status,
    update_ticket_status,
)


# --- device inventory ------------------------------------------------------

def test_get_user_devices_lists_assigned_endpoints():
    r = get_user_devices("EMP001")
    assert r["device_count"] >= 1
    ids = [d["device_id"] for d in r["devices"]]
    assert "LAP-1001" in ids
    assert all("os" in d and "managed_by" in d for d in r["devices"])


def test_get_user_devices_unknown_employee():
    r = get_user_devices("EMP999")
    assert "error" in r


# --- device compliance -----------------------------------------------------

def test_compliance_flags_unencrypted_laptop():
    r = check_device_compliance("EMP001")
    assert r["all_compliant"] is False
    laptop = next(d for d in r["devices"] if d["device_id"] == "LAP-1001")
    assert laptop["compliant"] is False
    issues = [f["issue"] for f in laptop["findings"]]
    assert any("encryption" in i.lower() for i in issues)
    assert all("remediation" in f for f in laptop["findings"])


def test_compliance_single_device_filter():
    r = check_device_compliance("EMP001", device_id="LAP-1001")
    assert r["devices_checked"] == 1
    assert r["devices"][0]["device_id"] == "LAP-1001"


def test_compliance_unknown_device_lists_assigned():
    r = check_device_compliance("EMP001", device_id="NOPE")
    assert "error" in r
    assert "LAP-1001" in r["assigned_devices"]


def test_compliance_shape_for_every_employee():
    from mock_data import USERS

    for uid in USERS:
        r = check_device_compliance(uid)
        assert r["all_compliant"] in (True, False)
        assert all("compliant" in d and "findings" in d for d in r["devices"])


# --- VPN diagnostics -------------------------------------------------------

def test_vpn_reports_gateway_and_session():
    r = check_vpn_status("EMP001")
    assert r["gateway"]["status"] == "operational"
    assert "connected" in r["session"]
    assert r["issues"] and r["recommended_actions"]


def test_vpn_disconnected_outdated_client_detected():
    r = check_vpn_status("EMP001")
    joined = " ".join(r["issues"]).lower()
    assert "not connected" in joined
    assert "outdated" in joined


def test_vpn_healthy_session_has_no_issues():
    r = check_vpn_status("EMP002")  # connected + current client version
    assert r["issues"] == []
    assert r["recommended_actions"] == ["Connection healthy — no action needed"]


def test_vpn_unknown_employee():
    assert "error" in check_vpn_status("EMP999")


# --- ticket lifecycle ------------------------------------------------------

def test_update_ticket_status_requires_resolution_to_resolve():
    t = create_ticket("EMP001", "VPN drops", "medium", "vpn disconnects hourly", "Network")
    r = update_ticket_status(t["ticket_id"], "EMP001", "resolved")
    assert "error" in r
    assert "resolution" in r["error"]


def test_update_ticket_status_wrong_owner_rejected():
    t = create_ticket("EMP001", "VPN drops", "medium", "vpn disconnects hourly", "Network")
    r = update_ticket_status(t["ticket_id"], "EMP002", "resolved", resolution="done")
    assert "error" in r
    assert "own tickets" in r["error"]


def test_update_ticket_status_invalid_status_rejected():
    t = create_ticket("EMP001", "VPN drops", "medium", "vpn disconnects hourly", "Network")
    r = update_ticket_status(t["ticket_id"], "EMP001", "archived")
    assert "error" in r
    assert "in_progress" in r["valid_statuses"]


def test_update_ticket_status_resolves_and_persists():
    t = create_ticket("EMP001", "VPN drops", "medium", "vpn disconnects hourly", "Network")
    r = update_ticket_status(t["ticket_id"], "EMP001", "in_progress")
    assert r["status"] == "in_progress"
    assert r["previous_status"] == "open"

    r = update_ticket_status(
        t["ticket_id"], "EMP001", "resolved",
        resolution="Replaced split-tunnel config on gw-ap-mum-01",
    )
    assert r["status"] == "resolved"

    saved = get_ticket_status(t["ticket_id"])
    assert saved["status"] == "resolved"
    assert saved["resolution"] == "Replaced split-tunnel config on gw-ap-mum-01"


def test_resolved_ticket_exits_stale_monitor():
    from monitors import check_stale_tickets, STALE_AFTER_DAYS
    from datetime import datetime, timedelta

    t = create_ticket("EMP001", "Old issue", "low", "something quiet", "General")
    update_ticket_status(
        t["ticket_id"], "EMP001", "resolved", resolution="fixed long ago",
    )
    # backdate so it would be stale if still open
    ticket = __import__("mock_data").TICKETS[t["ticket_id"]]
    ticket["created_at"] = (datetime.now() - timedelta(days=STALE_AFTER_DAYS + 5)).isoformat()
    ticket["updated_at"] = ticket["created_at"]
    assert check_stale_tickets() == [] or t["ticket_id"] not in [
        x["ticket_id"] for x in check_stale_tickets()
    ]


# --- dispatcher ------------------------------------------------------------

def test_all_new_tools_dispatchable_via_json():
    for name, args in [
        ("get_user_devices", {"employee_id": "EMP001"}),
        ("check_device_compliance", {"employee_id": "EMP001"}),
        ("check_vpn_status", {"employee_id": "EMP001"}),
        ("update_ticket_status", {"ticket_id": "TKT-9999", "employee_id": "EMP001", "status": "resolved", "resolution": "n/a"}),
    ]:
        out = json.loads(dispatch_tool(name, args))
        assert isinstance(out, dict)
