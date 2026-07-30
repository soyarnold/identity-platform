from identity_api.schemas.auth import LoginRequest, RegisterRequest, UserOut
from identity_api.schemas.common import MessageOut
from identity_api.schemas.oauth import (
    ConsentRequest,
    ConsentResponse,
    OAuthClientCreate,
    OAuthClientOut,
    TokenResponse,
    UserInfoResponse,
)
from identity_api.schemas.session import SessionOut
from identity_api.schemas.webauthn import (
    LoginOptionsOut,
    LoginOptionsRequest,
    LoginVerifyRequest,
    PasskeyOut,
    PasskeyRenameRequest,
    RegisterOptionsOut,
    RegisterVerifyRequest,
    WebAuthnCredentialResponse,
)

__all__ = [
    "ConsentRequest",
    "ConsentResponse",
    "LoginOptionsOut",
    "LoginOptionsRequest",
    "LoginRequest",
    "LoginVerifyRequest",
    "MessageOut",
    "OAuthClientCreate",
    "OAuthClientOut",
    "PasskeyOut",
    "PasskeyRenameRequest",
    "RegisterOptionsOut",
    "RegisterRequest",
    "RegisterVerifyRequest",
    "SessionOut",
    "TokenResponse",
    "UserInfoResponse",
    "UserOut",
    "WebAuthnCredentialResponse",
]
