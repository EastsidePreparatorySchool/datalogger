import hmac
import secrets

from flask import current_app, session


def is_enabled():
    return bool(current_app.config.get("ADMIN_PASSWORD"))


def password_matches(candidate):
    expected = current_app.config["ADMIN_PASSWORD"]
    return hmac.compare_digest(candidate.encode(), expected.encode())


def log_in():
    session.clear()
    session.permanent = True
    session["admin"] = True


def log_out():
    session.clear()


def is_logged_in():
    return session.get("admin") is True


def csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_urlsafe(32)
    return session["csrf"]


def csrf_valid(submitted):
    expected = session.get("csrf")
    return bool(expected) and hmac.compare_digest(submitted or "", expected)
