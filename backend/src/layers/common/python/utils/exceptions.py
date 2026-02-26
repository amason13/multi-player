"""Custom exceptions for multi-player application."""


class MultiPlayerException(Exception):
    """Base exception for multi-player application."""
    
    def __init__(self, message: str, status_code: int = 400, error_code: str = "INTERNAL_ERROR"):
        """Initialize exception.
        
        Args:
            message: Error message
            status_code: HTTP status code
            error_code: Application error code
        """
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)


class ValidationError(MultiPlayerException):
    """Raised when input validation fails."""
    
    def __init__(self, message: str):
        super().__init__(message, status_code=400, error_code="VALIDATION_ERROR")


class NotFoundError(MultiPlayerException):
    """Raised when resource is not found."""
    
    def __init__(self, message: str):
        super().__init__(message, status_code=404, error_code="NOT_FOUND")


class UnauthorizedError(MultiPlayerException):
    """Raised when user is not authorized."""
    
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status_code=401, error_code="UNAUTHORIZED")


class ConflictError(MultiPlayerException):
    """Raised when resource already exists."""
    
    def __init__(self, message: str):
        super().__init__(message, status_code=409, error_code="CONFLICT")
