import pandas as pd
import numpy as np
import requests
import matplotlib.pyplot as plt
import sqlite3

URL = "https://kbbuddywts.kbsec.com.vn/iis-server/investment/stocks/{symbol}/data_day"
HEADERS = {"User-Agent": "Mozilla/5.0"}
symbols = ["FPT", "POW", "ACB", "VCB","BID","VIC"]
def get_kbs(symbol, sdate, edate):
    r = requests.get(
        URL.format(symbol=symbol),
        params={"sdate": sdate, "edate": edate},
        headers=HEADERS,
        timeout=15, #timeout 15 giây quá thời gian này raise error
    )
    print(r.status_code) #dòng cho thấy debug
    r.raise_for_status() #lỗi ném ngay lỗi 
    return pd.DataFrame(r.json()["data_day"])

def gen_stock(symbol):
    try:
        df= get_kbs(symbol, "01-01-2024","31-12-2024")
    except Exception as error:
        return print(error)
    df["symbol"] = symbol
    df["t"] = pd.to_datetime(df["t"])
    df = df.set_index("t").sort_index()
    #sort_index() để đảm bảo ngày xếp tăng dần, vì pct_change 
    #tính theo thứ tự dòng, nên nếu dữ liệu xếp ngược thì lợi suất sẽ bị đảo dấu.    
    return df 

def gen_multiple_stocks():
    global symbols
    cr_stock = {}
    for symbol in symbols:
        try:
            stock = get_kbs(symbol, "01-01-2024","31-12-2024")
        except Exception as error:
            print(error)
            continue
        cr_stock[symbol] = stock
    all_df = pd.concat(cr_stock, names =["symbol"]).reset_index(level="symbol").reset_index(drop= True)
    all_df["t"] = pd.to_datetime(all_df["t"])
    all_df = all_df.set_index("t").sort_index()
    #sort_index() để đảm bảo ngày xếp tăng dần, vì pct_change 
    #tính theo thứ tự dòng, nên nếu dữ liệu xếp ngược thì lợi suất sẽ bị đảo dấu.    
    return all_df     

def time_datetime(df):
    df["t"] = pd.to_datetime(df["t"])
    return df.sort_values("t").reset_index(drop=True)

def sqlitesave(all_df):
    with sqlite3.connect("stock.db") as f:
        all_df.to_sql("prices", f, if_exists="replace", index = False)    

def calc_daily_returns(df: pd.DataFrame) -> pd.series:
    return df["c"].pct_change() 
    
df = gen_stock("ACB")
v = calc_daily_returns(df)
print(v)

