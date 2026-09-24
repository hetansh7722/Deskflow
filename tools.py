"""
Helper tools used by DeskFlow.
Contains ticket handling, entitlement checks,
password reset logic, and tool dispatcher functions.
"""

import json
import random
import string
from datetime import datetime
import auth
from mock_data import (
    USERS,
    SOFTWARE_CATALOG,
    TICKETS,
    _next_ticket_id,
    DEVICES,
    VPN_GATEWAY,
    VPN_SESSIONS,
)
from alerts import send_discord_alert
from classifier import classify_priority
import db


# SLA targets per priority (minutes) + human-readable labels
SLA_TARGETS_MINUTES = {
    "low": 5 * 8 * 60,       # 5 business days (8h days)
    "medium": 24 * 60,       # 24 hours
    "high": 2 * 60,          # 2 hours
    "critical": 30,          # 30 minutes
}
SLA_LABELS = {
    "low": "5 business days",
    "medium": "24 hours",
    "high": "2 hours",
    "critical": "30 minutes",
}


# Helper functions

def _match_software(name: str) -> str | None:
    """Case-insensitive partial match against catalog keys."""
    name_lower = name.lower()
    for key in SOFTWARE_CATALOG:
        if name_lower in key.lower() or key.lower() in name_lower:
            return key
    return None


# Ticket operations

def get_user_profile(employee_id: str) -> dict:
    """Return employee profile (name, dept, role, entitlements)."""
    user = USERS.get(employee_id.upper())
    if not user:
        return {"error": f"No employee found with ID '{employee_id}'. Check the ID and try again."}
    if not user["active"]:
        return {"error": f"Employee {employee_id} account is inactive. Contact HR."}
    return {
        "employee_id": user["employee_id"],
        "name": user["name"],
        "email": user["email"],
        "department": user["department"],
        "role": user["role"],
        "active": user["active"],
        "current_entitlements": user["entitlements"],
    }


def check_software_entitlement(employee_id: str, software_name: str) -> dict:
    """Check if an employee has a software entitlement; return catalog info too."""
    user = USERS.get(employee_id.upper())
    if not user:
        return {"error": f"Employee '{employee_id}' not found."}

    matched = _match_software(software_name)
    if not matched:
        return {
            "error": f"Software '{software_name}' not found in the catalog.",
            "available_software": list(SOFTWARE_CATALOG.keys()),
        }

    sw = SOFTWARE_CATALOG[matched]
    entitled = matched in user["entitlements"]

    return {
        "employee_id": employee_id,
        "employee_name": user["name"],
        "software": matched,
        "entitled": entitled,
        "approval_required": sw["approval_required"],
        "approver_role": sw.get("approver_role", "IT Admin"),
        "available_licenses": sw["available_licenses"],
        "cost_per_seat_usd": sw.get("cost_per_seat_usd"),
    }


def create_ticket(
    employee_id: str,
    title: str,
    priority: str,
    description: str,
    category: str = "General",
) -> dict:
    """Create a helpdesk ticket."""
    user = USERS.get(employee_id.upper())
    if not user:
        return {"error": f"Employee '{employee_id}' not found. Cannot create ticket."}

    priority = priority.lower()
    if priority not in ("low", "medium", "high", "critical"):
        priority = "medium"

    # Independent gate: never trust the LLM's priority guess on its own.
    review = classify_priority(title, description, priority)
    priority = review["final_priority"]

    ticket_id = _next_ticket_id()
    now = datetime.now().isoformat()

    ticket = {
        "ticket_id": ticket_id,
        "employee_id": employee_id.upper(),
        "title": title,
        "description": description,
        "priority": priority,
        "status": "open",
        "category": category,
        "created_at": now,
        "updated_at": now,
        "assigned_to": "L1-HelpDesk",
        "resolution": None,
        "priority_review": review,
    }
    TICKETS[ticket_id] = ticket
    db.save_ticket(ticket)
    send_discord_alert(ticket)

    return {
        "ticket_id": ticket_id,
        "status": "open",
        "priority": priority,
        "priority_source": review["decision"],
        "priority_reason": review["reason"],
        "category": category,
        "assigned_to": "L1-HelpDesk",
        "estimated_response_time": SLA_LABELS[priority],
        "message": f"Ticket {ticket_id} created successfully for {user['name']}.",
    }


