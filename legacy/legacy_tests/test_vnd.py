import urllib.request
import json
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

def test():
    req = urllib.request.Request("https://finfo-api.vndirect.com.vn/v4/stock_prices?sort=date&q=code:FPT", headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            print(json.dumps(data, indent=2))
    except Exception as e:
        print("ERROR:", e)

test()
