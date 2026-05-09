import requests
import time

API_URL = "http://localhost:8000/api"

def test_bot_signal():
    try:
        # Test GET
        r = requests.get(f"{API_URL}/bot-signal?src=test_script&ts={int(time.time())}")
        print(f"GET /api/bot-signal: {r.status_code} - {r.json()}")
        
        # Test POST
        r = requests.post(f"{API_URL}/bot-signal", json={"src": "test_script_post"})
        print(f"POST /api/bot-signal: {r.status_code} - {r.json()}")
    except Exception as e:
        print(f"Error testing bot signal: {e}")

if __name__ == "__main__":
    test_bot_signal()
