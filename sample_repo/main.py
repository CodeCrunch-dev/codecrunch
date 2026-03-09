"""Main entry point for the web application."""

from utils import log, format_response
from models import User, fetch_user


def main():
    """Run the application."""
    log("Starting application...")
    user = fetch_user(1)
    if user:
        log(f"Loaded user: {user.username}")
        print(format_response(user.to_dict()))


if __name__ == "__main__":
    main()
