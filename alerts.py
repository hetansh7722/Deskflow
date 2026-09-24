"""
Pluggable notification channels for DeskFlow.
Backends: Discord webhook, SMTP email, and an always-on log channel.
Channels activate only when their env vars are configured.
"""

import os
import smtplib
from email.message import EmailMessage

import httpx
import logger

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM") or SMTP_USER or "deskflow@localhost"
SMTP_TO = os.getenv("SMTP_TO", "")
SMTP_STARTTLS = os.getenv("SMTP_STARTTLS", "1") == "1"


def _send_discord(content: str) -> bool:
    if not DISCORD_WEBHOOK_URL:
        return False
    try:
        resp = httpx.post(DISCORD_WEBHOOK_URL, json={"content": content}, timeout=5)
        return resp.status_code in (200, 204)
    except httpx.HTTPError as e:
        logger.log(f"[Notifier] Discord webhook failed: {e}", level="warning")
        return False


def _send_email(subject: str, body: str) -> bool:
    if not (SMTP_HOST and SMTP_TO):
        return False
    try:
        msg = EmailMessage()
        msg["From"] = SMTP_FROM
        msg["To"] = SMTP_TO
        msg["Subject"] = subject
        msg.set_content(body)

        if SMTP_PORT == 465:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=10) as server:
                if SMTP_USER:
                    server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)
        else:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
                if SMTP_STARTTLS:
                    server.starttls()
                if SMTP_USER:
                    server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)
        return True
    except (smtplib.SMTPException, OSError) as e:
        logger.log(f"[Notifier] SMTP failed: {e}", level="warning")
        return False


def notify(title: str, body: str, level: str = "warning") -> dict:
    """Fan an alert out to every configured channel."""
    logger.log(f"[Alert] {title} — {body}", level=level)
    return {
        "log": True,
        "discord": _send_discord(f"**{title}**\n{body}"),
        "email": _send_email(title, body),
    }


def send_discord_alert(ticket: dict) -> None:
    """P1 (high/critical) ticket alert — kept as the tools.py hook."""
    if ticket.get("priority") not in ("high", "critical"):
        return
    notify(
        "P1 Ticket Alert",
        f"**{ticket.get('ticket_id')}** — {ticket.get('title')}\n"
        f"Category: {ticket.get('category')} | Assigned: {ticket.get('assigned_to')}\n"
        f"Reported by: {ticket.get('employee_id', 'unknown')}",
        level="error",
    )
