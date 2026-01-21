import re


def generate_user_id(first_name: str, last_name: str) -> str:
    """Generate a consistent user_id from first+last name."""
    user_id = re.sub(r"\W+", "", f"{first_name}{last_name}".lower())
    return user_id if user_id else "default_user"
