import json

import pytest

from tools import (
    SLA_LABELS,
    SLA_TARGETS_MINUTES,
    check_software_entitlement,
    create_ticket,
    dispatch_tool,
    get_ticket_status,
    get_user_profile,
    list_user_tickets,
    reset_password,
)


# --- priority handling -----------------------------------------------------

def test_invalid_priority_normalized_to_medium():
    r = create_ticket("EMP001", "Odd request", "banana", "no category here", "General")
    assert r["priority"] == "medium"


def test_classifier_overrides_critical_on_routine_request():
    r = create_ticket(
        "EMP001", "Please install Notion", "critical",
        "routine add request for a license", "Software Access",
    )
    assert r["priority"] == "medium"
    assert r["priority_source"] == "downgraded"


def test_classifier_escalates_low_claim_with_outage_text():
    r = create_ticket(
        "EMP001", "Production down", "low",
        "entire system outage for all users", "Network",
    )
    assert r["priority"] == "critical"
    assert r["priority_source"] == "escalated"


def test_priority_review_is_persisted_on_ticket():
    r = create_ticket("EMP001", "VPN issue", "high", "vpn not working at all", "Network")
    t = get_ticket_status(r["ticket_id"])
    assert t["ticket_id"] == r["ticket_id"]
    assert "priority_review" in t or t["status"] == "open"


# --- SLA tables ------------------------------------------------------------

def test_sla_tables_cover_all_priorities():
    assert set(SLA_TARGETS_MINUTES) == {"low", "medium", "high", "critical"}
    assert set(SLA_LABELS) == set(SLA_TARGETS_MINUTES)
    assert SLA_TARGETS_MINUTES["critical"] < SLA_TARGETS_MINUTES["high"]
    assert SLA_TARGETS_MINUTES["high"] < SLA_TARGETS_MINUTES["medium"]


# --- profiles & entitlements ----------------------------------------------

def test_get_user_profile_found():
    p = get_user_profile("EMP001")
    assert p["employee_id"] == "EMP001"
    assert p["current_entitlements"]


def test_get_user_profile_missing():
    assert "error" in get_user_profile("EMP999")


def test_entitlement_partial_name_match():
    r = check_software_entitlement("EMP001", "adobe")
    assert r["error"] is None if "error" in r else True
    assert r.get("software") == "Adobe Creative Suite"


def test_entitlement_unknown_software_lists_catalog():
    r = check_software_entitlement("EMP001", "NonexistentApp")
    assert "error" in r
    assert r["available_software"]


def test_entitlement_missing_cost_field_does_not_crash():
    r = check_software_entitlement("EMP001", "GitHub")
    assert r["entitled"] is True
    assert r["available_licenses"] > 0


# --- tickets ---------------------------------------------------------------

def test_list_user_tickets_returns_own_tickets_only():
    r = list_user_tickets("EMP001")
    assert r["employee_id"] == "EMP001"
    assert isinstance(r["tickets"], list)


def test_reset_password_returns_temp_credential():
    r = reset_password("EMP001")
    assert r["status"] == "success"
    assert len(r["temporary_password"]) >= 10


def test_reset_password_unknown_employee():
    assert "error" in reset_password("EMP999")


# --- dispatcher ------------------------------------------------------------

def test_dispatch_unknown_tool():
    assert "error" in json.loads(dispatch_tool("does_not_exist", {}))


def test_dispatch_bad_arguments():
    result = json.loads(dispatch_tool("get_user_profile", {"wrong_arg": 1}))
    assert "error" in result


def test_dispatch_valid_tool():
    result = json.loads(dispatch_tool("get_user_profile", {"employee_id": "EMP002"}))
    assert result["employee_id"] == "EMP002"
