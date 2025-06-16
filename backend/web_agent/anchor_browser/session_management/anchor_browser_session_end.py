import requests
import os
from dotenv import load_dotenv


def end_anchor_session(session_id: str):
  

    load_dotenv()
    api_key = os.getenv('ANCHOR_API_KEY')
    if not api_key:
        raise ValueError('ANCHOR_API_KEY not set')

    url = f"https://api.anchorbrowser.io/v1/sessions/{session_id}"
    headers = {"anchor-api-key": api_key}

    response = requests.request("DELETE", url, headers=headers)

    if response.status_code == 200:
        return {"data": {"status": "success"}}
    else:
        response.raise_for_status()