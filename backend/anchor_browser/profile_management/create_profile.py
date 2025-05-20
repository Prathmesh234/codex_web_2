import requests
import os
from dotenv import load_dotenv
def create_anchor_profile(name: str, description: str, session_id: str = None, store_cache: bool = True):
    

    load_dotenv()
    api_key = os.getenv('ANCHOR_API_KEY')
    if not api_key:
        raise ValueError('ANCHOR_API_KEY not set')

    url = "https://api.anchorbrowser.io/v1/profiles"

    payload = {
        "name": name,
        "description": description,
        "source": "session",
        "session_id": session_id,
        "store_cache": store_cache
    }

    headers = {
        "anchor-api-key": api_key,
        "Content-Type": "application/json"
    }

    response = requests.request("POST", url, json=payload, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()