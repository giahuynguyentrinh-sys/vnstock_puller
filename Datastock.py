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
import time
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

def save_shares(df, table = "shares"):
    with sqlite3.connect("stock.db") as f:
        df.to_sql(table, f, if_exists = "replace", index = False)
def calc_daily_returns(df: pd.DataFrame) -> pd.Series:
    return df.groupby("symbol")["c"].pct_change()

def calc_ma(df,n): #đường trung bình động n phiên 
    return df.groupby("symbol")["c"].transform(lambda s: s.rolling(n).mean())
#transform tính trong từng nhóm, rồi trả về một chuỗi có cùng số dòng để dễ dàng
#gán lại vào sqlite

#ve bieu do 
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
#end ve bieu do
#laythongtintuyahoo
def get_2024_totalshares(symbol):
    try:
        bs = yf.Ticker(f"{symbol}.VN").balance_sheet
        col = [c for c in bs.columns if c.year == 2024]
        if not col:
            print(f"{symbol}: không có cột 2024, cột hiện có: {[str(c.date()) for c in bs.columns]}")
            return None
        return bs.loc["Common Stock", col[0]] / 10000
    except Exception as e:
        print(f"{symbol} error: {type(e).__name__}: {e}")
        return None
def get_all_2024_totalshares(symbols, workers=8):
    shares = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        results = ex.map(get_2024_totalshares, symbols)
        for r in tqdm(results, total=len(symbols)):
            shares.append(r)
    df = pd.DataFrame({"symbol": symbols, "total_shares": shares})
    return df

def cal_market_cap():
    sql_querry = """Select  p.symbol, 
                            p.t,
                            p.c as close_price,
                            p.c * s.total_shares as market_cap
                    from prices as p
                    join shares_2024 as s
                        on p.symbol == s.symbol
                    where p.t = (
                        select max(p2.t)
                        from prices as p2
                        where p2.symbol = s.symbol
                        and p2.t >= "2024-01-01"
                        and p2.t < "2025-01-01"
                    )
    """
    con = sqlite3.connect("stock.db")
    try:
        result = pd.read_sql_query(sql_querry, con =con)
        return result
    finally:
        con.close()                    
x= cal_market_cap()
print(x)