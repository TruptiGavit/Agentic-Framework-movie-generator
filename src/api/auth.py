from fastapi import Depends, HTTPException, Security
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from typing import Optional, Dict
import jwt
from datetime import datetime, timedelta
import logging
from pydantic import BaseModel

class AuthConfig:
    SECRET_KEY = "your-secret-key"  # Change in production
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    API_KEY_NAME = "X-API-Key"

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    scopes: list[str] = []

class User(BaseModel):
    username: str
    disabled: Optional[bool] = None
    scopes: list[str] = []

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
api_key_header = APIKeyHeader(name=AuthConfig.API_KEY_NAME, auto_error=False)

class AuthHandler:
    def __init__(self):
        self.logger = logging.getLogger("movie_generator.auth")
        
        # In-memory API key store (replace with database in production)
        self.api_keys: Dict[str, Dict] = {
            "test-api-key": {
                "client_id": "test-client",
                "scopes": ["read", "write"]
            }
        }
    
    def create_access_token(self, data: dict) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=AuthConfig.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, AuthConfig.SECRET_KEY, algorithm=AuthConfig.ALGORITHM)
    
    def verify_token(self, token: str) -> TokenData:
        """Verify JWT token."""
        try:
            payload = jwt.decode(token, AuthConfig.SECRET_KEY, algorithms=[AuthConfig.ALGORITHM])
            username: str = payload.get("sub")
            scopes: list = payload.get("scopes", [])
            return TokenData(username=username, scopes=scopes)
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=401,
                detail="Could not validate credentials"
            )
    
    def verify_api_key(self, api_key: str) -> Dict:
        """Verify API key."""
        if api_key in self.api_keys:
            return self.api_keys[api_key]
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )

auth_handler = AuthHandler()

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    api_key: str = Security(api_key_header)
) -> User:
    """Get current user from token or API key."""
    if api_key:
        client_data = auth_handler.verify_api_key(api_key)
        return User(
            username=client_data["client_id"],
            scopes=client_data["scopes"]
        )
    
    token_data = auth_handler.verify_token(token)
    return User(
        username=token_data.username,
        scopes=token_data.scopes
    ) 