"""
SQLite persistence for DeskFlow.
Stores the conversation audit trail and tickets so state survives restarts.
"""

import json
import os
import sqlite3
import threading
from datetime import datetime, timezone

DB_PATH = os.getenv("DESKFLOW_DB", "deskflow.db")
_lock = threading.Lock()
_initialized = False


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables if they do not exist."""
    global _initialized
    with _lock, _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                session_id TEXT NOT NULL,
                employee_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                tool_calls TEXT
            );
            CREATE TABLE IF NOT EXISTS tickets (
                ticket_id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_messages_session
                ON messages(session_id, id);
            """
        )
    _initialized = True


def _ensure() -> None:
    if not _initialized:
        init_db()


def log_message(
    session_id: str,
    employee_id: str,
    role: str,
    content: str,
    tool_calls: list | None = None,
) -> None:
    """Append one chat/audit row."""
    _ensure()
    row = (
        datetime.now(timezone.utc).isoformat(),
        session_id,
        employee_id,
        role,
        content,
        json.dumps(tool_calls, default=str) if tool_calls else None,
    )
    with _lock, _connect() as conn:
        conn.execute(
            "INSERT INTO messages (ts, session_id, employee_id, role, content, tool_calls)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            row,
        )


def get_session_history(session_id: str, employee_id: str, limit: int = 20) -> list[dict]:
    """Restore user/assistant turns for a session after a restart."""
    _ensure()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT role, content FROM messages"
            " WHERE session_id = ? AND employee_id = ? AND role IN ('user', 'assistant')"
            " ORDER BY id DESC LIMIT ?",
            (session_id, employee_id, limit),
        ).fetchall()
    return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]


def get_audit(
    session_id: str | None = None,
    employee_id: str | None = None,
    limit: int = 100,
) -> list[dict]:
    """Return recent audit rows, optionally filtered."""
    _ensure()
    query = "SELECT ts, session_id, employee_id, role, content, tool_calls FROM messages"
    params: list = []
    clauses = []
    if session_id:
        clauses.append("session_id = ?")
        params.append(session_id)
    if employee_id:
        clauses.append("employee_id = ?")
        params.append(employee_id)
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    with _connect() as conn:
        rows = conn.execute(query, params).fetchall()

    out = []
    for r in rows:
        item = dict(r)
        if item["tool_calls"]:
            try:
                item["tool_calls"] = json.loads(item["tool_calls"])
            except json.JSONDecodeError:
                item["tool_calls"] = None
        out.append(item)
    return out


def save_ticket(ticket: dict) -> None:
    """Upsert one ticket record."""
    _ensure()
    ticket_id = ticket.get("ticket_id")
    if not ticket_id:
        return
    with _lock, _connect() as conn:
        conn.execute(
            "INSERT INTO tickets (ticket_id, data, updated_at) VALUES (?, ?, ?)"
            " ON CONFLICT(ticket_id) DO UPDATE SET data = excluded.data,"
            " updated_at = excluded.updated_at",
            (
                ticket_id,
                json.dumps(ticket, default=str),
                datetime.now(timezone.utc).isoformat(),
            ),
        )


def load_tickets() -> dict[str, dict]:
    """Load all persisted tickets (keyed by ticket_id)."""
    _ensure()
    with _connect() as conn:
        rows = conn.execute("SELECT data FROM tickets").fetchall()
    tickets = {}
    for r in rows:
        try:
            data = json.loads(r["data"])
            tickets[data["ticket_id"]] = data
        except (json.JSONDecodeError, KeyError):
            continue
    return tickets


def tool_call_stats() -> dict[str, int]:
    """Count persisted tool calls by tool name."""
    _ensure()
    with _connect() as conn:
        rows = conn.execute("SELECT content FROM messages WHERE role = 'tool'").fetchall()
    stats: dict[str, int] = {}
    for r in rows:
        name = (r["content"] or "").split("(", 1)[0] or "unknown"
        stats[name] = stats.get(name, 0) + 1
    return stats


def recent_tool_calls(limit: int = 20) -> list[dict]:
    """Most recent tool-call rows (for admin views)."""
    _ensure()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT ts, employee_id, content, tool_calls FROM messages"
            " WHERE role = 'tool' ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    out = []
    for r in rows:
        item = dict(r)
        if item["tool_calls"]:
            try:
                item["tool_calls"] = json.loads(item["tool_calls"])
            except json.JSONDecodeError:
                item["tool_calls"] = None
        out.append(item)
    return out
