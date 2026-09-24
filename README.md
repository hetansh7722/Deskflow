<h1 align="center">DeskFlow AI-Powered IT Helpdesk Assistant</h1>

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-LLaMA%203.1-F55036?style=flat-square&logo=groq&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

DeskFlow is an agentic AI-powered IT helpdesk assistant. It uses an LLM tool-calling workflow to query internal IT systems, perform actions such as entitlement checks and ticket creation, and return actionable responses without hardcoded intent classification.

---

## Features

- **Agentic tool-calling loop** — the LLM decides which tools to call and when, natively handling multi-step conditional requests (e.g. *"request Adobe if I'm not entitled"*).
- **10 IT tools** — user profile, software-entitlement check, ticket create / status / list / lifecycle update, password reset, device inventory, device compliance, and VPN diagnostics.
- **Endpoint & network diagnostics** — device inventory, compliance checks (encryption / patching / AV / MDM check-in), and VPN gateway + session troubleshooting, so chat answers are backed by live mock-IT data.
- **Employee login & session tokens** — PBKDF2 password hashing + HMAC-signed tokens; identity comes from the token, so nobody can impersonate another employee. **Role-based admin gate**: `/stats`, `/tickets`, `/employees`, and the dashboard are admin-only (System Administrator / IT Operations Manager / CTO); audit trail is scoped to your own records unless you're an admin.
- **Persistent audit trail** — chat turns and tool calls are stored in SQLite and survive restarts (`GET /audit`); tickets reload on startup.
- **Priority classifier gate** — an independent keyword ruleset reviews the LLM's priority before a ticket is created (escalates / downgrades with an auditable reason).
- **SLA breach checker + stale sweep** — background monitors flag tickets past their SLA window or idle for 7+ days and send one batched alert (flag-only: status is never changed automatically).
- **Pluggable alert channels** — one `Notifier` fans alerts out to Discord, SMTP email, and the log; each channel activates only when its env vars are set.
- **Admin dashboard** — `/static/admin.html` (admin-only) shows open tickets by priority/category/status, SLA breaches, stale tickets, persisted tool-call activity, and **ticket actions** — change status or resolve any ticket with a required resolution note.
- **PowerShell admin scripts** — password reset, bulk entitlement report (CSV), ticket export (CSV), and service health checks against the REST API.
- **Automation API** — `POST /tools/{name}` lets scripts and CI drive the same tools the chat agent uses, fully audited.
- **Web chat UI** — single-file frontend with a live agent-trace panel.
- **Tests** — 61 pytest cases covering the classifier, tools, auth, persistence, monitors, device/VPN diagnostics, and ticket lifecycle.
- **Full observability** — every tool call is traced to an in-memory ring buffer and exposed at `GET /trace`.
- **Scope & privacy guardrails** — a 10-rule system prompt refuses out-of-scope (HR/payroll/general) queries and blocks access to other employees' data.
- **Resilient** — automatic rate-limit retry with exponential backoff, per-tool error handling, and capped session memory.

---

## Architecture

```
Browser (chat UI)  →  FastAPI  →  Agentic Loop (llm.py)  →  Tool Dispatcher (tools.py)  →  Mock IT Systems (mock_data.py)
                                      
                                 Groq API (LLaMA 3.1)
```

**Agentic loop:** builds messages (system prompt + history + user turn) → calls Groq with the tool schemas → if the model returns `tool_calls`, executes them, appends results, and loops (up to 10 iterations) → returns the final answer when the model stops.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | FastAPI + Uvicorn |
| **LLM** | Groq API — `openai/gpt-oss-20b` (called via `httpx`, OpenAI-compatible endpoint) |
| **Validation** | Pydantic |
| **Frontend** | Single-file HTML / CSS / JS chat UI |
| **State & logs** | In-memory sessions + a `deque` ring-buffer logger |

---

## Tools Available

| Tool | Description |
|---|---|
| `get_user_profile` | Fetch employee name, department, role, email, and current entitlements |
| `check_software_entitlement` | Check access to a specific app + approval requirement and license count |
| `create_ticket` | Open an IT ticket with title, priority, description, and category |
| `get_ticket_status` | Look up status, assignment, and resolution of a ticket |
| `list_user_tickets` | List all tickets raised by an employee |
| `update_ticket_status` | Move a ticket through its lifecycle (`in_progress` → `resolved`); resolution note required, own-tickets only |
| `get_user_devices` | List an employee's assigned endpoints (laptops/desktops) from the MDM inventory |
| `check_device_compliance` | Per-device findings: encryption, OS patching, AV signatures, MDM check-in — with remediation steps |
| `check_vpn_status` | VPN gateway health + the employee's session (connection state, client version, handshake) with troubleshooting steps |
| `reset_password` | Reset a password and issue a temporary credential |

---

## API Endpoints

