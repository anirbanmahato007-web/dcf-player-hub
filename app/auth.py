import secrets
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

ADMIN_PASSWORD = "admin123"
tokens_db = set()
security = HTTPBearer(auto_error=False)

def authenticate_admin(password: str) -> str:
    if password == ADMIN_PASSWORD:
        token = secrets.token_hex(32)
        tokens_db.add(token)
        return token
    return None

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    if not credentials or credentials.credentials not in tokens_db:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized admin access required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials
