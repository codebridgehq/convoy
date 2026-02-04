"""Custom exceptions for the cargo tracker module."""


class CargoTrackingError(Exception):
    """Base exception for cargo tracking failures."""

    def __init__(self, message: str = "Failed to track cargo"):
        self.message = message
        super().__init__(self.message)


class CargoNotFoundError(CargoTrackingError):
    """Exception raised when cargo is not found in the database."""

    def __init__(self, cargo_id: str):
        self.cargo_id = cargo_id
        super().__init__(f"Cargo not found: {cargo_id}")
