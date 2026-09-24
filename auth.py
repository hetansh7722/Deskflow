"""
Employee authentication for DeskFlow.
Stdlib only: PBKDF2 password hashing + HMAC-signed session tokens.
"""

import base64
import hashlib
import hmac
import os
import secrets
import time
from pathlib import Path

from mock_data import USERS

TOKEN_TTL_SECONDS = 12 * 3600
SECRET_FILE = Path(os.getenv("AUTH_SECRET_FILE", ".auth_secret"))
DEMO_PASSWORD = os.getenv("DESKFLOW_DEMO_PASSWORD", "Deskflow@123")


def hash_password(password: str, salt: str | None = None) -> str:
    """Return 'salt$pbkdf2_hex' for a password."""
    salt = salt or secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return f"{salt}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, _ = stored.split("$", 1)
    except ValueError:
        return False
    return hmac.compare_digest(hash_password(password, salt), stored)


# Demo credentials: every active employee shares one demo password.
PASSWORD_HASHES = {
    uid: hash_password(DEMO_PASSWORD)
    for uid, u in USERS.items()
    if u.get("active", True)
}

# Roles allowed to use the operations dashboard + admin endpoints.
ADMIN_ROLES = {"System Administrator", "IT Operations Manager", "Chief Technology Officer"}


def is_admin(employee_id: str) -> bool:
    """True if the employee's directory role grants admin access."""
    user = USERS.get((employee_id or "").strip().upper())
    return bool(user and user["role"] in ADMIN_ROLES)


def authenticate(employee_id: str, password: str) -> dict | None:
    """Check credentials against the in-memory directory. Returns the user dict."""
    user = USERS.get(employee_id.strip().upper())
    if not user or not user.get("active", True):
        return None
    stored = PASSWORD_HASHES.get(user["employee_id"])
    if not stored or not verify_password(password, stored):
        return None
    return user


def _secret() -> bytes:
    env_secret = os.getenv("AUTH_SECRET")
    if env_secret:
        return env_secret.encode()
    if not SECRET_FILE.exists():
        SECRET_FILE.write_text(secrets.token_hex(32))
    return SECRET_FILE.read_text().strip().encode()


def create_token(employee_id: str) -> str:
    """Signed token: base64url('EMP001.<expiry>') + '.' + hex hmac."""
    payload = f"{employee_id}.{int(time.time()) + TOKEN_TTL_SECONDS}"
    body = base64.urlsafe_b64encode(payload.encode()).decode()
    sig = hmac.new(_secret(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{sig}"


def verify_token(token: str | None) -> str | None:
    """Return the employee_id if the token is valid and unexpired, else None."""
    if not token or "." not in token:
        return None
    try:
        body, sig = token.rsplit(".", 1)
        payload = base64.urlsafe_b64decode(body.encode()).decode()
        expected = hmac.new(_secret(), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        employee_id, expiry = payload.rsplit(".", 1)
        if int(expiry) < time.time():
            return None
    except (ValueError, TypeError):
        return None
    return employee_id if employee_id in USERS else None
