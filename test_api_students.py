import requests

def test_api():
    # Attempting to hit the local server with a test course
    url = "http://localhost:8001/api/students?course=JR01"
    
    # We'll probably get 401 Unauthorized if auth is active
    # but we can check if it at least returns JSON (401 is JSON)
    try:
        response = requests.get(url)
        print("Status Code:", response.status_code)
        try:
            print("Response JSON:", response.json())
        except:
            print("Response Text (Not JSON):", response.text[:200])
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_api()
