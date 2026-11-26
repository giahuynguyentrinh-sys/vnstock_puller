
import pandas as pd
import numpy as np
import os
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

import duckdb


def inspect_dataset(path="data/data.parquet"):
    con = duckdb.connect()

    # 1. Dataset summary
    query = f"""
        SELECT
            COUNT(*) AS total_rows,
            COUNT(DISTINCT t) AS trading_days,
            COUNT(DISTINCT symbol) AS total_stocks,
            MIN(t) AS start_date,
            MAX(t) AS end_date,
            COUNT(*) FILTER (
                WHERE label_5d IS NULL
            ) AS missing_labels
        FROM read_parquet('{path}')
    """

    summary = con.execute(query).df()

    # 2. Rows per trading day
    query = f"""
        SELECT
            t,
            COUNT(*) AS rows
        FROM read_parquet('{path}')
        GROUP BY t
        ORDER BY t
    """

    daily = con.execute(query).df()

    # 3. Missing values in features
    feature_cols = [
        "return1day", "return5day", "return10day", "return60day",
        "hlrange_returns_day", "oc_return", "gap_overnight",
        "close_ma5", "close_ma10", "close_ma200",
        "return_ma_volatility_20day", "return5volatility",
        "return40volatility", "return60volatility", "atr_pct",
        "return_volume_ratio_5day", "return_volume_ratio_60day",
        "v_pct", "macd_norm", "signal_norm", "hist_norm",
        "norm_ema_12_day", "adx", "adx_pos", "adx_neg"
    ]

    feature_sql = ",\n".join(
        [
            f'COUNT(*) FILTER (WHERE "{col}" IS NULL) AS "{col}"'
            for col in feature_cols
        ]
    )

    query = f"""
        SELECT
            {feature_sql}
        FROM read_parquet('{path}')
    """

    missing = con.execute(query).df().T
    missing.columns = ["missing_count"]
    missing["missing_pct"] = (
        missing["missing_count"] / summary["total_rows"].iloc[0] * 100
    )

    # 4. Print results
    print("\n========== DATASET SUMMARY ==========")
    print(summary.to_string(index=False))

    print("\n========== ROWS PER DAY ==========")
    print(daily["rows"].describe())

    print("\n========== FEATURE MISSING VALUES ==========")
    print(
        missing.sort_values(
            "missing_pct",
            ascending=False
        ).to_string()
    )

    con.close()

    return summary, daily, missing


if __name__ == "__main__":
    summary, daily, missing = inspect_dataset()
summary, daily, missing = inspect_dataset()
"""
ic, summary = test_ic(
    df,
    feature_cols,
    label_col="label_5d",
    step=5,
    min_n=30
)


os.makedirs("data/ic_results", exist_ok=True)

ic.to_parquet("data/ic_results/ic.parquet")

summary.to_csv(
    "data/ic_results/ic_summary.csv",
    index=True
)

print("\n===== IC SUMMARY =====")
print(summary.to_string())

print("\nSaved:")
print("- data/ic_results/ic.parquet")
print("- data/ic_results/ic_summary.csv")
"""