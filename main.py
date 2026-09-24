"""
Main FastAPI server for DeskFlow.
Handles chat requests and demo APIs.
"""

import json
from collections import Counter
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from dotenv import load_dotenv
from fastapi import Cookie, Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# load .env before app modules read configuration
load_dotenv()

import auth
import db
import logger
import monitors
from llm import run_agent, MODEL
from mock_data import TICKETS, USERS
from tools import TOOL_NAMES, dispatch_tool


def get_current_employee(
    request: Request,
    df_token: str | None = Cookie(default=None),
) -> str:
    """Resolve the authenticated employee from cookie or Bearer token."""
    token = df_token
    if not token:
        header = request.headers.get("Authorization", "")
        if header.startswith("Bearer "):
            token = header[7:]
    employee_id = auth.verify_token(token)
    if not employee_id:
        raise HTTPException(status_code=401, detail="Not authenticated. Please sign in.")
    return employee_id


def get_current_admin(employee_id: str = Depends(get_current_employee)) -> str:
    """Admin-only gate: 403 for regular employees."""
    if not auth.is_admin(employee_id):
        raise HTTPException(
            status_code=403,
            detail="Admin access required. Ask IT to grant your account an admin role.",
        )
    return employee_id


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    persisted = db.load_tickets()
    TICKETS.update(persisted)
    logger.log(f"[db] Restored {len(persisted)} persisted ticket(s) from {db.DB_PATH}")

    import asyncio
    monitor_task = asyncio.create_task(monitors.monitor_loop())
    yield
    monitor_task.cancel()


app = FastAPI(
    title="DeskFlow — AI IT Helpdesk",
    description="AI-powered IT helpdesk assistant demo",
    version="1.0.0",
    lifespan=lifespan,
)

# Admin dashboard: gated before the /static mount so it is admin-only
@app.get("/static/admin.html", include_in_schema=False)
async def serve_admin(admin: str = Depends(get_current_admin)):
    ui_path = Path("static/admin.html")
    if not ui_path.exists():
        raise HTTPException(status_code=404, detail="Frontend not found.")
    return FileResponse(ui_path)


# Serve frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

# stores chat history for each session
_sessions: dict[str, list[dict]] = {}


# Request/response models

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class LoginRequest(BaseModel):
    employee_id: str
    password: str


class ChatResponse(BaseModel):
    response: str
    session_id: str
    employee_id: str
    trace: list


# API routes

@app.get("/", include_in_schema=False)
async def serve_ui():
    ui_path = Path("static/index.html")
    if not ui_path.exists():
        raise HTTPException(status_code=404, detail="Frontend not found.")
    return FileResponse(ui_path)


@app.post("/login")
async def login(req: LoginRequest, response: Response):
    """Sign in with employee ID + password; sets an httpOnly session cookie."""
    user = auth.authenticate(req.employee_id, req.password)
    if not user:
        logger.log(f"[/login] Failed sign-in for {req.employee_id!r}", level="warning")
        raise HTTPException(status_code=401, detail="Invalid employee ID or password.")
    token = auth.create_token(user["employee_id"])
    response.set_cookie(
        "df_token",
        token,
        httponly=True,
        samesite="lax",
        max_age=auth.TOKEN_TTL_SECONDS,
    )
    logger.log(f"[/login] {user['employee_id']} signed in")
    return {
        "employee_id": user["employee_id"],
        "name": user["name"],
        "department": user["department"],
        "token": token,
    }


@app.post("/logout")
async def logout(response: Response):
    response.delete_cookie("df_token")
    return {"status": "signed out"}


@app.get("/me")
async def me(
    request: Request,
    df_token: str | None = Cookie(default=None),
):
    """Who am I? Returns authenticated=False instead of 401 so the UI can decide."""
    token = df_token
    if not token:
        header = request.headers.get("Authorization", "")
        if header.startswith("Bearer "):
            token = header[7:]
    employee_id = auth.verify_token(token)
    if not employee_id:
        return {"authenticated": False}
    user = USERS[employee_id]
    return {
        "authenticated": True,
        "employee_id": employee_id,
        "name": user["name"],
        "department": user["department"],
        "role": user["role"],
        "is_admin": auth.is_admin(employee_id),
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, employee_id: str = Depends(get_current_employee)):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    logger.log(
        f"[/chat] session={req.session_id} employee={employee_id} "
        f"msg={req.message[:80]!r}"
    )

    history = _sessions.get(req.session_id)
    if history is None:
        history = db.get_session_history(req.session_id, employee_id, limit=20)
        _sessions[req.session_id] = history
        if history:
            logger.log(
                f"[/chat] Restored {len(history)} message(s) for session={req.session_id}"
            )

    try:
        result = run_agent(
            user_message=req.message,
            conversation_history=history,
            employee_id=employee_id,
        )
    except RuntimeError as e:
        # Missing API key or similar config error
        logger.log(f"[/chat] Config error: {e}", level="error")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.log(f"[/chat] Unexpected error: {e}", level="error")
        if "429" in str(e) or "rate limit" in str(e).lower():
            raise HTTPException(
                status_code=429,
                detail="DeskFlow is busy right now. Please wait 30 seconds and try again.",
            )
        raise HTTPException(
            status_code=500,
            detail="DeskFlow encountered an internal error. Please try again.",
        )

    # keep recent messages only in session history to limit memory usage
    history.append({"role": "user", "content": req.message})
    history.append({"role": "assistant", "content": result["response"]})
    if len(history) > 20:
        _sessions[req.session_id] = history[-20:]

    # persist audit trail (survives restart)
    db.log_message(req.session_id, employee_id, "user", req.message)
    db.log_message(req.session_id, employee_id, "assistant", result["response"])
    for step in result.get("trace", []):
        for tc in step.get("tool_calls", []):
            db.log_message(
                req.session_id,
                employee_id,
                "tool",
                f"{tc.get('tool')}({json.dumps(tc.get('arguments', {}), default=str)})",
                tool_calls=[tc],
            )

    return ChatResponse(
        response=result["response"],
        session_id=req.session_id,
        employee_id=employee_id,
        trace=result["trace"],
    )


