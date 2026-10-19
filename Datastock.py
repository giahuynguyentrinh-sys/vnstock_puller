import pandas as pd
import numpy as np
import requests
import matplotlib.pyplot as plt
import sqlite3 as sqlite3
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from symbol_list import symbols
import matplotlib.dates as mdates
import yfinance as yf
URL = "https://kbbuddywts.kbsec.com.vn/iis-server/investment/stocks/{symbol}/data_day"
HEADERS = {"User-Agent": "Mozilla/5.0"}
session = requests.Session()
session.headers.update(HEADERS)

def get_kbs(symbol, sdate, edate):
    r = session.get(URL.format(symbol=symbol),
                    params={"sdate": sdate, "edate": edate}, timeout=15)
    r.raise_for_status()
    return pd.DataFrame(r.json()["data_day"])

def fetch(symbol):
    try:
        df = get_kbs(symbol, "01-01-2024", "31-12-2024")
    except Exception as e:
        return symbol, None, str(e)
    if df.empty:
        return symbol, None, "rỗng"
    df["symbol"] = symbol
    return symbol, df, None

def gen_multiple_stocks(symbols, workers=8):
    with ThreadPoolExecutor(max_workers=workers) as ex:
        results = list(tqdm(ex.map(fetch, symbols), total=len(symbols)))
    frames = [df for _, df, err in results if df is not None]
    failed = [(s, err) for s, df, err in results if df is None]
    all_df = pd.concat(frames, ignore_index=True)
    all_df["t"] = pd.to_datetime(all_df["t"])
    all_df = all_df.sort_values(["symbol", "t"]).set_index("t")
    return all_df, failed    

def time_datetime(df):
    df["t"] = pd.to_datetime(df["t"])
    return df.sort_values("t").reset_index(drop=True)

def sqlitesave(all_df):
    with sqlite3.connect("stock.db") as f:
        all_df.to_sql("prices", f, if_exists="replace", index = True) 

def calc_daily_returns(df: pd.DataFrame) -> pd.Series:
    return df.groupby("symbol")["c"].pct_change()

def calc_ma(df,n): #đường trung bình động n phiên 
    return df.groupby("symbol")["c"].transform(lambda s: s.rolling(n).mean())
#transform tính trong từng nhóm, rồi trả về một chuỗi có cùng số dòng để dễ dàng
#gán lại vào sqlite
def linechart_price(t,df,title,xlabel,ylabel):
    fig, ax = plt.subplots(figsize=(12, 5))
    t = pd.to_datetime(t)
    ax.plot(t, df)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.xaxis.set_major_locator(mdates.MonthLocator())          # mỗi tháng 1 nhãn
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
    ax.grid(alpha=0.3)
    fig.tight_layout()
    plt.show()
keep_no_yahoo = ['BCG','HBC','HNG','ITA','BSC','NTP','PMC','NTH','HGM']
yahoo_symbols = [s for s in symbols if s not in keep_no_yahoo]

def get_total_shares(symbol):
    try:
        t = yf.Ticker(f"{symbol}.VN")
        return t.info.get('sharesOutstanding')
    except Exception as e:
        print(f"{symbol} error: {e}")
        return None
def get_all_totalshares(symbols):
    all_df = {}
    for symbol in symbols:
        try:
            total_share = get_total_shares(symbol)
            all_df[symbol] = total_share
        except Exception as e:
            print(f"{symbol} error: {e}")
    return all_df
all_df,failed = gen_multiple_stocks(symbols)
all_df["value"] = all_df["c"] * all_df["v"]          # giá trị giao dịch mỗi dòng (đồng)

liq = all_df.groupby("symbol")["value"].median()     # mỗi mã lấy 1 con số: giá trị giao dịch/ngày điển hình
print((liq / 1e9).describe())                        # xem phân bố, đơn vị tỷ đồng

NGUONG = 10e9                                        # 10 tỷ đồng/ngày, chỉnh sau khi xem phân bố
good = liq[liq >= NGUONG].index
all_df = all_df[all_df["symbol"].isin(good)]

print(len(good), "mã còn lại")
            