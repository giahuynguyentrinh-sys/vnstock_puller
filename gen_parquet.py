from features import *
import sqlite3
with sqlite3.connect("stock.db") as conn:
    df = pd.read_sql_query("SELECT * FROM all_data", conn, parse_dates=["t"])
    df_index = pd.read_sql_query("SELECT * FROM all_index_info", conn, parse_dates=["t"])

df["t"] = df["t"].dt.normalize()
df_index["t"] = df_index["t"].dt.normalize()
base_cols = set(df.columns)
df = calc_return_features(df)
df = calc_high_low_range(df)
df = calc_open_close_range(df)
df = calc_overnight_gap(df)
df = calc_turnover_mean(df,periods=[20])
for n in [5,200]:
    df = calc_ma_features(df, n)
df = calc_ma_volatility_features(df, 20)
df = calc_volatility(df)
df = calc_atr_features(df)
df = calc_volume_ratio(df)
df = get_vpct_change(df, 5)
df = calc_rsi(df)
df = calc_macd(df)
df = calc_ema(df)
df = calc_adx(df)
df = calc_label(df, df_index, 5)
df = filter_liquidity(df)
new_cols = [c for c in df.columns if c not in base_cols]
exclude = {
    "label_5d", "ret_fwd5", "idx_ret_fwd5",        # label (rò rỉ tương lai)
    "turnover", "turnover_mean_20day",
    "atr",                                         # giá trị tuyệt đối
    "ema_12_day", "ema_26_day", "ema_50_day",      # giá trị tuyệt đối
}
feature_cols = [c for c in new_cols if c not in exclude]
df.to_parquet("data/data.parquet", index = False)

