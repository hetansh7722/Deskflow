import base64
import hashlib
import hmac
import time

import auth


def test_password_hash_roundtrip():
    stored = auth.hash_password("S3cret!Value")
    assert auth.verify_password("S3cret!Value", stored)
    assert not auth.verify_password("wrong", stored)


def test_verify_password_rejects_malformed_stored_value():
    assert not auth.verify_password("x", "no-salt-format")


def test_authenticate_success():
    user = auth.authenticate("EMP001", auth.DEMO_PASSWORD)
    assert user is not None
    assert user["employee_id"] == "EMP001"


def test_authenticate_is_case_insensitive_on_id():
    assert auth.authenticate("emp001", auth.DEMO_PASSWORD) is not None


def test_authenticate_wrong_password():
    assert auth.authenticate("EMP001", "not-the-password") is None


def test_authenticate_unknown_employee():
    assert auth.authenticate("EMP999", auth.DEMO_PASSWORD) is None


def test_token_roundtrip():
    token = auth.create_token("EMP003")
    assert auth.verify_token(token) == "EMP003"


def test_tampered_token_rejected():
    token = auth.create_token("EMP003")
    forged = auth.create_token("EMP001")
    body, _ = forged.rsplit(".", 1)
    tampered = f"{body}.{token.rsplit('.', 1)[1]}"
    assert auth.verify_token(tampered) is None


def test_garbage_token_rejected():
    assert auth.verify_token(None) is None
    assert auth.verify_token("") is None
    assert auth.verify_token("not-a-token") is None
    assert auth.verify_token("a.b.c.d") is None


def test_expired_token_rejected():
    payload = f"EMP001.{int(time.time()) - 10}"
    body = base64.urlsafe_b64encode(payload.encode()).decode()
    sig = hmac.new(auth._secret(), payload.encode(), hashlib.sha256).hexdigest()
    assert auth.verify_token(f"{body}.{sig}") is None


def test_token_for_unknown_employee_rejected():
    payload = f"EMP999.{int(time.time()) + 3600}"
    body = base64.urlsafe_b64encode(payload.encode()).decode()
    sig = hmac.new(auth._secret(), payload.encode(), hashlib.sha256).hexdigest()
    assert auth.verify_token(f"{body}.{sig}") is None
