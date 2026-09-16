"""Errors contain only fixed messages and allowlisted numeric metadata."""

from decimal import Decimal


class EngieError(Exception):
    """Base error for the read-only client."""


class PayloadError(EngieError, ValueError):
    """A response does not match the verified data contract."""


class AuthenticationError(EngieError):
    """An interactive login is required."""


class TransportError(EngieError):
    """The service could not be reached."""


class ServiceError(EngieError):
    def __init__(
        self,
        status: int,
        error_code: int | None = None,
        detailed_code: Decimal | None = None,
    ) -> None:
        super().__init__(f"ENGIE request failed (HTTP {status})")
        self.status = status
        self.error_code = error_code
        self.detailed_code = detailed_code


class RateLimitError(EngieError):
    def __init__(self, retry_after: float) -> None:
        super().__init__("ENGIE rate limit reached; wait before retrying")
        self.retry_after = retry_after
