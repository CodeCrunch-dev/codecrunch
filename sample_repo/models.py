"""Data models for the application."""

from database import get_connection


class User:
    """Represents a user in the system."""

    def __init__(self, id: int, username: str, email: str):
        self.id = id
        self.username = username
        self.email = email

    def to_dict(self):
        """Convert user to dictionary."""
        return {"id": self.id, "username": self.username, "email": self.email}


def fetch_user(user_id: int) -> User | None:
    """Fetch a user by ID from the database."""
    conn = get_connection()
    # Simplified - would query DB
    return User(user_id, "demo", "demo@example.com")
