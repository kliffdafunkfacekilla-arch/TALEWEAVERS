import requests
import json

try:
    # Hit the tactical generate endpoint and capture full response
    r = requests.get('http://127.0.0.1:8000/tactical/generate?player_name=Burt', timeout=10)
    print("STATUS:", r.status_code)
    try:
        print("JSON:", json.dumps(r.json(), indent=2))
    except:
        print("BODY:", r.text)
except Exception as e:
    print("CONNECTION ERROR:", e)
