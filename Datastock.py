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
from ta.momentum import RSIIndicator
from ta.trend import MACD, ADXIndicator
from ta.volatility import AverageTrueRange
import duckdb
start_date = date(2018,1,1)
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

DB_PATH = "stock.db"

def save_append(df, table, keys=("symbol", "t")):
    if df is None or df.empty:
        return 0
    for k in keys:
        if k not in df.columns:
            raise ValueError(f"{table}: df thiếu cột {k}")

    df = df.drop_duplicates(subset=list(keys)).copy()

    # chuẩn hóa datetime về cùng một định dạng chuỗi
    for c in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[c]):
            df[c] = df[c].dt.strftime("%Y-%m-%d %H:%M:%S")

    with sqlite3.connect(DB_PATH) as conn:
        co_bang = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ).fetchone()
        if co_bang is None:
            df.to_sql(table, conn, index=False)
            return len(df)

        cols = ", ".join(f'"{c}"' for c in df.columns)
        marks = ", ".join("?" * len(df.columns))
        sql = f'INSERT OR IGNORE INTO "{table}" ({cols}) VALUES ({marks})'

        rows = df.astype(object).where(df.notna(), None).itertuples(index=False, name=None)
        before = conn.total_changes
        conn.executemany(sql, rows)
        return conn.total_changes - before
        
def sqlite_append(df, table):
    if df is None or df.empty:
        return 0
    conn = sqlite3.connect("stock.db")
    try:
        df.to_sql(table, conn, if_exists="append", index=False)
        return len(df)
    finally:
        conn.close()
            

def calc_ma(symbol,n =200, extra= 100): #đường trung bình động n phiên
    df= get_recent_prices(symbol,n+extra)
    df["ma"] =df["c"].rolling(n).mean()
    return df

#transform tính trong từng nhóm, rồi trả về một chuỗi có cùng số dòng để dễ dàng
#gán lại vào sqlite
def cal_market_cap(sdate, edate, table1 = "all_data", table2 ="total_shares_2025"): #cái này chỉ pull dữ liệu từ năm 2025, thích
#thì phải sử dụng table2 = "2024_totalshares"
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


