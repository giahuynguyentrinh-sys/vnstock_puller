import duckdb
import pandas as pd
import numpy as np
pd.set_option("display.max_rows", None)      # không giới hạn số hàng
pd.set_option("display.max_columns", None)   # không giới hạn số cột
pd.set_option("display.width", None)         # tự lấy theo độ rộng cửa sổ terminal
pd.set_option("display.max_colwidth", None)  # không cắt nội dung trong ô
def calc_ic(df, feature_cols, label_col="label_5d", min_n=30):

    result = {}

    for t, g in df.groupby("t"):

        row = {}

        for col in feature_cols:

            sub = g[[col, label_col]].dropna()

            if len(sub) < min_n:
                row[col] = np.nan

            else:
                row[col] = sub[col].rank().corr(
                    sub[label_col].rank()
                )

        result[t] = row

    ic = pd.DataFrame.from_dict(result, orient="index")
    ic.index.name = "t"

    return ic.sort_index()

def summarize_ic(ic, step=5):

    out = pd.DataFrame({
        "mean_ic": ic.mean(),
        "std_ic": ic.std(),
        "count_ic": ic.count()
    })

    out["icir"] = out["mean_ic"] / out["std_ic"]

    out["pos_rate"] = (ic > 0).sum() / ic.count()

    ic_s = ic.iloc[::step]

    out["t_stat"] = (
        ic_s.mean() / ic_s.std()
    ) * np.sqrt(ic_s.count())

    return out.sort_values(
        "t_stat",
        key=abs,
        ascending=False
    )

def test_ic(df, feature_cols, label_col="label_5d",
            step=5, min_n=30):

    ic = calc_ic(df, feature_cols, label_col, min_n)

    summary = summarize_ic(ic, step)

    offset_t = {}

    for k in range(step):

        s = ic.iloc[k::step]

        offset_t[f"t_off{k}"] = (
            s.mean() / s.std()
        ) * np.sqrt(s.count())

    offset_df = pd.DataFrame(offset_t)

    summary = summary.join(offset_df)

    summary["stable"] = (
        (offset_df > 2).all(axis=1)
        |
        (offset_df < -2).all(axis=1)
    )

    return ic, summary

df = pd.read_parquet("data/data.parquet")

df["t"] = pd.to_datetime(df["t"]).dt.normalize()

print("Data shape:", df.shape)

feature_cols = [
    "return1day",
    "return5day",
    "return10day",
    "return60day",
    "hlrange_returns_day",
    "oc_return",
    "gap_overnight",
    "close_ma5",
    "close_ma10",
    "close_ma200",
    "return_ma_volatility_20day",
    "return5volatility",
    "return40volatility",
    "return60volatility",
    "atr_pct",
    "return_volume_ratio_5day",
    "return_volume_ratio_60day",
    "v_pct",
    "macd_norm",
    "signal_norm",
    "hist_norm",
    "norm_ema_12_day",
    "adx",
    "adx_pos",
    "adx_neg"
]

label_col = "label_5d"


missing = [c for c in feature_cols + [label_col] if c not in df.columns]

if missing:
    raise ValueError(f"Missing columns: {missing}")

ic, summary = test_ic(
    df,
    feature_cols,
    label_col="label_5d",
    step=5,
    min_n=30
)
"""
stage3
grouped = df.groupby("t")
grouped = grouped[feature_cols].corr(method="spearman", min_periods = 30)
mean_df = grouped.groupby(level=1).mean()
mean_df = mean_df.reindex(feature_cols)
print(mean_df)
"""

"""
stage2
stable_cols = summary.index[summary["stable"]].tolist()   # lấy tự động, khỏi gõ tay

ic_year_mean  = ic[stable_cols].groupby(ic.index.year).mean()
ic_year_count = ic[stable_cols].groupby(ic.index.year).count()


print(df[stable_cols].corr(method="spearman").round(2)) 
"""