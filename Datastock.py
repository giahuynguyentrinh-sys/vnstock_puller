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
from datetime import date, time, timedelta
import json
from ta.momentum import RSIIndicator
from ta.trend import MACD
import pandas as pd
start_date = date(2024,1,1)
indexs = ["VNINDEX","VN30", "VN100", "UPCOMINDEX", "HNX30"]
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
    all_df = to_datetime(all_df)
    all_df = all_df.sort_values(["symbol", "t"])
    return all_df, failed

def to_datetime(df):
    df["t"] = pd.to_datetime(df["t"]).dt.normalize()
    cols = [c for c in ["o", "h", "l", "c", "v"] if c in df.columns]
    df[cols] = df[cols].astype(float)
    return df

#savesqlite 

def save_append(df, table, keys=("symbol", "t")):
    # Bước 1: không có dữ liệu thì thoát
    if df is None:
        return 0
    if df.empty:
        return 0

    # Bước 2: kiểm tra df có đủ cột khóa
    for k in keys:
        if k not in df.columns:
            raise ValueError(f"{table}: df thiếu cột {k}")

    df = df.copy()

    # Bước 3: tạo cột "_key" cho df, ví dụ "VNM|2026-10-29 00:00:00"
    key = None
    for k in keys:
        if pd.api.types.is_datetime64_any_dtype(df[k]):
            part = df[k].dt.strftime("%Y-%m-%d %H:%M:%S")
        else:
            part = df[k].astype(str)
        if key is None:
            key = part
        else:
            key = key + "|" + part
    df["_key"] = key

    conn = sqlite3.connect("stock.db")
    try:
        # Bước 4: bảng chưa tồn tại thì ghi luôn
        co_bang = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table,)
        ).fetchone()
        if co_bang is None:
            df = df.drop_duplicates(subset="_key")
            df = df.drop(columns=["_key"])
            df.to_sql(table, conn, if_exists="append", index=False)
            return len(df)

        # Bước 5: đọc các khóa đã có trong DB
        col_list = ""
        for i in range(len(keys)):
            if i > 0:
                col_list = col_list + ", "
            col_list = col_list + '"' + keys[i] + '"'
        old = pd.read_sql_query(f'SELECT {col_list} FROM "{table}"', conn)

        # Bước 6: tạo "_key" cho dữ liệu cũ theo đúng cách trên
        old_key = None
        for k in keys:
            part = old[k].astype(str)
            if old_key is None:
                old_key = part
            else:
                old_key = old_key + "|" + part

        # Bước 7: bỏ dòng đã có trong DB, bỏ dòng trùng ngay trong df
        da_co = df["_key"].isin(old_key)
        moi = df[~da_co]
        moi = moi.drop_duplicates(subset="_key")
        moi = moi.drop(columns=["_key"])

        # Bước 8: append phần mới
        if moi.empty:
            return 0
        moi.to_sql(table, conn, if_exists="append", index=False)
        return len(moi)
    finally:
        conn.close()
    
       

def calc_daily_returns(df: pd.DataFrame) -> pd.Series:
    return df.groupby("symbol")["c"].pct_change()
def calc_ma(df,n): #đường trung bình động n phiên 
    return df.groupby("symbol")["c"].transform(lambda s: s.rolling(n).mean())
#transform tính trong từng nhóm, rồi trả về một chuỗi có cùng số dòng để dễ dàng
#gán lại vào sqlite
def cal_market_cap(sdate, edate, table1 = "all_data", table2 ="2025_totalshares"):
    sql_querry = f"""Select  p.symbol, 
                            p.t,
                            p.c as close_price,
                            p.c * s.total_shares as market_cap
                    from {table1} as p
                    join "{table2}" as s
                        on p.symbol == s.symbol
                    where p.t = (
                        select max(p2.t)
                        from {table1} as p2
                        where p2.symbol = s.symbol
                        and p2.t >= ?
                        and p2.t < ?
                    )
    """
    con = sqlite3.connect("stock.db")
    try:
        result = pd.read_sql_query(sql_querry, con =con, params = (sdate, edate))
        result = to_datetime(result)
        return result
    finally:
        con.close()

def get_recent_prices(symbol, n=100):
    with sqlite3.connect("stock.db") as conn:
        query = """
            SELECT t, symbol, c FROM all_data
            WHERE symbol = ?
            ORDER BY t DESC
            LIMIT ?
        """
        df = pd.read_sql_query(query, conn, params=(symbol, n))
    df = to_datetime(df)
    return df.sort_values("t")

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

def cal_pe(symbol, table1 = "all_data", table2 = "fundamentals", fid = "12/2025"):
    with sqlite3.connect("stock.db") as con:
        query = f"""
        Select  data.symbol, 
                data.t,
                data.c / funda.EPS  as pe
        from {table1} as data
        join {table2} as funda
        on funda.SB = data.symbol 
        where data.symbol = ? and funda.FID = ? AND funda.EPS > 0
        order by data.t desc limit 1
        """
        df = pd.read_sql_query(query, con, params = (symbol,fid))
        if df.empty:
            return
    return df[["t","FID","symbol","pe"]]