def cal_pe(symbol, table1 = "all_data", table2 = "fundamentals", fid = "12/2025"):
    with sqlite3.connect("stock.db") as con:
        query = f"""
        Select  data.symbol, 
                data.t,
                funda.FID,
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
                    funda.FID,
                    data.c / funda.BVPS  as pb
            from {table1} as data
            join {table2} as funda
            on funda.SB = data.symbol 
            where data.symbol = ? and funda.FID = ? and funda.BVPS > 0
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
def get_symbol_shares_range(symbol, start_year, end_year):
    """Trả về list các (symbol, t, shares) cho mọi cột nằm trong [start_year, end_year]."""
    try:
        bs = yf.Ticker(f"{symbol}.VN").balance_sheet
        if bs is None or bs.empty:
            print(f"{symbol}: balance_sheet rỗng")
            return []

        rows = []
        for col in bs.columns:
            ts = pd.Timestamp(col)
            if not (start_year <= ts.year <= end_year):
                continue
            for row, divisor in [
                ("Ordinary Shares Number", 1),
                ("Share Issued", 1),
                ("Common Stock", 10000),
            ]:
                if row in bs.index:
                    v = bs.loc[row, col]
                    if pd.notna(v) and v != 0:
                        rows.append((symbol, ts.tz_localize(None).normalize(), v / divisor))
                        break
        return rows

    except Exception as e:
        print(f"{symbol} error: {type(e).__name__}: {e}")
        return []


def get_all_totalshares_range(symbols, start_year=2021, end_year=2025, workers=8, table="totalshares"):
    with ThreadPoolExecutor(max_workers=workers) as ex:
        results = ex.map(
            lambda s: get_symbol_shares_range(s, start_year, end_year), symbols
        )
        results = list(tqdm(results, total=len(symbols)))

    flat = [r for sub in results for r in sub]
    df = pd.DataFrame(flat, columns=["symbol", "t", "total_shares"])
    df["t"] = pd.to_datetime(df["t"])

    n = save_append(df, table, keys=("symbol", "t"))
    print(f"Thêm {n} dòng mới vào bảng {table}")
    return n
def top_losers(n):#limit(n= 181)
    now = pd.Timestamp.today().normalize()
    with sqlite3.connect("stock.db") as conn:
        query = f""" WITH latest_dates AS (
    SELECT DISTINCT t
    FROM all_data
    WHERE t <= ?
    ORDER BY t DESC
    LIMIT 2
)
SELECT t, symbol, c
FROM all_data
WHERE t IN (SELECT t FROM latest_dates)
ORDER BY t ASC, symbol ASC;
        """
        df = pd.read_sql_query(query, conn, params = (now,))
    df.pivot(index = "symbol", columns = "t", values = "c")
    dates = sorted(df["t"].unique())
    if len(dates) < 2:
        return
    pivot = df.pivot(index = "symbol", columns = "t", values = "c")
    pivot = pivot.dropna(subset = dates)
    pivot = pivot[(pivot[dates[0]] > 0) & (pivot[dates[1]]>0)]
    pivot["change_pct"] = (
        (pivot[dates[1]] - pivot[dates[0]])
        / pivot[dates[0]]
    ) * 100
    top_gainers = pivot.sort_values(
        "change_pct", ascending=False
    ).head(n)

    top_losers = pivot.sort_values(
        "change_pct", ascending=True
    ).head(n)

    return top_gainers, top_losers

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
    border = 10
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
    first = days.iloc[0].date()
    if first > start_date + timedelta(days=border):
        missing.insert(0, (start_date, first - timedelta(days=1)))
    return missing


def findmissing_all(symbols, table):
    result = {}
    for symbol in symbols:
        missing = find_missing(symbol, table)
        if missing:
            result[symbol] = missing
    return result

def auto_update_all_data(symbols, table, workers=4):
    tasks = [(s, a, b) for s, rs in findmissing_all(symbols, table).items() for a, b in rs]

    def job(t):
        s, a, b = t
        try:
            x = get_kbs(s, a.strftime("%d-%m-%Y"), b.strftime("%d-%m-%Y"))
            if x.empty:
                return None
            x["symbol"] = s
            return to_datetime(x)
        except Exception as e:
            print(f"{s}: error {e}")

    with ThreadPoolExecutor(max_workers=workers) as ex:
        frames = [f for f in ex.map(job, tasks) if f is not None]
    if frames:
        print("Thêm", save_append(pd.concat(frames, ignore_index=True), table), "dòng")

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

def find_stale(symbols, days=60, tol=0.005, workers=4):
    end = date.today()
    start = end - timedelta(days=days)
    cutoff = pd.Timestamp(end - timedelta(days=3))   # bỏ 3 ngày gần nhất (có thể là dòng lưu dở)
    s_str, e_str = start.strftime("%d-%m-%Y"), end.strftime("%d-%m-%Y")

    # 1) Đọc DB đúng 1 lần cho tất cả mã (thay vì 1 query mỗi mã)
    with sqlite3.connect("stock.db") as conn:
        db_all = pd.read_sql_query(
            "SELECT symbol, t, c AS c_db FROM all_data WHERE substr(t,1,10) >= ?",
            conn, params=(start.strftime("%Y-%m-%d"),), parse_dates=["t"])
    db_all["t"] = db_all["t"].dt.normalize()
    db_by_symbol = {s: g[["t", "c_db"]] for s, g in db_all.groupby("symbol")}

    # 2) Hàm chạy trong thread: chỉ gọi API + so sánh, không đụng DB
    def check(s):
        try:
            src = get_kbs(s, s_str, e_str)
        except Exception as e:
            return s, None, str(e)
        if src.empty or s not in db_by_symbol:
            return s, False, None
        src = to_datetime(src)[["t", "c"]]
        m = src.merge(db_by_symbol[s], on="t")
        m = m[(m["t"] < cutoff) & (m["c_db"] > 0)]
        stale = bool(len(m) and ((m["c"] / m["c_db"] - 1).abs() > tol).any())
        return s, stale, None
    with ThreadPoolExecutor(max_workers=workers) as ex:
        results = list(tqdm(ex.map(check, symbols), total=len(symbols)))
    stale = [s for s, st, err in results if st]
    failed = [(s, err) for s, st, err in results if st is None]
    return stale, failed

def auto_fix_stale(symbols, table="all_data", days=60, tol=0.005, workers=4):
    stale, failed = find_stale(symbols, days=days, tol=tol, workers=workers)
    print(f"Lệch: {len(stale)} mã | Lỗi API: {len(failed)} mã")

    if stale:
        with sqlite3.connect("stock.db") as conn:
            conn.executemany(f'DELETE FROM "{table}" WHERE symbol = ?',
                             [(s,) for s in stale])
        auto_update_all_data(stale, table)

    return stale, failed
 