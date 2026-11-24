import sqlite3
import pandas as pd
from features import *

with sqlite3.connect("stock.db") as conn:
    df = pd.read_sql_query("SELECT * FROM all_data ORDER BY symbol, t", conn)
df = to_datetime(df)
df = calc_atr_features(df)
df = calc_adx(df)
df_v = df[df["symbol"] == "VNM"]
df_v = calc_rsi(df_v)
df_v = calc_macd(df_v)
print(df_v[["t", "rsi", "macd_norm", "signal_norm", "hist_norm"]].head(40))