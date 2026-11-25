"""Request/response models. The `type` field selects the solver."""

from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator

from multicaptcha.transcribers.base import TranscriberName


class ProxyConfig(BaseModel):
    server: str
    username: str | None = None
    password: str | None = None


class BaseSolveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: str
    sitekey: str = Field(pattern=r"^[A-Za-z0-9_-]{10,100}$")
    proxy: ProxyConfig | None = None

    @field_validator("url")
    @classmethod
    def _http_url(cls, value: str) -> str:
        parts = urlsplit(value)
        if parts.scheme not in ("http", "https") or not parts.hostname:
            raise ValueError("must be an absolute http(s) URL")
        return value


class RecaptchaV2Request(BaseSolveRequest):
    type: Literal["recaptcha_v2"]
    transcriber: TranscriberName = TranscriberName.WHISPER


# When a second captcha type is added, this becomes:
#   Annotated[RecaptchaV2Request | HCaptchaRequest, Field(discriminator="type")]
SolveRequest = RecaptchaV2Request


class SolveSuccess(BaseModel):
    status: Literal["ok"] = "ok"
    type: str
    token: str
    elapsed_seconds: float


class SolveFailure(BaseModel):
    status: Literal["error"] = "error"
    code: str
    message: str
