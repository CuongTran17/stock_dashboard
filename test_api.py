import requests
import pandas as pd

def test_finfo():
    headers = {'User-Agent': 'Mozilla/5.0'}
    # Try different endpoints used by vnstock for macro
    url = "https://finfo-api.vndirect.com.vn/v4/interbank_rates?q=date:gte:2025-08-31~date:lte:2026-03-31"
    response = requests.get(url, headers=headers)
    print("interbank_rates status:", response.status_code)
    if response.status_code == 200:
        print(response.json())
        return

test_finfo()
