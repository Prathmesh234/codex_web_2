import requests
import os
from dotenv import load_dotenv
def get_anchor_profile(name: str):
    

    load_dotenv()
    api_key = os.getenv('ANCHOR_API_KEY')
    if not api_key:
        raise ValueError('ANCHOR_API_KEY not set')

    url = f"https://api.anchorbrowser.io/v1/profiles/{name}"
    headers = {"anchor-api-key": api_key}

    response = requests.request("GET", url, headers=headers)

    if response.status_code == 200:
        return response.json()
    elif response.status_code == 404:
        return {"error": {"code": 404, "message": "Profile not found"}}
    elif response.status_code == 500:
        return {"error": {"code": 500, "message": "Unable to retrieve profile"}}
    elif response.status_code == 401:
        return {"error": {"code": 401, "message": "Invalid API key"}}
    else:
        response.raise_for_status()