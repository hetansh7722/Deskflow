"""
Background monitors for DeskFlow.
- SLA breach checker: flags tickets that are past their SLA window.
- Stale ticket sweep: flags open tickets with no updates in N days.
Both are flag-only: they never change ticket status or close anything.
"""

import asyncio
import os
from datetime import datetime, timedelta

import alerts
import db
import logger
from mock_data import TICKETS
from tools import SLA_TARGETS_MINUTES

STALE_AFTER_DAYS = float(os.getenv("STALE_AFTER_DAYS", "7"))
INTERVAL_SECONDS = max(30, int(os.getenv("SLA_SCAN_INTERVAL_MINUTES", "1")) * 60)

_CLOSED_STATUSES = ("closed", "resolved")


def _parse(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        return None


def _summarize(tickets: list[dict], limit: int = 5) -> str:
    lines = [f"**{t['ticket_id']}** — {t.get('title')}" for t in tickets[:limit]]
    if len(tickets) > limit:
        lines.append(f"…and {len(tickets) - limit} more")
    return "\n".join(lines)


def check_sla_breaches(now: datetime | None = None) -> list[dict]:
    """Flag open tickets whose age exceeds their priority's SLA target."""
    now = now or datetime.now()
    breached = []
    for ticket_id, ticket in TICKETS.items():
        if ticket.get("status") in _CLOSED_STATUSES or ticket.get("sla_breached"):
            continue
        created = _parse(ticket.get("created_at"))
        target_minutes = SLA_TARGETS_MINUTES.get(ticket.get("priority", "medium"), 1440)
        if not created or (now - created).total_seconds() <= target_minutes * 60:
            continue

        ticket["sla_breached"] = True
        ticket["sla_breached_at"] = now.isoformat()
        db.save_ticket(ticket)
        breached.append(ticket)

    if breached:
        alerts.notify(
            f"SLA Breach Alert — {len(breached)} ticket(s)",
            _summarize(breached)
            + "\nEach ticket is past its priority SLA target. Flags saved; status unchanged.",
            level="error",
        )
    return breached


def check_stale_tickets(now: datetime | None = None) -> list[dict]:
    """Flag open tickets with no updates in STALE_AFTER_DAYS days."""
    now = now or datetime.now()
    cutoff = now - timedelta(days=STALE_AFTER_DAYS)
    stale = []
    for ticket_id, ticket in TICKETS.items():
        if ticket.get("status") in _CLOSED_STATUSES or ticket.get("stale"):
            continue
        updated = _parse(ticket.get("updated_at")) or _parse(ticket.get("created_at"))
        if not updated or updated > cutoff:
            continue

        ticket["stale"] = True
        ticket["stale_flagged_at"] = now.isoformat()
        db.save_ticket(ticket)
        stale.append(ticket)

    if stale:
        alerts.notify(
            f"Stale Ticket Sweep — {len(stale)} ticket(s) flagged",
            _summarize(stale)
            + f"\nNo update in {STALE_AFTER_DAYS:g} day(s) — flag only, not closed.",
        )
    return stale


async def monitor_loop() -> None:
    """Run both checks immediately, then on a fixed interval."""
    logger.log(
        f"[Monitor] Started — SLA scan every {INTERVAL_SECONDS}s, "
        f"stale after {STALE_AFTER_DAYS:g} day(s)"
    )
    while True:
        try:
            breached = check_sla_breaches()
            stale = check_stale_tickets()
            if breached or stale:
                logger.log(
                    f"[Monitor] {len(breached)} new SLA breach(es), "
                    f"{len(stale)} new stale ticket(s)"
                )
        except Exception as e:  # keep the loop alive
            logger.log(f"[Monitor] Scan failed: {e}", level="error")
        await asyncio.sleep(INTERVAL_SECONDS)
