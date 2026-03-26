from pydantic import BaseModel


class AuthSessionRead(BaseModel):
    role: str
    auth_enabled: bool
    allowed_capabilities: list[str]
