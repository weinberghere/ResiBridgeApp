import requests
from configurations.splynx_config import SPLYNX_BASE_URL, SPLYNX_KEY


def fetch_splynx_data(endpoint):
    """
    Fetch data from Splynx based on the provided endpoint.
    """
    headers = {
        "Authorization": f"Bearer {SPLYNX_KEY}",
        "Content-Type": "application/json"
    }
    response = requests.get(f"{SPLYNX_BASE_URL}/{endpoint}", headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        # Log or print the error for debugging
        print(f"Error fetching Splynx data for endpoint {endpoint}. Status code: {response.status_code}")
        return None
