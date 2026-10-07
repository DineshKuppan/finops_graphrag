from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserAttributes(BaseModel):
    department: str
    clearance_level: int
    region: str


class UserProfile(BaseModel):
    id: str
    username: str
    full_name: str
    roles: list[str]
    attributes: UserAttributes