def get_ticket_status(ticket_id: str) -> dict:
    """Fetch status and details of an existing support ticket."""
    ticket = TICKETS.get(ticket_id.upper())
    if not ticket:
        return {"error": f"Ticket '{ticket_id}' not found. Check the ticket ID."}
    return {
        "ticket_id": ticket["ticket_id"],
        "title": ticket["title"],
        "status": ticket["status"],
        "priority": ticket["priority"],
        "category": ticket["category"],
        "assigned_to": ticket["assigned_to"],
        "created_at": ticket["created_at"],
        "updated_at": ticket["updated_at"],
        "resolution": ticket["resolution"],
    }


def list_user_tickets(employee_id: str) -> dict:
    """List all support tickets raised by an employee."""
    user = USERS.get(employee_id.upper())
    if not user:
        return {"error": f"Employee '{employee_id}' not found."}

    user_tickets = [
        {
            "ticket_id": t["ticket_id"],
            "title": t["title"],
            "status": t["status"],
            "priority": t["priority"],
            "category": t["category"],
            "created_at": t["created_at"],
        }
        for t in TICKETS.values()
        if t["employee_id"] == employee_id.upper()
    ]

    return {
        "employee_id": employee_id,
        "employee_name": user["name"],
        "total_tickets": len(user_tickets),
        "tickets": user_tickets,
    }


def reset_password(employee_id: str) -> dict:
    """Reset employee password."""
    user = USERS.get(employee_id.upper())
    if not user:
        return {"error": f"Employee '{employee_id}' not found."}

    chars = string.ascii_letters + string.digits + "!@#$"
    temp_pw = "".join(random.choices(chars, k=14))

    return {
        "employee_id": employee_id,
        "name": user["name"],
        "status": "success",
        "temporary_password": temp_pw,
        "note": (
            "Temporary password issued. An email with login instructions has been "
            f"sent to {user['email']}. Password must be changed on first login."
        ),
    }


# Endpoint + network diagnostics

def _device_findings(device: dict) -> list[dict]:
    """Evaluate one device against compliance rules; returns findings with remediation."""
    findings = []
    if not device["disk_encrypted"]:
        findings.append({
            "issue": "Disk encryption is disabled",
            "severity": "high",
            "remediation": f"Enable BitLocker (Windows) or FileVault (macOS) via {device['managed_by']}",
        })
    if device["os_patch_days"] > 45:
        findings.append({
            "issue": f"OS update pending for {device['os_patch_days']} days",
            "severity": "medium",
            "remediation": "Run the pending OS update (Settings > Windows Update / Software Update)",
        })
    if device["av_signature_days"] > 7:
        findings.append({
            "issue": f"Antivirus signatures are {device['av_signature_days']} days old",
            "severity": "medium",
            "remediation": "Force an antivirus/Defender signature update",
        })
    try:
        last_seen = datetime.fromisoformat(device["last_check_in"])
        hours = (datetime.now() - last_seen).total_seconds() / 3600
    except ValueError:
        hours = 0.0
    if hours > 72:
        findings.append({
            "issue": f"No device check-in for {int(hours // 24)} day(s)",
            "severity": "low",
            "remediation": "Device not reporting to MDM — confirm it is powered on and connected",
        })
    return findings


def get_user_devices(employee_id: str) -> dict:
    """List an employee's assigned endpoints from the MDM inventory."""
    user = USERS.get(employee_id.upper())
    if not user:
        return {"error": f"Employee '{employee_id}' not found."}

    devices = DEVICES.get(user["employee_id"], [])
    return {
        "employee_id": user["employee_id"],
        "employee_name": user["name"],
        "device_count": len(devices),
        "devices": [
            {
                "device_id": d["device_id"],
                "name": d["name"],
                "type": d["type"],
                "model": d["model"],
                "os": d["os"],
                "managed_by": d["managed_by"],
                "last_check_in": d["last_check_in"],
            }
            for d in devices
        ],
    }


def check_device_compliance(employee_id: str, device_id: str | None = None) -> dict:
    """Run a compliance check (encryption, patching, AV, check-in) on managed devices."""
    user = USERS.get(employee_id.upper())
    if not user:
        return {"error": f"Employee '{employee_id}' not found."}

    devices = DEVICES.get(user["employee_id"], [])
    if device_id:
        devices = [d for d in devices if d["device_id"] == device_id.upper()]
        if not devices:
            known = [d["device_id"] for d in DEVICES.get(user["employee_id"], [])]
            return {
                "error": f"Device '{device_id}' not assigned to {user['employee_id']}.",
                "assigned_devices": known,
            }

    results = []
    for d in devices:
        findings = _device_findings(d)
        results.append({
            "device_id": d["device_id"],
            "name": d["name"],
            "os": d["os"],
            "compliant": not findings,
            "findings": findings,
        })

    return {
        "employee_id": user["employee_id"],
        "employee_name": user["name"],
        "devices_checked": len(results),
        "all_compliant": all(r["compliant"] for r in results),
        "devices": results,
    }