| Method | Route | Purpose |
|---|---|---|
| `POST` | `/login` | Sign in with employee ID + password → session cookie + bearer token |
| `POST` | `/logout` | Clear the session cookie |
| `GET` | `/me` | Current identity (or `authenticated: false`) |
| `GET` | `/` | Serve the chat UI |
| `POST` | `/chat` | Send a message; returns the agent's response + execution trace |
| `POST` | `/tools/{name}` | Automation API — call any of the 10 tools directly (audited) |
| `GET` | `/tickets` | All tickets with SLA/stale flags (admin only) |
| `GET` | `/stats` | Aggregates for the admin dashboard (admin only) |
| `GET` | `/audit` | Persistent conversation + tool-call trail (SQLite) — own records, or any with admin |
| `GET` | `/employees` | Employee directory (admin/scripts) (admin only) |
| `DELETE` | `/session/{session_id}` | Clear a session's conversation history |
| `GET` | `/health` | Health check |

Everything except `/`, `/login`, `/logout`, `/me`, `/health` and static assets requires authentication (cookie or `Authorization: Bearer <token>`).

---

## Demo credentials

Every active employee shares one demo password (override with `DESKFLOW_DEMO_PASSWORD` in `.env`):

```
Employee ID : EMP001   Password: Deskflow@123
```

> The login screen shows no hints — this is documented here on purpose.

**Admin dashboard accounts** (see the  Admin link + `/static/admin.html`): `EMP009` (System Administrator), `EMP014` (IT Operations Manager), `EMP020` (CTO) — same demo password. Regular employees get **403** on admin endpoints.

---

## Setup

**Prerequisites:** Python 3.11+ and a free Groq API key from [console.groq.com](https://console.groq.com).

**Option A — one command (Windows):**

```powershell
.\setup.ps1        # creates venv, installs deps, prepares .env, runs tests
```

**Option B — manual:**

```bash
# 1. Create & activate a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your API key to a .env file in the project root
echo GROQ_API_KEY=your_key_here > .env

# 4. Run
python main.py
```

Open **http://localhost:8000** in your browser and sign in with the [demo credentials](#demo-credentials).

> **Dependencies:** `fastapi`, `uvicorn[standard]`, `httpx`, `python-dotenv`, `pydantic` (tests: `pytest`, see `requirements-dev.txt`).

---

## Testing

```bash
pip install -r requirements-dev.txt
pytest -q
```

61 tests across `tests/`: classifier rules, tool behaviours (incl. priority gating), auth tokens (tamper/expiry), SQLite persistence, SLA/stale monitors, device & VPN diagnostics, and ticket-lifecycle updates.

---

## PowerShell admin scripts

All scripts live in `scripts/` and talk to the authenticated REST API (`/login` → `/tools/*`).

| Script | Purpose |
|---|---|
| `Reset-DeskFlowPassword.ps1` | Reset an employee's password, print the temp credential |
| `Get-DeskFlowEntitlementReport.ps1` | Check every employee against one app → CSV |
| `Export-DeskFlowTickets.ps1` | Export all tickets incl. SLA/stale flags → CSV |
| `Get-DeskFlowHealth.ps1` | Service health + SLA summary (with `-Credential`) |

```powershell
$cred = Get-Credential    # EMP001 / Deskflow@123
.\scripts\Get-DeskFlowHealth.ps1 -Credential $cred
.\scripts\Export-DeskFlowTickets.ps1 -Credential $cred -OutFile tickets.csv
```

---

## Project Structure

```
DeskFlow/
 main.py            # FastAPI app — routes, auth gate, session management
 auth.py            # PBKDF2 password hashing + HMAC session tokens
 llm.py             # Agentic loop — Groq API call + tool execution
 tools.py           # 10 tool implementations + JSON schemas + dispatcher
 classifier.py      # Independent priority gate for ticket creation
 monitors.py        # Background SLA breach checker + stale ticket sweep
 alerts.py          # Pluggable notifier — Discord / SMTP / log channels
 db.py              # SQLite persistence — audit trail + ticket store
 mock_data.py       # In-memory users, software catalog, seed tickets
 logger.py          # In-memory ring-buffer logger (exposed at /trace)
 static/
    index.html     # Single-file chat UI (with login screen)
    admin.html     # Operations dashboard
 scripts/           # PowerShell admin/automation scripts
 tests/             # pytest suite
 setup.ps1          # One-command setup (venv + deps + tests)
 requirements.txt
 requirements-dev.txt
 .env               # GROQ_API_KEY + optional alert/auth config (not committed)
```

---

## Design Notes

- **Why a tool-calling loop, not intent classification?** Conditional multi-step queries (*"check entitlement, then raise a ticket if I'm not entitled"*) require a decision based on live data — an agentic loop does this natively; a classifier can't.
- **Why Groq + LLaMA 3.1?** Free tier, function-calling support, and sub-second latency. The design is model-agnostic — swapping to another provider is a small change in `llm.py`.
- **Why in-memory mock data?** Zero setup — clone and run. The data shapes mirror what real systems (ServiceNow, Okta, AD) would return. Tickets and the conversation audit trail persist to SQLite (`deskflow.db`) so nothing is lost on restart.
- **Why gate priority with rules instead of trusting the LLM?** A wrong priority means a wrong SLA clock. `classifier.py` escalates/denies the model's guess with a logged, auditable reason — never silently.
- **Why flag instead of auto-close?** Stale/SLA sweeps surface work for humans; auto-closing tickets without review is how real ITSM systems lose incidents.

---

## License

MIT
