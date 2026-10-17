class FcatError(Exception):
    pass
class BlockedRequest(FcatError):
    """Raised when a request would break the read-only rule."""
class IncompleteResult(FcatError):
    """Raised when a result set is truncated and cannot be paged. Never ignore silently."""
class AuthError(FcatError):
    pass
