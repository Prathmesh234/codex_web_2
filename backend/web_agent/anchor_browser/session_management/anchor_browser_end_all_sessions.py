import requests
import os
from dotenv import load_dotenv

def end_all_anchor_sessions():
    

    load_dotenv()
    api_key = os.getenv('ANCHOR_API_KEY')
    if not api_key:
        raise ValueError('ANCHOR_API_KEY not set')

    url = "https://api.anchorbrowser.io/v1/sessions/all"
    headers = {"anchor-api-key": api_key}

    response = requests.request("DELETE", url, headers=headers)

    if response.status_code == 200:
        return {"data": {"status": "success"}}
    else:
        response.raise_for_status()

def main():
    result = end_all_anchor_sessions()
    print("Result:", result)

if __name__ == "__main__":
    main()