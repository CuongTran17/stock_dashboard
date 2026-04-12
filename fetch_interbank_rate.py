import warnings
import pandas as pd
import requests

def get_interbank_rate_vnstock(start_date, end_date):
    """
    Hàm này sử dụng thư viện vnstock phiên bản cũ (<= 0.2.28) để lấy lãi suất liên ngân hàng.
    Lưu ý: Từ phiên bản vnstock nâng cấp thành vnai (2.x trở lên), các hàm dữ liệu vĩ mô 
    (bao gồm lãi suất liên ngân hàng) đã bị lược bỏ do API nguồn (VNDirect) không còn ổn định.
    
    Để chạy được hàm này, bạn cần cài đặt bản cũ:
    pip install vnstock==0.2.28
    """
    try:
        from vnstock import money_market
        # Hoặc một số phiên bản sử dụng macro_activity
        # df = macro_activity('interbank_rate')
        print("Vui lòng tham khảo tài liệu của vnstock bản 0.2.28 cho tên hàm chính xác.")
    except ImportError:
        print("vnstock hiện tại không hỗ trợ module macro/money_market.")

def get_interbank_rate_api(start_date, end_date):
    """
    Đây là cách truy cập trực tiếp API cung cấp dữ liệu (tương tự vnstock đã từng sử dụng).
    """
    url = f"https://finfo-api.vndirect.com.vn/v4/macro_parameters?q=itemCode:INTERBANK_OVERNIGHT~date:gte:{start_date}~date:lte:{end_date}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json().get('data', [])
            if not data:
                print("Không có dữ liệu trả về từ API.")
                return pd.DataFrame()
                
            df = pd.DataFrame(data)
            # Lọc các cột cần thiết
            df = df[['date', 'value', 'itemCode']]
            df.columns = ['Ngày', 'Lãi suất (%)', 'Kỳ hạn']
            df['Ngày'] = pd.to_datetime(df['Ngày'])
            df = df.sort_values('Ngày')
            return df
        else:
            print(f"Lỗi truy cập API: {response.status_code}")
            return pd.DataFrame()
    except Exception as e:
        print(f"Lỗi kết nối: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    start_date = "2025-08-31"
    end_date = "2026-03-31"
    
    print(f"Bắt đầu kéo dữ liệu lãi suất liên ngân hàng qua đêm từ {start_date} đến {end_date}...")
    
    # Do vnstock mới không hỗ trợ, script sẽ dùng trực tiếp API 
    df_rates = get_interbank_rate_api(start_date, end_date)
    
    if not df_rates.empty:
        csv_filename = "lai_suat_lien_ngan_hang_qua_dem.csv"
        df_rates.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        print(f"Đã lưu thành công dữ liệu vào file: {csv_filename}")
        print(df_rates.head())
    else:
        print("Kéo dữ liệu thất bại. Nguồn cấp dữ liệu (API) có thể đang bị lỗi hoặc hạn chế truy cập.")
        print("Bạn có thể cần phải tra cứu thủ công từ sbv.gov.vn hoặc sử dụng dữ liệu từ FiinTrade/WiChart.")
