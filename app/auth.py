import hashlib
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

ADMIN_PASSWORD = "admin123"
SECRET_SALT = "dcf_player_hub_secret_2026"

def get_valid_token(password: str) -> str:
    return hashlib.sha256(f"{password}_{SECRET_SALT}".encode('utf-8')).hexdigest()

def authenticate_admin(password: str) -> str:
    if password == ADMIN_PASSWORD:
        return get_valid_token(ADMIN_PASSWORD)
    return None

security = HTTPBearer(auto_error=False)

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    valid_token = get_valid_token(ADMIN_PASSWORD)
    if not credentials or credentials.credentials != valid_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized admin access required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials
