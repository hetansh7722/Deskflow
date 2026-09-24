"""
Deterministic priority classifier for ticket creation.

Runs as an independent gate alongside the LLM's priority argument so that
priority is never just "whatever the model guessed":
  - keyword evidence at HIGH/CRITICAL can escalate the model's value
  - routine evidence (requests, questions) caps the model at MEDIUM
  - an unsupported CRITICAL/HIGH claim is capped when no keywords match
"""

import re

RANKS = {"low": 0, "medium": 1, "high": 2, "critical": 3}
RANK_NAMES = {v: k for k, v in RANKS.items()}

# (rank, human-readable label, regex)
_RULES: list[tuple[int, str, str]] = [
    (
        3,
        "critical impact keywords",
        r"\b(production down|full outage|outage|data loss|data breach|"
        r"ransomware|phishing|compromised|security incident)\b",
    ),
    (
        2,
        "business-impact keywords",
        r"\b(cannot work|can'?t work|blocked|urgent|asap|emergency|not working|"
        r"offline|locked out|down|crash(?:ed|ing)?|all users|several users|"
        r"whole team|completely fail(?:ed|ing)?)\b",
    ),
    (
        1,
        "problem keywords",
        r"\b(error|failing|failure|broken|slow|lag(?:ging)?|timeout|"
        r"issue|problem|unable|keeps?|intermittent|degraded)\b",
    ),
    (
        0,
        "routine request keywords",
        r"\b(request|please|install|installation|license|licence|entitlement|"
        r"how do i|question|when will|add me|access to|upgrade)\b",
    ),
]

_COMPILED = [(rank, label, re.compile(pattern)) for rank, label, pattern in _RULES]


def classify_priority(title: str, description: str, model_priority: str) -> dict:
    """Return the final priority plus an auditable explanation."""
    model_priority = model_priority if model_priority in RANKS else "medium"
    model_rank = RANKS[model_priority]

    text = f"{title} {description}".lower()
    matched: list[str] = []
    evidence_rank = -1
    for rank, label, pattern in _COMPILED:
        if pattern.search(text):
            matched.append(label)
            evidence_rank = max(evidence_rank, rank)

    if evidence_rank < 0:
        # No keyword evidence at all — a HIGH/CRITICAL claim is unsupported.
        final_rank = min(model_rank, RANKS["medium"])
        reason = "No supporting keywords — high/critical claims capped at medium."
    elif evidence_rank >= RANKS["high"]:
        # Strong evidence: escalate, never downgrade below what the rules prove.
        final_rank = max(model_rank, evidence_rank)
        reason = "Strong impact keywords found in the ticket text."
    else:
        # Routine/problem wording only: the model cannot claim above medium.
        final_rank = min(model_rank, RANKS["medium"])
        reason = "Only routine/problem keywords found — capped at medium."

    final_priority = RANK_NAMES[final_rank]
    if final_rank > model_rank:
        decision = "escalated"
    elif final_rank < model_rank:
        decision = "downgraded"
    else:
        decision = "unchanged"

    return {
        "model_priority": model_priority,
        "evidence_priority": RANK_NAMES[evidence_rank] if evidence_rank >= 0 else None,
        "final_priority": final_priority,
        "decision": decision,
        "matched_keywords": matched,
        "reason": reason,
    }
