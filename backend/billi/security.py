"""Private test-access controls for BILLI knowledge endpoints."""
import hmac


def token_matches(supplied: str | None, expected: str | None) -> bool:
    """Compare an access token without leaking timing information.

    Missing server configuration fails closed. Never treat an unset token as
    an open endpoint.
    """
    if not isinstance(supplied, str) or not isinstance(expected, str):
        return False
    if not supplied or not expected:
        return False
    try:
        return hmac.compare_digest(supplied.encode("utf-8"), expected.encode("utf-8"))
    except (TypeError, UnicodeError):
        return False