def check_vpn_status(employee_id: str) -> dict:
    """Check corporate VPN gateway health and the employee's VPN session."""
    user = USERS.get(employee_id.upper())
    if not user:
        return {"error": f"Employee '{employee_id}' not found."}

    session = VPN_SESSIONS.get(user["employee_id"])
    if not session:
        return {"error": f"No VPN session found for {user['employee_id']}."}

    issues: list[str] = []
    actions: list[str] = []

    if not session["connected"]:
        issues.append("Not connected to the VPN")
        actions += [
            f"Re-authenticate at {VPN_GATEWAY['portal']} (SAML sessions expire after 12h)",
            "Toggle the VPN connection off and on in the client",
            "Confirm normal internet access works without the VPN",
        ]
    if session["client_version"] != VPN_GATEWAY["server_version"]:
        issues.append(
            f"VPN client outdated: {session['client_version']} "
            f"(gateway runs {VPN_GATEWAY['server_version']})"
        )
        actions.append("Update the VPN client from the software portal")
    if session["connected"]:
        try:
            handshake = datetime.fromisoformat(session["last_handshake"])
            age_min = (datetime.now() - handshake).total_seconds() / 60
        except ValueError:
            age_min = 0.0
        if age_min > 30:
            issues.append(f"Last handshake {int(age_min)} minutes ago (stale)")
            actions.append("Reconnect to refresh the tunnel handshake")

    if not issues:
        actions.append("Connection healthy — no action needed")

    return {
        "employee_id": user["employee_id"],
        "employee_name": user["name"],
        "gateway": dict(VPN_GATEWAY),
        "session": session,
        "issues": issues,
        "recommended_actions": actions,
    }


# Ticket lifecycle

VALID_TICKET_STATUSES = ("open", "in_progress", "pending", "resolved", "closed")


def update_ticket_status(
    ticket_id: str,
    employee_id: str,
    status: str,
    resolution: str | None = None,
) -> dict:
    """Move a ticket through its lifecycle. Only the owning employee may update it."""
    ticket = TICKETS.get(ticket_id.upper())
    if not ticket:
        return {"error": f"Ticket '{ticket_id}' not found. Check the ticket ID."}
    if ticket["employee_id"] != employee_id.upper() and not auth.is_admin(employee_id):
        return {
            "error": (
                f"Ticket {ticket_id.upper()} belongs to {ticket['employee_id']}, "
                f"not {employee_id.upper()}. You can only update your own tickets."
            )
        }

    status = status.lower().strip()
    if status not in VALID_TICKET_STATUSES:
        return {
            "error": f"Invalid status '{status}'.",
            "valid_statuses": list(VALID_TICKET_STATUSES),
        }
    if status in ("resolved", "closed") and not (resolution or "").strip():
        return {"error": "A resolution note is required to resolve or close a ticket."}

    previous = ticket["status"]
    ticket["status"] = status
    if resolution:
        ticket["resolution"] = resolution.strip()
    ticket["updated_at"] = datetime.now().isoformat()
    db.save_ticket(ticket)

    return {
        "ticket_id": ticket["ticket_id"],
        "status": status,
        "previous_status": previous,
        "resolution": ticket["resolution"],
        "updated_at": ticket["updated_at"],
        "message": f"Ticket {ticket['ticket_id']} moved from '{previous}' to '{status}'.",
    }


