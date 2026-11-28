import duckdb
import pandas as pd

pd.set_option("display.width", None)
pd.set_option("display.max_columns", None)

DATA_PATH = "data/data.parquet"
LABEL_COL = "label_5d"
MIN_N = 30
STEP = 5

feature_cols = [
    "return1day", "return5day", "return10day", "return60day",
    "hlrange_returns_day", "oc_return", "gap_overnight",
    "close_ma5", "close_ma10", "close_ma200",
    "return_ma_volatility_20day", "return5volatility",
    "return40volatility", "return60volatility", "atr_pct",
    "return_volume_ratio_5day", "return_volume_ratio_60day", "v_pct",
    "macd_norm", "signal_norm", "hist_norm", "norm_ema_12_day",
    "adx", "adx_pos", "adx_neg",
]

# Ép mọi feature về DOUBLE để UNPIVOT không lỗi khác kiểu dữ liệu
cast_cols = ",\n        ".join(f'CAST("{c}" AS DOUBLE) AS "{c}"' for c in feature_cols)
unpivot_cols = ", ".join(f'"{c}"' for c in feature_cols)

query = f"""
WITH src AS (
    SELECT
        CAST(t AS DATE) AS t,
        CAST({LABEL_COL} AS DOUBLE) AS y,
        {cast_cols}
    FROM read_parquet('{DATA_PATH}')
),

-- Bảng rộng (25 cột feature) -> bảng dài (t, feature, x, y)
long AS (
    UNPIVOT src
    ON {unpivot_cols}
    INTO NAME feature VALUE x
),

clean AS (
    SELECT t, feature, x, y
    FROM long
    WHERE x IS NOT NULL AND y IS NOT NULL
      AND isfinite(x) AND isfinite(y)
),

-- Rank trong từng (ngày, feature); hạng bằng nhau lấy hạng trung bình
ranked AS (
    SELECT
        t, feature,
        RANK() OVER (PARTITION BY t, feature ORDER BY x)
          + (COUNT(*) OVER (PARTITION BY t, feature, x) - 1) / 2.0 AS rx,
        RANK() OVER (PARTITION BY t, feature ORDER BY y)
          + (COUNT(*) OVER (PARTITION BY t, feature, y) - 1) / 2.0 AS ry
    FROM clean
),

-- IC theo ngày = Pearson trên rank = Spearman
daily AS (
    SELECT t, feature, CORR(rx, ry) AS ic
    FROM ranked
    GROUP BY t, feature
    HAVING COUNT(*) >= {MIN_N}
),

numbered AS (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY feature ORDER BY t) - 1 AS rn
    FROM daily
    WHERE ic IS NOT NULL
)

SELECT
    feature,
    AVG(ic)                       AS mean_ic,
    ABS(AVG(ic))                  AS abs_mean_ic,
    STDDEV_SAMP(ic)               AS std_ic,
    AVG(ic) / STDDEV_SAMP(ic)     AS icir,
    COUNT(*)                      AS n_days,
    -- t-stat lấy cách {STEP} ngày để tránh label chồng lấn
    AVG(ic) FILTER (WHERE rn % {STEP} = 0)
      / STDDEV_SAMP(ic) FILTER (WHERE rn % {STEP} = 0)
      * SQRT(COUNT(*) FILTER (WHERE rn % {STEP} = 0)) AS t_stat
FROM numbered
GROUP BY feature
ORDER BY abs_mean_ic ASC
"""

con = duckdb.connect()
result = con.execute(query).fetchdf()
con.close()

print("========== 9 FEATURE YẾU NHẤT (theo |mean IC|) ==========")
print(result.head(9).round(4).to_string(index=False))

print("\n========== 20 FEATURE YẾU NHẤT ==========")
print(result.head(20).round(4).to_string(index=False))

print("\n========== TOÀN BỘ 25 ==========")
print(result.round(4).to_string(index=False))