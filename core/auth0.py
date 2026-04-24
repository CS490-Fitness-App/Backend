# FastAPI dependency for protected routes that reads Auth0 JWT claims from Bearer tokens.
# Returns decoded claims (including `sub`) for route handlers and role checks.

import base64
import json
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.config import settings


bearer_scheme = HTTPBearer(auto_error=False)


def _normalize_audience(value: str | None) -> str:
    if not value:
        return ""
    return value.strip().rstrip("/").lower()


def _decode_jwt_payload(token: str) -> dict:
    "Decode JWT payload section without verifying signature."
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Token is not valid")

    payload_segment = parts[1]
    padding = "=" * (-len(payload_segment) % 4)
    raw_payload = base64.urlsafe_b64decode(payload_segment + padding)
    return json.loads(raw_payload.decode("utf-8"))


def auth(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    """
    Simple auth() dependency.
    This checks (iss, aud, sub).
    """
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )

    token = credentials.credentials
    try:
        claims = _decode_jwt_payload(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
        )

    # Lightweight checks to help frontend catch wrong token config quickly.
    if settings.auth0_domain:
        expected_iss = f"https://{settings.auth0_domain}/"
        if claims.get("iss") != expected_iss:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token issuer mismatch",
            )

    if settings.auth0_api_audience:
        expected_audience = _normalize_audience(settings.auth0_api_audience)
        aud_claim = claims.get("aud")
        if isinstance(aud_claim, str):
            aud_ok = _normalize_audience(aud_claim) == expected_audience
        else:
            normalized_audiences = {
                _normalize_audience(item)
                for item in (aud_claim or [])
                if isinstance(item, str)
            }
            aud_ok = expected_audience in normalized_audiences

        if not aud_ok:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token audience mismatch",
            )

    if not claims.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject (sub)",
        )

    return claims
