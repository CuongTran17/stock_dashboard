import requests
import json

def test():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }
    url = "https://finfo-api.vndirect.com.vn/v4/stock_prices?sort=date&q=code:FPT"
    try:
        r = requests.get(url, headers=headers)
        print(json.dumps(r.json(), indent=2))
    except Exception as e:
        print("ERROR:", e)

test()
