"""Custom exceptions for the cargo loader module."""


class CargoLoadError(Exception):
    """Base exception for cargo loading failures."""

    def __init__(self, message: str = "Failed to load cargo"):
        self.message = message
        super().__init__(self.message)


class DatabasePersistenceError(CargoLoadError):
    """Exception raised when cargo persistence to database fails."""

    def __init__(self, message: str = "Failed to persist cargo to database", original_error: Exception | None = None):
        self.original_error = original_error
        super().__init__(message)
