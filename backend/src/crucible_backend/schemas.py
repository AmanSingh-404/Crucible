from pydantic import BaseModel


class ContextItem(BaseModel):
    text: str
    origin: str  # e.g. a URL - only used when trusted=False


class SecurityCheckRequest(BaseModel):
    agent: str
    user_input: str = ""
    context: list[ContextItem] = []
    tool_name: str
    tool_args: dict = {}


class SecurityCheckResponse(BaseModel):
    action: str
    risk: float
    threat: str | None
    confidence: float
    reasons: list[str]
