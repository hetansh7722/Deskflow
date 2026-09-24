from datetime import datetime, timedelta

import monitors
from mock_data import TICKETS


def _put(ticket):
    TICKETS[ticket["ticket_id"]] = ticket
    return ticket


def _clean(ticket_id):
    TICKETS.pop(ticket_id, None)


def test_old_open_ticket_is_flagged_as_breached():
    tid = "TKT-SLA-TEST"
    _put({
        "ticket_id": tid, "status": "open", "priority": "high",
        "title": "test", "created_at": (datetime.now() - timedelta(hours=5)).isoformat(),
        "updated_at": datetime.now().isoformat(),
    })
    try:
        breached = monitors.check_sla_breaches()
        assert any(t["ticket_id"] == tid for t in breached)
        assert TICKETS[tid]["sla_breached"] is True
        assert TICKETS[tid]["status"] == "open"  # flag only, never closed

        again = monitors.check_sla_breaches()
        assert all(t["ticket_id"] != tid for t in again)  # no duplicate flagging
    finally:
        _clean(tid)


def test_new_ticket_within_sla_is_not_flagged():
    tid = "TKT-SLA-NEW"
    _put({
        "ticket_id": tid, "status": "open", "priority": "critical",
        "title": "test", "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    })
    try:
        assert all(t["ticket_id"] != tid for t in monitors.check_sla_breaches())
        assert "sla_breached" not in TICKETS[tid]
    finally:
        _clean(tid)


def test_resolved_ticket_never_flagged():
    tid = "TKT-SLA-RESOLVED"
    _put({
        "ticket_id": tid, "status": "resolved", "priority": "high",
        "title": "test", "created_at": (datetime.now() - timedelta(days=30)).isoformat(),
        "updated_at": (datetime.now() - timedelta(days=30)).isoformat(),
    })
    try:
        breached = monitors.check_sla_breaches()
        stale = monitors.check_stale_tickets()
        assert all(t["ticket_id"] != tid for t in breached + stale)
    finally:
        _clean(tid)


def test_stale_ticket_flagged_but_not_closed():
    tid = "TKT-STALE-TEST"
    old = (datetime.now() - timedelta(days=monitors.STALE_AFTER_DAYS + 2)).isoformat()
    _put({
        "ticket_id": tid, "status": "open", "priority": "medium",
        "title": "test", "created_at": old, "updated_at": old,
    })
    try:
        stale = monitors.check_stale_tickets()
        assert any(t["ticket_id"] == tid for t in stale)
        assert TICKETS[tid]["stale"] is True
        assert TICKETS[tid]["status"] == "open"  # flag only

        again = monitors.check_stale_tickets()
        assert all(t["ticket_id"] != tid for t in again)
    finally:
        _clean(tid)
