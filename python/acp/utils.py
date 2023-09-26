import requests
import os

def get_acp_token():
    api_id = os.getenv("ACP_API_ID")
    api_key = os.getenv("ACP_API_KEY")
    acp_token_url = "https://api.universalservice.org/auth/token"
    response = requests.post(acp_token_url, auth=(api_id, api_key))
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        return None