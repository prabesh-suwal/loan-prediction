class LoanSystemException(Exception):
    """Base exception for loan system."""
    pass

class ValidationError(LoanSystemException):
    """Raised when input validation fails."""
    pass

class PredictionError(LoanSystemException):
    """Raised when ML prediction fails."""
    pass

class ModelNotLoadedError(LoanSystemException):
    """Raised when ML model is not loaded."""
    pass

class DatabaseError(LoanSystemException):
    """Raised when database operations fail."""
    pass
