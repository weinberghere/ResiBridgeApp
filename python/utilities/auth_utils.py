import jwt
from configurations.flask_config import FLASK_SECRET_KEY

def generate_auth_header(user_id):
    """
    Generate an authentication header using JWT.

    Parameters:
    - user_id (int): The user's ID.

    Returns:
    - str: The generated authentication header.
    """
    token = jwt.encode({"user_id": user_id}, FLASK_SECRET_KEY, algorithm="HS256")
    return f"Bearer {token}"