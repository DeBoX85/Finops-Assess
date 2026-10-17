"""Token provider reusing `az login` via azure-identity AzureCliCredential.
Known limits (Learn, read 2026-10-17): no token caching by the credential, one scope per request,
no claims challenge support (conditional access step-up may fail), 10 s default subprocess timeout.
"""
from __future__ import annotations
import base64, json, time
from .errors import AuthError

ARM_SCOPE = "https://management.azure.com/.default"

class AzCliTokenProvider:
    def __init__(self, tenant_id: str | None = None, timeout: int = 30):
        try:
            from azure.identity import AzureCliCredential
        except ImportError as e:
            raise AuthError("azure-identity not installed: pip install 'fcat[azure]'") from e
        kw = {"process_timeout": timeout}
        if tenant_id:
            kw["tenant_id"] = tenant_id
        self._cred = AzureCliCredential(**kw)
        self._tok = None

    def token(self) -> str:
        if self._tok is None or self._tok.expires_on - time.time() < 300:
            try:
                self._tok = self._cred.get_token(ARM_SCOPE)
            except Exception as e:  # CredentialUnavailableError, ClientAuthenticationError
                raise AuthError(f"could not get a token from Azure CLI: {type(e).__name__}") from e
        return self._tok.token

    def identity(self) -> dict:
        """Tenant and principal type from token claims (unverified decode, for the run manifest only)."""
        try:
            p = self.token().split(".")[1]
            c = json.loads(base64.urlsafe_b64decode(p + "=" * (-len(p) % 4)))
            return {"tenant_id": c.get("tid"), "principal_type": c.get("idtyp") or ("user" if "upn" in c or "unique_name" in c else "unknown")}
        except Exception:
            return {}
