import requests
try:
    resp = requests.post("http://localhost:8000/combat/load", json={"character_name": "Burt"})
    print("STATUS:", resp.status_code)
    print("RESPONSE:", resp.text)
except Exception as e:
    print("ERROR:", e)
