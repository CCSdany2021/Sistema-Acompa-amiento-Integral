import requests
try:
    r = requests.get("http://127.0.0.1:8002/dashboard", allow_redirects=False)
    print(f"Status: {r.status_code}")
    print(f"Content Start: {r.text[:2000]}")
except Exception as e:
    print(f"Error: {e}")
