import sqlite3
import pandas as pd
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 200)
pd.set_option("display.max_rows", 200)

NGUONG = 0.07
DA_LOAI = []   # điền 5 mã đã loại nếu có

conn = sqlite3.connect("stock.db")

# Bảng lợi suất theo từng dòng (LAG theo từng mã)
sql = """
WITH r AS (
    SELECT symbol, t, c,
           LAG(c) OVER (PARTITION BY symbol ORDER BY t) AS prev_c,
           LAG(t) OVER (PARTITION BY symbol ORDER BY t) AS prev_t
    FROM all_data
)
SELECT symbol, t,
       c * 1.0 / prev_c - 1 AS ret,
       julianday(t) - julianday(prev_t) AS gap_days
FROM r
WHERE prev_c IS NOT NULL AND prev_c > 0
"""
x = pd.read_sql_query(sql, conn)
x["nam"] = x["t"].str[:4]
x["co"] = x["ret"].abs() > NGUONG
x = x[~x["symbol"].isin(DA_LOAI)]

# 1. Theo mã
theo_ma = (x.groupby("symbol")
             .agg(n_ret=("ret", "size"),
                  n_flag=("co", "sum"),
                  max_abs=("ret", lambda s: s.abs().max()))
             .query("n_flag > 0")
             .sort_values("n_flag", ascending=False))
theo_ma["pct_flag"] = (100 * theo_ma["n_flag"] / theo_ma["n_ret"]).round(3)
print("=== Theo mã (số mã có cờ:", len(theo_ma), ") ===")
print(theo_ma.round(4).to_string())

# 2. Theo năm: cờ dồn ở 2016 hay rải đều?
theo_nam = x.groupby("nam").agg(n_ret=("ret", "size"), n_flag=("co", "sum"))
theo_nam["pct_flag"] = (100 * theo_nam["n_flag"] / theo_nam["n_ret"]).round(3)
print("\n=== Theo năm ===")
print(theo_nam.to_string())

# 3. 81 dòng c ngoài [l, h] theo năm
bad = pd.read_sql_query(
    "SELECT symbol, t FROM all_data WHERE c > h OR c < l", conn)
print("\n=== c ngoài [l, h] theo năm ===")
print(bad.groupby(bad["t"].str[:4]).size())

# 4. Các cờ có max_abs lớn (nghi chia tách/lỗi nguồn): 20 dòng lớn nhất
print("\n=== 20 dòng |ret| lớn nhất ===")
print(x.reindex(x["ret"].abs().sort_values(ascending=False).index)
        .head(20)[["symbol", "t", "ret", "gap_days"]].to_string(index=False))

conn.close()

