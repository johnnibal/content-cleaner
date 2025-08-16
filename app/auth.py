import os
from fastapi import Header, HTTPException, status

TOKENS = {t.strip() for t in os.environ.get("API_TOKENS", "dev-token").split(",") if t.strip()}
BLOCKED = {t.strip() for t in os.environ.get("BLOCKED_TOKENS", "").split(",") if t.strip()}

def require_token(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid token")
    token = authorization.split(" ", 1)[1].strip()
    if token in BLOCKED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token blocked")
    if token not in TOKENS:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return token
