import urllib.request
import json
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

def test_api():
    url = "https://services.entrade.com.vn/dnse-market-data-service/api/stocks/FPT"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            print("STOCK", json.dumps(data, indent=2))
    except Exception as e:
        print("STOCK ERROR", e)
        
test_api()
