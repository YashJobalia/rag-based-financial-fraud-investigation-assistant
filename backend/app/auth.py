from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings
from .db import connection

bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Principal:
    tenant: str
    actor: str
    role: str


def principal(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> Principal:
    config = settings()
    if credentials is None:
        if config.enable_public_demo:
            return Principal("demo", "public-demo", "viewer")
        raise HTTPException(401, "Analyst authentication required")
    secret = config.auth_secret.get_secret_value()
    if len(secret) < 32:
        raise HTTPException(503, "Analyst authentication is not configured")
    try:
        claims = jwt.decode(
            credentials.credentials,
            secret,
            algorithms=["HS256"],
            audience="fraud-investigation",
            issuer="fraud-investigation",
            options={"require": ["exp", "iat", "sub", "tenant"]},
        )
        actor, tenant = str(claims["sub"]), str(claims["tenant"])
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid or expired analyst session") from None
    with connection(tenant, actor) as conn:
        member = conn.execute(
            "SELECT role FROM memberships WHERE tenant_id=%s AND actor=%s", (tenant, actor)
        ).fetchone()
    if not member:
        raise HTTPException(403, "No active analyst membership")
    return Principal(tenant, actor, member["role"])


def require_analyst(user: Principal):
    if user.role != "analyst":
        raise HTTPException(403, "Read-only demo. Analyst access required for this action.")
