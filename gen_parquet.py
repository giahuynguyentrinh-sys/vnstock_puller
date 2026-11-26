from features import *
import sqlite3
def calc_ic(df, feature_cols, label_col="label_5d", min_n=30):
    result = {}
    for t, g in df.groupby("t"):
        row = {}
        for col in feature_cols:
            sub = g[[col, label_col]].dropna()
            if len(sub) < min_n:
                row[col] = np.nan
        else:
            row[col] = sub[col].rank().corr(sub[label_col].rank())                
        result[t]= row
    ic = pd.DataFrame.from_dict(result, orient = "index")    
    return ic.sort_index()
def summarize_ic(ic, step = 5):
    out = pd.DataFrame({
        "mean_ic": ic.mean(),
        "std_ic": ic.std(),
        "count_ic": ic.count()
    })
    out["icir"] = out["mean_ic"] / out["std_ic"]
    out["pos_rate"] = (ic > 0).sum() / ic.count()
    ic_s = ic.iloc[::step]                      
    out["t_stat"] = ic_s.mean() / ic_s.std() * np.sqrt(ic_s.count())
    return out.sort_values("t_stat", key=abs, ascending=False)

with sqlite3.connect("stock.db") as conn:
    df = pd.read_sql_query("SELECT * FROM all_data", conn, parse_dates=["t"])
    df_index = pd.read_sql_query("SELECT * FROM all_index_info", conn, parse_dates=["t"])

df["t"] = df["t"].dt.normalize()
df_index["t"] = df_index["t"].dt.normalize()
base_cols = set(df.columns)

df = calc_return_features(df)                      # return1day ... return60day
df = calc_high_low_range(df)                       # hlrange_returns_day
df = calc_open_close_range(df)                     # gap_overnight (thực chất là c/o - 1)
df = calc_overnight_gap(df)                        # oc_return (thực chất là gap qua đêm)

for n in [5, 10, 20, 50, 200]:                     # chọn n tùy bạn
    df = calc_ma_features(df, n)                   # close_ma{n}
for n in [20]:
    df = calc_ma_volatility_features(df, n)        # return_ma_volatility_{n}day

df = calc_volatility(df)                           # return{5,10,20,40,60}volatility
df = calc_atr_features(df)                         # atr, atr_pct
df = calc_volume_ratio(df)                         # return_volume_ratio_{5,20,60}day
df = get_vpct_change(df, 5)                        # v_pct (n=5 là ví dụ)
df = calc_turnover_mean(df)                        # turnover, turnover_mean_20day
df = calc_rsi(df)                                  # rsi
df = calc_macd(df)                                 # macd_norm, signal_norm, hist_norm
df = calc_ema(df)                                  # ema_x_day và norm_ema_x_day
df = calc_adx(df)                                  # adx, adx_pos, adx_neg

df = calc_label(df, df_index, 5)                   # ĐỂ CUỐI: ret_fwd5, idx_ret_fwd5, label_5d
df = filter_liquidity(df)                          # lọc thanh khoản sau cùng

new_cols = [c for c in df.columns if c not in base_cols]
exclude = {
    "label_5d", "ret_fwd5", "idx_ret_fwd5",        # label (rò rỉ tương lai)
    "turnover", "turnover_mean_20day",             # quy mô thanh khoản
    "atr",                                         # giá trị tuyệt đối
    "ema_12_day", "ema_26_day", "ema_50_day",      # giá trị tuyệt đối
}
feature_cols = [c for c in new_cols if c not in exclude]
df.to_parquet("data/data.parquet", index = False)

