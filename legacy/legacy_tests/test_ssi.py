import urllib.request
import json
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

def test():
    req = urllib.request.Request("https://iboard-query.ssi.com.vn/v1/api/stock/actualQuotes", headers={"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"})
    try:
        req.get_method = lambda: 'POST'
        req.data = json.dumps({"stockIds":["FPT", "VCB", "HPG"]}).encode()
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            print(json.dumps(data, indent=2))
    except Exception as e:
        print("ERROR:", e)

test()