@app.get("/trace")
async def get_trace(employee_id: str = Depends(get_current_employee)):
    """Returns execution logs."""
    return JSONResponse({"logs": logger.get_logs()})


@app.get("/audit")
async def get_audit(
    session_id: str | None = None,
    employee_id: str | None = None,
    limit: int = 100,
    current: str = Depends(get_current_employee),
):
    """Persistent conversation + tool-call trail (SQLite).
    Admins may view anyone; regular employees only see their own entries."""
    limit = max(1, min(limit, 500))
    if not auth.is_admin(current):
        if employee_id and employee_id.upper() != current.upper():
            raise HTTPException(
                status_code=403,
                detail="Admin access required to view another employee's audit trail.",
            )
        employee_id = current
    return JSONResponse(
        {"entries": db.get_audit(session_id=session_id, employee_id=employee_id, limit=limit)}
    )


class ToolRequest(BaseModel):
    arguments: dict = {}


@app.post("/tools/{tool_name}")
async def run_tool(
    tool_name: str,
    req: ToolRequest,
    current: str = Depends(get_current_employee),
):
    """Authenticated automation API — the surface PowerShell/CI scripts call."""
    if tool_name not in TOOL_NAMES:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown tool '{tool_name}'. Available: {', '.join(TOOL_NAMES)}",
        )
    args_json = json.dumps(req.arguments, default=str)
    # session identity wins: never trust a caller-supplied employee_id
    # for ticket updates (spoof-proof ownership / admin checks).
    if tool_name == "update_ticket_status":
        req.arguments["employee_id"] = current
    result_str = dispatch_tool(tool_name, req.arguments)
    try:
        result = json.loads(result_str)
    except json.JSONDecodeError:
        result = {"raw": result_str}

    db.log_message(
        "api",
        current,
        "tool",
        f"{tool_name}({args_json})",
        tool_calls=[{"tool": tool_name, "arguments": req.arguments, "result": result}],
    )
    logger.log(f"[/tools] {current} -> {tool_name}({args_json})")
    return JSONResponse({"tool": tool_name, "result": result})


@app.get("/tickets")
async def list_tickets(current: str = Depends(get_current_admin)):
    """All tickets (admin/automation view) — newest first."""
    tickets = sorted(TICKETS.values(), key=lambda t: t.get("ticket_id", ""), reverse=True)
    return {"count": len(tickets), "tickets": tickets}


@app.get("/stats")
async def stats(current: str = Depends(get_current_admin)):
    """Aggregates for the admin dashboard."""
    all_tickets = list(TICKETS.values())
    open_tickets = [
        t for t in all_tickets if t.get("status") not in ("closed", "resolved")
    ]
    breaches = [
        {
            "ticket_id": t["ticket_id"],
            "priority": t.get("priority"),
            "title": t.get("title"),
            "assigned_to": t.get("assigned_to"),
            "created_at": t.get("created_at"),
        }
        for t in open_tickets
        if t.get("sla_breached")
    ]
    stale = [
        {
            "ticket_id": t["ticket_id"],
            "status": t.get("status"),
            "title": t.get("title"),
            "updated_at": t.get("updated_at"),
        }
        for t in open_tickets
        if t.get("stale")
    ]
    return {
        "model": MODEL,
        "totals": {
            "tickets": len(all_tickets),
            "open": len(open_tickets),
            "sla_breached": len(breaches),
            "stale": len(stale),
            "employees": len(USERS),
        },
        "by_priority": dict(Counter(t.get("priority", "medium") for t in open_tickets)),
        "by_category": dict(Counter(t.get("category", "General") for t in open_tickets)),
        "by_status": dict(Counter(t.get("status", "unknown") for t in all_tickets)),
        "sla_breaches": breaches,
        "stale_tickets": stale,
        "tool_calls": db.tool_call_stats(),
        "recent_tool_calls": db.recent_tool_calls(15),
    }


@app.get("/employees")
async def list_employees(current: str = Depends(get_current_admin)):
    """Helper endpoint for admin views and automation scripts."""
    return {
        "employees": [
            {
                "employee_id": uid,
                "name": u["name"],
                "department": u["department"],
                "role": u["role"],
            }
            for uid, u in USERS.items()
        ]
    }


@app.delete("/session/{session_id}")
async def clear_session(session_id: str, current: str = Depends(get_current_employee)):
    _sessions.pop(session_id, None)
    logger.log(f"[/session] Cleared session: {session_id}")
    return {"status": "cleared", "session_id": session_id}


@app.get("/health")
async def health():
    return {"status": "ok", "model": MODEL}


# Run server

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
