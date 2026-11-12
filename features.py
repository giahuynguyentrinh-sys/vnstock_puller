import yfinance as yf

def debug_balance_sheet(symbol):
    t = yf.Ticker(f"{symbol}.VN")
    bs = t.balance_sheet

    print("=== 1. Kích thước ===")
    print(bs.shape)

    print("\n=== 2. Các cột (ngày báo cáo) ===")
    print([str(c.date()) for c in bs.columns])

    print("\n=== 3. Các dòng liên quan đến cổ phiếu/vốn ===")
    keys = [i for i in bs.index if any(k in i for k in ["Stock", "Share", "Capital"])]
    print(keys)

    print("\n=== 4. Giá trị các dòng đó theo từng cột ===")
    print(bs.loc[keys].to_string())

    print("\n=== 5. Số ô NaN theo từng cột ===")
    print(bs.isna().sum().to_string())

    print("\n=== 6. Thử lấy thẳng số cổ phiếu từ info ===")
    try:
        print("sharesOutstanding:", t.info.get("sharesOutstanding"))
    except Exception as e:
        print("info lỗi:", e)

debug_balance_sheet("FPT")   # đổi thành mã đang bị lỗi