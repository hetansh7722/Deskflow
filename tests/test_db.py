import db


def test_log_and_read_audit_trail():
    db.log_message("sess-db-1", "EMP001", "user", "hello world")
    db.log_message("sess-db-1", "EMP001", "assistant", "hi there")
    entries = db.get_audit(session_id="sess-db-1", limit=10)
    roles = [e["role"] for e in entries]
    assert "user" in roles and "assistant" in roles
    assert entries[0]["ts"]


def test_audit_filters_by_employee():
    db.log_message("sess-db-2", "EMP001", "user", "mine")
    db.log_message("sess-db-2", "EMP002", "user", "theirs")
    mine = db.get_audit(session_id="sess-db-2", employee_id="EMP001")
    assert all(e["employee_id"] == "EMP001" for e in mine)
    assert any(e["content"] == "mine" for e in mine)


def test_session_history_restores_in_order_and_ignores_tool_rows():
    db.log_message("sess-db-3", "EMP001", "user", "first")
    db.log_message("sess-db-3", "EMP001", "tool", "create_ticket({})",
                   tool_calls=[{"tool": "create_ticket", "arguments": {}, "result": {}}])
    db.log_message("sess-db-3", "EMP001", "assistant", "second")
    history = db.get_session_history("sess-db-3", "EMP001")
    assert [m["role"] for m in history] == ["user", "assistant"]
    assert [m["content"] for m in history] == ["first", "second"]


def test_ticket_save_and_load_roundtrip():
    ticket = {"ticket_id": "TKT-TEST-1", "status": "open", "priority": "high"}
    db.save_ticket(ticket)
    loaded = db.load_tickets()
    assert loaded["TKT-TEST-1"]["status"] == "open"


def test_ticket_upsert_overwrites():
    db.save_ticket({"ticket_id": "TKT-TEST-2", "status": "open"})
    db.save_ticket({"ticket_id": "TKT-TEST-2", "status": "closed"})
    assert db.load_tickets()["TKT-TEST-2"]["status"] == "closed"


def test_tool_call_stats_counts_by_tool():
    db.log_message("api", "EMP001", "tool", "get_user_profile({})",
                   tool_calls=[{"tool": "get_user_profile", "arguments": {}, "result": {}}])
    stats = db.tool_call_stats()
    assert "get_user_profile" in stats
    assert stats["get_user_profile"] >= 1


def test_recent_tool_calls_returns_latest_first():
    db.log_message("api", "EMP001", "tool", "reset_password({})",
                   tool_calls=[{"tool": "reset_password", "arguments": {}, "result": {}}])
    rows = db.recent_tool_calls(limit=5)
    assert rows and rows[0]["content"].startswith("reset_password")
