from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from backend.auth import create_access_token, verify_credentials
from backend.schemas.common import APIResponse

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenData(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=APIResponse[TokenData])
async def login(body: LoginRequest):
    if not verify_credentials(body.username, body.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    token = create_access_token(subject=body.username)
    return APIResponse.ok(
        data=TokenData(access_token=token),
        message="Login successful",
    )
