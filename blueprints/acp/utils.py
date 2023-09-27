import requests
import os
import functools
from flask import session
import os
from datetime import datetime, timedelta
from configurations.acp_config import ACP_API_ID, ACP_API_KEY, ACP_TOKEN_URL


def requires_token(func):
    @functools.wraps(func)
    def decorated_function(*args, **kwargs):
        # Check if there's an existing token and it's still valid
        token = session.get('acp_access_token')
        token_expiry = session.get('acp_token_expiry', datetime.now() - timedelta(hours=1))

        if not token or datetime.now() >= token_expiry:
            if not fetch_new_token():
                return "Failed to retrieve ACP token", 500

        return func(*args, **kwargs)

    return decorated_function


def fetch_new_token():
    headers = {"Content-Type": "application/json"}
    response = requests.post(ACP_TOKEN_URL, headers=headers, auth=(ACP_API_ID, ACP_API_KEY))

    if response.status_code == 200:
        response_data = response.json()
        session["access_token"] = response_data["access_token"]
        session["token_expiry"] = (datetime.now() + timedelta(hours=1)).timestamp()


def get_acp_token():
    api_id = os.getenv("ACP_API_ID")
    api_key = os.getenv("ACP_API_KEY")
    acp_token_url = os.getenv("ACP_TOKEN_URL")
    response = requests.post(acp_token_url, auth=(api_id, api_key))
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        return None
