"""
Authentication API endpoints
"""
import logging
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, Optional

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import jwt

from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])
security = HTTPBearer()

# In-memory storage for client credentials (in production, use a database)
CLIENT_CREDENTIALS: Dict[str, str] = {}

# In-memory storage for active tokens (in production, use Redis or database)
ACTIVE_TOKENS: Dict[str, Dict] = {}

# JWT settings
JWT_SECRET = settings.SECRET_KEY if hasattr(settings, 'SECRET_KEY') else secrets.token_urlsafe(32)
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24


class ClientCredentialsRequest(BaseModel):
    """Client credentials authentication request"""
    client_id: str
    client_secret: str
    grant_type: str = "client_credentials"


class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class ClientCredentials(BaseModel):
    """Client credentials model"""
    client_id: str
    client_secret: str
    name: str
    description: Optional[str] = None


def generate_client_credentials(name: str, description: Optional[str] = None) -> ClientCredentials:
    """Generate new client credentials"""
    client_id = f"hls_{secrets.token_urlsafe(16)}"
    client_secret = secrets.token_urlsafe(32)
    
    CLIENT_CREDENTIALS[client_id] = client_secret
    
    return ClientCredentials(
        client_id=client_id,
        client_secret=client_secret,
        name=name,
        description=description
    )


def verify_client_credentials(client_id: str, client_secret: str) -> bool:
    """Verify client credentials"""
    return CLIENT_CREDENTIALS.get(client_id) == client_secret


def create_access_token(client_id: str) -> str:
    """Create JWT access token"""
    expire = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    payload = {
        "sub": client_id,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access_token"
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    # Store token info
    ACTIVE_TOKENS[token] = {
        "client_id": client_id,
        "expires_at": expire,
        "created_at": datetime.utcnow()
    }
    
    return token


def verify_access_token(token: str) -> Optional[str]:
    """Verify JWT access token and return client_id"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        client_id = payload.get("sub")
        
        # Check if token is in active tokens
        if token not in ACTIVE_TOKENS:
            return None
            
        # Check if token is expired
        token_info = ACTIVE_TOKENS[token]
        if datetime.utcnow() > token_info["expires_at"]:
            # Clean up expired token
            del ACTIVE_TOKENS[token]
            return None
            
        return client_id
        
    except jwt.ExpiredSignatureError:
        # Clean up expired token
        if token in ACTIVE_TOKENS:
            del ACTIVE_TOKENS[token]
        return None
    except jwt.JWTError:
        return None


async def get_current_client(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Get current authenticated client"""
    token = credentials.credentials
    client_id = verify_access_token(token)
    
    if not client_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return client_id


@router.post("/auth/token", response_model=TokenResponse)
async def get_access_token(request: ClientCredentialsRequest):
    """
    OAuth2 client credentials flow - exchange client credentials for access token
    """
    if request.grant_type != "client_credentials":
        raise HTTPException(
            status_code=400,
            detail="Unsupported grant type. Only 'client_credentials' is supported."
        )
    
    # Verify client credentials
    if not verify_client_credentials(request.client_id, request.client_secret):
        raise HTTPException(
            status_code=401,
            detail="Invalid client credentials"
        )
    
    # Create access token
    access_token = create_access_token(request.client_id)
    
    logger.info(f"Access token created for client: {request.client_id}")
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=TOKEN_EXPIRE_HOURS * 3600  # Convert hours to seconds
    )


@router.post("/auth/credentials", response_model=ClientCredentials)
async def create_client_credentials(name: str, description: Optional[str] = None):
    """
    Create new client credentials (admin endpoint)
    In production, this should be protected with admin authentication
    """
    credentials = generate_client_credentials(name, description)
    
    logger.info(f"New client credentials created: {credentials.client_id}")
    
    return credentials


@router.get("/auth/verify")
async def verify_token(current_client: str = Depends(get_current_client)):
    """
    Verify current token and return client information
    """
    return {
        "valid": True,
        "client_id": current_client,
        "message": "Token is valid"
    }


@router.delete("/auth/revoke")
async def revoke_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Revoke current access token
    """
    token = credentials.credentials
    
    if token in ACTIVE_TOKENS:
        del ACTIVE_TOKENS[token]
        return {"message": "Token revoked successfully"}
    
    raise HTTPException(
        status_code=404,
        detail="Token not found or already expired"
    )


# Initialize with a default client for development
if not CLIENT_CREDENTIALS:
    default_creds = generate_client_credentials(
        name="Default Development Client",
        description="Default client credentials for development and testing"
    )
    logger.info(f"Default client credentials created:")
    logger.info(f"  Client ID: {default_creds.client_id}")
    logger.info(f"  Client Secret: {default_creds.client_secret}")