# Tool schemas for LLM

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_user_profile",
            "description": (
                "Retrieve an employee's profile from the HR/IT directory: "
                "name, department, role, email, and list of currently entitled software. "
                "Call this first when you need to know who the employee is or what they already have."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_id": {
                        "type": "string",
                        "description": "Employee ID, e.g. EMP001",
                    }
                },
                "required": ["employee_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_software_entitlement",
            "description": (
                "Check whether an employee is currently entitled to a specific software application. "
                "Also returns whether approval is required and how many licenses are available."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_id": {"type": "string", "description": "Employee ID"},
                    "software_name": {
                        "type": "string",
                        "description": "Name of the software, e.g. 'Adobe Creative Suite', 'GitHub'",
                    },
                },
                "required": ["employee_id", "software_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_ticket",
            "description": (
                "Open a new IT helpdesk support ticket for an employee. "
                "Use this for software access requests, hardware issues, network problems, "
                "password resets needing L2 attention, or any issue that needs tracking."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_id": {"type": "string"},
                    "title": {
                        "type": "string",
                        "description": "Short descriptive title for the ticket",
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                        "description": "Ticket priority. Use 'high' for access blockers or business-critical issues.",
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed description of the issue or request",
                    },
                    "category": {
                        "type": "string",
                        "description": "Category: 'Software Access', 'Hardware', 'Network', 'Password Reset', 'General'",
                    },
                },
                "required": ["employee_id", "title", "priority", "description"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_ticket_status",
            "description": "Get the current status, assignment, and resolution details of an IT support ticket by ticket ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_id": {
                        "type": "string",
                        "description": "Ticket ID, e.g. TKT-1001",
                    }
                },
                "required": ["ticket_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_user_tickets",
            "description": "List all IT support tickets raised by a specific employee.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_id": {"type": "string", "description": "Employee ID"}
                },
                "required": ["employee_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reset_password",
            "description": (
                "Reset an employee's network/system password and generate a temporary credential. "
                "The employee will receive login instructions by email."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_id": {"type": "string", "description": "Employee ID"}
                },
                "required": ["employee_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_devices",
            "description": (
                "List an employee's assigned endpoints (laptops/desktops) from the "
                "MDM device inventory: device IDs, model, OS, management platform, last check-in."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_id": {"type": "string", "description": "Employee ID"}
                },
                "required": ["employee_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_device_compliance",
            "description": (
                "Run a compliance check on an employee's managed devices: disk encryption, "
                "OS patch level, antivirus signatures, and MDM check-in. Returns per-device "
                "findings with remediation steps. Optionally check a single device."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_id": {"type": "string", "description": "Employee ID"},
                    "device_id": {
                        "type": "string",
                        "description": "Optional device ID, e.g. 'LAP-1001'. Omit to check all devices.",
                    },
                },
                "required": ["employee_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_vpn_status",
            "description": (
                "Check corporate VPN gateway health and the employee's VPN session: connection "
                "state, client version, last handshake, plus troubleshooting steps. Use for any "
                "'cannot connect to VPN' or network connectivity issue."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_id": {"type": "string", "description": "Employee ID"}
                },
                "required": ["employee_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_ticket_status",
            "description": (
                "Update an IT ticket's lifecycle status. Use 'in_progress' when work starts, "
                "'pending' while waiting on the employee, and 'resolved'/'closed' when done "
                "(a resolution note is required for resolved/closed). Employees may only "
                "update their own tickets."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_id": {
                        "type": "string",
                        "description": "Ticket ID, e.g. TKT-1001",
                    },
                    "employee_id": {
                        "type": "string",
                        "description": "ID of the employee making the update (must own the ticket)",
                    },
                    "status": {
                        "type": "string",
                        "enum": ["open", "in_progress", "pending", "resolved", "closed"],
                        "description": "New ticket status",
                    },
                    "resolution": {
                        "type": "string",
                        "description": "Resolution note — required when resolving or closing",
                    },
                },
                "required": ["ticket_id", "employee_id", "status"],
            },
        },
    },
]

# Tool dispatcher

_TOOL_FUNCTIONS = {
    "get_user_profile": get_user_profile,
    "check_software_entitlement": check_software_entitlement,
    "create_ticket": create_ticket,
    "get_ticket_status": get_ticket_status,
    "list_user_tickets": list_user_tickets,
    "reset_password": reset_password,
    "get_user_devices": get_user_devices,
    "check_device_compliance": check_device_compliance,
    "check_vpn_status": check_vpn_status,
    "update_ticket_status": update_ticket_status,
}

TOOL_NAMES = list(_TOOL_FUNCTIONS)


def dispatch_tool(tool_name: str, arguments: dict) -> str:
    """Execute a tool by name and return JSON string result."""
    func = _TOOL_FUNCTIONS.get(tool_name)
    if not func:
        return json.dumps({"error": f"Unknown tool: '{tool_name}'"})
    try:
        result = func(**arguments)
        return json.dumps(result, default=str)
    except TypeError as e:
        return json.dumps({"error": f"Invalid arguments for {tool_name}: {e}"})
    except Exception as e:
        return json.dumps({"error": f"Tool '{tool_name}' failed: {e}"})
