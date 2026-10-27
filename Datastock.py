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
from datetime import date, time
import json
from ta.momentum import RSIIndicator
from ta.trend import MACD
import pandas as pd


indexs = ["VNINDEX","VN30", "VN100", "UPCOMINDEX", "HNX30", "HNXINDEX"]
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 200)
HEADERS = {"User-Agent": "Mozilla/5.0"}
session = requests.Session()
session.headers.update(HEADERS)

def get_kbs(symbol, sdate, edate):
    URL = "https://kbbuddywts.kbsec.com.vn/iis-server/investment/stocks/{symbol}/data_day"
    r = session.get(URL.format(symbol=symbol),
                    params={"sdate": sdate, "edate": edate}, timeout=15)
    r.raise_for_status()
    return pd.DataFrame(r.json()["data_day"])

def fetch(symbol, sdate, edate):    
    try:
        df = get_kbs(symbol, sdate, edate)
    except Exception as e:
        return symbol, None, str(e)
    if df.empty:
        return symbol, None, "rỗng"
    df["symbol"] = symbol
    return symbol, df, None

def gen_multiple_stocks(symbols, sdate, edate, workers=8):
    with ThreadPoolExecutor(max_workers=workers) as ex:
        results = list(tqdm(
            ex.map(lambda s: fetch(s, sdate, edate), symbols),
            total = len(symbols)))
    frames = [df for _, df, err in results if df is not None]
    failed = [(s, err) for s, df, err in results if df is None]
    all_df = pd.concat(frames, ignore_index=True)
    all_df = all_df.sort_values(["symbol", "t"])
    return all_df, failed    

def time_datetime(df):
    df["t"] = pd.to_datetime(df["t"])
    return df.sort_values("t").reset_index(drop=True)

#savesqlite 

def save_sqlite(df, table = "shares"):
    with sqlite3.connect("stock.db") as f:
        df.to_sql(table, f, if_exists = "replace", index = False)
def append_sqlite(df, table):
    with sqlite3.connect("stock.db") as f:
        df.to_sql(table, f, if_exists = "append", index = False)

def calc_daily_returns(df: pd.DataFrame) -> pd.Series:
    return df.groupby("symbol")["c"].pct_change()
def calc_ma(df,n): #đường trung bình động n phiên 
    return df.groupby("symbol")["c"].transform(lambda s: s.rolling(n).mean())
#transform tính trong từng nhóm, rồi trả về một chuỗi có cùng số dòng để dễ dàng
#gán lại vào sqlite
def cal_market_cap(sdate, edate):
    sql_querry = f"""Select  p.symbol, 
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
                        and p2.t >= ?
                        and p2.t < ?
                    )
    """
    con = sqlite3.connect("stock.db")
    try:
        result = pd.read_sql_query(sql_querry, con =con, params = (sdate, edate))
        return result
    finally:
        con.close()
def get_recent_prices(symbol, n=100):
    with sqlite3.connect("stock.db") as conn:
        query = """
            SELECT t, symbol, c FROM data_2026
            WHERE symbol = ?
            ORDER BY t DESC
            LIMIT ?
        """
        df = pd.read_sql_query(query, conn, params=(symbol, n))
    df["t"] = pd.to_datetime(df["t"])
    return df.sort_values("t").reset_index(drop=True)
def calc_rsi(symbol, n =100):
    df = get_recent_prices(symbol, n)
    df["rsi"] = RSIIndicator(df["c"], window = 14).rsi()
    return df
def cal_macd(symbol, n= 100):
    df = get_recent_prices(symbol, n)
    macd_indicator = MACD(df["c"])
    df["macd"] = macd_indicator.macd()
    df["signal"] = macd_indicator.macd_signal()
    df["Histogram"] = macd_indicator.macd_diff()
    return df
    
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
def get_year_totalshares(symbol,year):
    try:
        bs = yf.Ticker(f"{symbol}.VN").balance_sheet
        col = [c for c in bs.columns if c.year == year]
        if not col:
            print(f"{symbol}: không có cột {year}, cột hiện có: {[str(c.date()) for c in bs.columns]}")
            return None
        return bs.loc["Common Stock", col[0]] / 10000
    except Exception as e:
        print(f"{symbol} error: {type(e).__name__}: {e}")
        return None
def get_all_totalshares(symbols, year, workers=8):
       with ThreadPoolExecutor(max_workers=workers) as ex:
           results = ex.map(lambda s: get_year_totalshares(s, year), symbols)
           shares = list(tqdm(results, total=len(symbols)))
       return pd.DataFrame({"symbol": symbols, "total_shares": shares})

def topforeigntrade(n): #limit = 100 #update daily
    url = "https://kbbuddywts.kbsec.com.vn/iis-server/investment/rtranking/foreignTotal"
    r = requests.get(url, params = {"top": n}, headers = HEADERS, timeout = 10)
    r.raise_for_status()
    df = pd.DataFrame(r.json())
    df["date"] = date.today().isoformat()
    df = df.rename(columns= {
        "SB": "symbol", "FB": "foreign_buy", "FS": "foreign_sell", "FT": "foreign_total" })
    return df[["date","symbol","foreign_buy", "foreign_sell", "foreign_total"]]
    
def topntrade(n): #limit = 100
    url = "https://kbbuddywts.kbsec.com.vn/iis-server/investment/rtranking/volume"
    r = requests.get(url, params = {"which": 1, "top": n}, headers = HEADERS, timeout = 10)
    r.raise_for_status()
    df = pd.DataFrame(r.json())
    df["date"] = date.today().isoformat()
    df = df.rename(columns = {
        "VAL": "value", "SB": "symbol", "date": "date", "ORIGINAL_VAL": "original_value",
    "CL": "ceiling", "FL": "floor", "RE": "ref_price" 
    })
    return df[["date", "symbol", "value", "original_value", "floor", "ceiling", "ref_price"]]

def volume_ratio(symbol, n):
    conn = sqlite3.connect("stock.db")
    query = """
    select v from data_2026
    where symbol = ?
    order by t desc
    limit ?    
    """
    df = pd.read_sql_query(query, conn, params = (symbol, n+1))
    conn.close()
    if len(df) < n +1:
        return None
    newest = df["v"].iloc[0]
    avg = df["v"].iloc[1:].mean()
    return newest/avg * 100

def get_index_info_day(index, sdate, edate):
    url = f"https://kbbuddywts.kbsec.com.vn/iis-server/investment/index/{index}/data_day"
    r = session.get(url, params={"sdate": sdate, "edate": edate}, timeout=10)
    r.raise_for_status()
    data = r.json()
    df = pd.DataFrame(data["data_day"])
    if df.empty:                                   # tên mã sai hoặc khoảng ngày không có dữ liệu
        return df
    for col in ["o", "h", "l", "c", "v"]:
        df[col] = pd.to_numeric(df[col])           # dòng đầu là chuỗi, các dòng sau là số
    df = time_datetime(df)                         # đổi t sang ngày, sắp tăng dần
    df["t"] = df["t"].dt.normalize()               # bỏ đuôi 07:00
    df["symbol"] = data["symbol"]
    return df[["t", "symbol", "o", "h", "l", "c", "v"]]
for index in indexs:
    x = get_index_info_day(index, "26-10-2024", "26-10-2026")
    save_sqlite(x, "index_prices")