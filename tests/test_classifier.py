from classifier import classify_priority


def test_escalates_medium_claim_with_critical_evidence():
    v = classify_priority("Production down", "entire system outage for all users", "medium")
    assert v["final_priority"] == "critical"
    assert v["decision"] == "escalated"
    assert v["matched_keywords"]


def test_downgrades_critical_claim_on_routine_request():
    v = classify_priority("Please install Notion", "routine add request", "critical")
    assert v["final_priority"] == "medium"
    assert v["decision"] == "downgraded"


def test_downgrades_high_claim_with_only_routine_evidence():
    v = classify_priority("Add me to Jira", "question about access", "high")
    assert v["final_priority"] == "medium"


def test_unchanged_when_evidence_agrees():
    v = classify_priority("Laptop battery fails", "keeps crashing with errors", "high")
    assert v["final_priority"] == "high"
    assert v["decision"] == "unchanged"


def test_no_evidence_caps_high_claims():
    v = classify_priority("zzz", "qqq", "critical")
    assert v["final_priority"] == "medium"
    assert v["evidence_priority"] is None


def test_low_model_priority_with_routine_evidence_stays_low():
    v = classify_priority("Password reset request", "", "low")
    assert v["final_priority"] == "low"
    assert v["decision"] == "unchanged"


def test_invalid_model_priority_defaults_to_medium():
    v = classify_priority("Password reset request", "", "banana")
    assert v["model_priority"] == "medium"
