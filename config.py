# config.py — nơi DUY NHẤT định nghĩa danh sách feature

label_col = "label_5d"
data_path = "data/data.parquet"

MODEL_FEATURES = [
    # 3 feature stable
    "close_ma5",
    "oc_return",
    "hlrange_returns_day",
    # đại diện các nhóm trùng lặp, chờ stage 3
    "atr_pct",
    "signal_norm",
    # feature đứng riêng
    "gap_overnight",
    "return60day",
    "close_ma200",
    "return_ma_volatility_20day",
    "return5volatility",
    "return_volume_ratio_5day",
    "return_volume_ratio_60day",
    "v_pct",
    "adx",
    "adx_pos",
    "adx_neg",
]