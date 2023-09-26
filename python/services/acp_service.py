import requests
from config import ACP_BASE_URL, ACP_API_KEY

def fetch_acp_data(action):
    """
    Fetch data from ACP based on the provided action.
    """
    headers = {
        "Authorization": f"Bearer {ACP_API_KEY}",
        "Content-Type": "application/json"
    }
    response = requests.get(f"{ACP_BASE_URL}/{action}", headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        # Log or print the error for debugging
        print(f"Error fetching ACP data for action {action}. Status code: {response.status_code}")
        return None
