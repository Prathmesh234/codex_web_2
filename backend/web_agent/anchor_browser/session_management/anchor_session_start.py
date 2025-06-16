import requests
from dotenv import load_dotenv
import os

def start_anchor_session():

    load_dotenv()
    api_key = os.getenv('ANCHOR_API_KEY')
    if not api_key:
        raise ValueError('ANCHOR_API_KEY not set')

    response = requests.post(
        "https://api.anchorbrowser.io/v1/sessions",
        headers={
            "anchor-api-key": api_key,
            "Content-Type": "application/json",
        },
        json={
          "browser": {
            "headless": {"active": False} # Use headless false to view the browser when combining with browser-use
          }
        }).json()

    # Access the data object from the response
    session_data = response["data"]

    return {
        "data": {
            "id": session_data.get("id"),
            "cdp_url": session_data.get("cdp_url"),
            "live_view_url": session_data.get("live_view_url")
        }
    }

def main():
    session_info = start_anchor_session()
    print("Session Info:", session_info)

if __name__ == "__main__":
    main()