def cal_pb(symbol,table1 ="all_data", table2 = "fundamentals", fid = "12/2025"):
    with sqlite3.connect("stock.db") as con:
            query = f"""
            Select  data.symbol, 
                    data.t,
                    data.c / funda.BVPS  as pb
            from {table1} as data
            join {table2} as funda
            on funda.SB = data.symbol 
            where data.symbol = ? and funda.FID = ? AND funda.EPS > 0
            order by data.t desc limit 1
            """
            df = pd.read_sql_query(query, con, params = (symbol,fid))
            if df.empty:
                return
    return df[["t","FID","symbol","pb"]]
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
    df["t"] = pd.to_datetime(date.today())
    df = df.rename(columns= {
        "SB": "symbol", "FB": "foreign_buy", "FS": "foreign_sell", "FT": "foreign_total" })
    return df[["t","symbol","foreign_buy", "foreign_sell", "foreign_total"]]
    
def topntrade(n): #limit = 100
    url = "https://kbbuddywts.kbsec.com.vn/iis-server/investment/rtranking/volume"
    r = requests.get(url, params = {"which": 1, "top": n}, headers = HEADERS, timeout = 10)
    r.raise_for_status()
    df = pd.DataFrame(r.json())
    df["t"] = pd.to_datetime(date.today())
    df = df.rename(columns = {
        "VAL": "value", "SB": "symbol", "date": "t", "ORIGINAL_VAL": "original_value",
    "CL": "ceiling", "FL": "floor", "RE": "ref_price" 
    })
    df["value"] = pd.to_numeric(df["value"])
    df["original_value"] = pd.to_numeric(df["original_value"])
    return df[["t", "symbol", "value", "original_value", "floor", "ceiling", "ref_price"]]

def volume_ratio(symbol, n):
    conn = sqlite3.connect("stock.db")
    query = """
    select t,symbol,v from all_data
    where symbol = ?
    order by t desc
    limit ?    
    """ 
    df = pd.read_sql_query(query, conn, params = (symbol, n+1))
    df = to_datetime(df)
    conn.close()
    if len(df) <= n:
        return None
    newest = df["v"].iloc[0]
    avg = df["v"].iloc[1:].mean()
    return newest/avg * 100

def get_index_info_day(index, sdate, edate): #update_daily #append
    url = f"https://kbbuddywts.kbsec.com.vn/iis-server/investment/index/{index}/data_day"
    r = session.get(url, params= {"sdate": sdate, "edate": edate}, headers = HEADERS, timeout = 10)
    r.raise_for_status()
    data = r.json()
    df = pd.DataFrame(data["data_day"])
    if not data.get("data_day"):
        return pd.DataFrame(df)
    df = to_datetime(df)
    df["symbol"] = data["symbol"]
    return df

def find_missing(symbol, table):
    today = date.today()
    border = 14
    with sqlite3.connect("stock.db") as conn:
        query = f"""
        select * from {table}
        where symbol = ?
        order by t asc
        """
        df = pd.read_sql_query(query, conn, params= (symbol,),parse_dates=["t"])
    if df.empty:
        return [((start_date), today)]
    days = df["t"].dt.normalize()
    missing = []
    gap = days.diff().dt.days
    for i in gap[gap > border].index:
        before = days[i - 1].date()
        after = days[i].date()
        missing.append((before + timedelta(days=1), after- timedelta(days=1))) 
    last = days.iloc[-1].date()
    if last < today:
        missing.append((last+ timedelta(days=1), today))
    return missing


def findmissing_all(symbols, table):
    result = {}
    for symbol in symbols:
        missing = find_missing(symbol, table)
        if missing:
            result[symbol] = missing
    return result

def auto_update_all_data(symbols, table):
    for symbol, ranges in findmissing_all(symbols, table).items():
        for s, e in ranges:
            try:
                x = get_kbs(symbol, s.strftime("%d-%m-%Y"), e.strftime("%d-%m-%Y"))
                if not x.empty:
                    x["symbol"] = symbol
                    save_append(to_datetime(x), table)
            except Exception as E:
                print(f"{symbol}: error {E}")
def auto_update_all_index_info(indexs, table):
    for index, ranges in findmissing_all(indexs, table).items():
            for s, e in ranges:
                try:
                    x = get_index_info_day(index, s.strftime("%d-%m-%Y"), e.strftime("%d-%m-%Y"))
                    if not x.empty:
                        x["symbol"] = index
                        save_append(to_datetime(x), table)
                except Exception as E:
                    print(f"{index}: error {E}")

def EPS_puller(symbol):
    url = f"""https://kbbuddywts.kbsec.com.vn/iis-server/investment/stockinfo/info/{symbol}?l=1"""
    try:
        r = session.get(url, headers = HEADERS, timeout = 10)
        r.raise_for_status()
    except Exception as e:
        print(f"{symbol} error: {e}")
        return None
    data = r.json()
    num_cols = ["EPS", "BVPS", "ROE", "ROA", "DIV", "YD", "MC"]
    text_cols = ["SB","FID"]
    data = pd.DataFrame([data]).reindex(columns = text_cols + num_cols)
    data[num_cols] = data[num_cols].apply(pd.to_numeric, errors="coerce")
    data["t"] = pd.Timestamp.today().normalize()
    return data[["t"] + text_cols + num_cols]

def auto_update_EPS(table = "fundamentals"):
    for symbol in symbols:
        x = EPS_puller(symbol)
        save_append(x, table, keys = ("SB", "FID"))
    
def auto_update_top_stock():
    x = topforeigntrade(100)
    y = topntrade(100)
    save_append(x, "top100_foreigntrade", keys = ("t", "symbol"))
    save_append(y, "top100_trade", keys = ("t","symbol"))

