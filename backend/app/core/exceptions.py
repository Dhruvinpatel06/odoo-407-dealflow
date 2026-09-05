from typing import Any, Optional


class DealFlowException(Exception):
    """Base exception for DealFlow360 application."""

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        details: Optional[Any] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details


class ResourceNotFoundError(DealFlowException):
    """Raised when an aggregate or entity cannot be found."""

    def __init__(self, message: str = "Resource not found", details: Optional[Any] = None):
        super().__init__(message=message, status_code=404, details=details)


class UnauthorizedError(DealFlowException):
    """Raised when authentication credentials are missing or invalid."""

    def __init__(self, message: str = "Authentication required", details: Optional[Any] = None):
        super().__init__(message=message, status_code=401, details=details)


class ForbiddenError(DealFlowException):
    """Raised when the authenticated user does not have permission."""

    def __init__(self, message: str = "Permission denied", details: Optional[Any] = None):
        super().__init__(message=message, status_code=403, details=details)


class InvalidStateTransitionError(DealFlowException):
    """Raised when an illegal workflow state transition is attempted."""

    def __init__(self, message: str = "Invalid state transition", details: Optional[Any] = None):
        super().__init__(message=message, status_code=400, details=details)


class BusinessRuleViolationError(DealFlowException):
    """Raised when a core commercial or validation rule fails."""

    def __init__(self, message: str = "Business rule violation", details: Optional[Any] = None):
        super().__init__(message=message, status_code=422, details=details)


class InsufficientInventoryError(DealFlowException):
    """Raised when stock allocation exceeds available inventory."""

    def __init__(self, message: str = "Insufficient inventory available", details: Optional[Any] = None):
        super().__init__(message=message, status_code=400, details=details)


class ApprovalRequiredError(DealFlowException):
    """Raised when a business action is blocked awaiting policy approval."""

    def __init__(self, message: str = "Action requires approval", details: Optional[Any] = None):
        super().__init__(message=message, status_code=400, details=details)


class BillingError(DealFlowException):
    """Raised when an invoice, payment, or schedule operation fails."""

    def __init__(self, message: str = "Billing operation failed", details: Optional[Any] = None):
        super().__init__(message=message, status_code=400, details=details)
