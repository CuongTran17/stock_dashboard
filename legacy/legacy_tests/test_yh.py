import urllib.request
import json

def test():
    req = urllib.request.Request("https://query1.finance.yahoo.com/v8/finance/chart/FPT.HM", headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            print("YH", data['chart']['result'][0]['meta']['regularMarketPrice'])
    except Exception as e:
        print("ERROR:", e)

test()
