
"""
partial_ic.py
Kiểm tra xem close_ma5 và oc_return có mang thông tin RIÊNG về label_5d hay không.

Ý tưởng:
- Mỗi ngày t, xếp hạng 2 feature giữa các mã.
- Hồi quy hạng của feature A theo hạng của feature B -> lấy phần dư.
- Phần dư = phần của A mà B không giải thích được.
- Tính IC của phần dư với label_5d. Nếu vẫn "stable" -> A có thông tin riêng.

Lưu ý: calc_ic / summarize_ic / test_ic được chép nguyên từ run_ic.py,
vì run_ic.py chạy toàn bộ code khi bị import (không có if __name__ == "__main__").
"""

import pandas as pd
import numpy as np
import os


# ---------- Phần mới: tính phần dư theo từng ngày ----------

def add_residual(df, y_col, x_col, new_col, min_n=30):
    """
    Với mỗi ngày t: hồi quy hạng(y_col) theo hạng(x_col), lưu phần dư vào new_col.
    Ngày nào có ít hơn min_n mã đủ dữ liệu thì để NaN.
    """
    df = df.copy()
    df[new_col] = np.nan

    for t, g in df.groupby("t"):
        sub = g[[x_col, y_col]].dropna()      # bỏ NaN ở CẢ HAI cột trước khi fit
        if len(sub) < min_n:
            continue

        x = sub[x_col].rank()
        y = sub[y_col].rank()

        a, b = np.polyfit(x, y, 1)            # y ≈ a*x + b
        resid = y - (a * x + b)

        df.loc[sub.index, new_col] = resid     # gán đúng vào các dòng của ngày t

    return df


def check_residual(df, x_col, resid_col):
    """
    Kiểm tra nhanh: phần dư phải gần như KHÔNG tương quan với x_col trong từng ngày.
    Nếu trung bình khác 0 rõ rệt -> hàm add_residual có lỗi.
    """
    corrs = []
    for t, g in df.groupby("t"):
        sub = g[[x_col, resid_col]].dropna()
        if len(sub) < 30:
            continue
        corrs.append(sub[x_col].rank().corr(sub[resid_col]))
    corrs = pd.Series(corrs)
    print(f"corr({x_col}, {resid_col}) theo ngày: "
          f"mean = {corrs.mean():.4f}, max |corr| = {corrs.abs().max():.4f}")


# ---------- Chép nguyên từ run_ic.py ----------

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
    out["t_stat"] = (ic_s.mean() / ic_s.std()) * np.sqrt(ic_s.count())
    return out.sort_values("t_stat", key=abs, ascending=False)


def test_ic(df, feature_cols, label_col="label_5d", step=5, min_n=30):
    ic = calc_ic(df, feature_cols, label_col, min_n)
    summary = summarize_ic(ic, step)
    offset_t = {}
    for k in range(step):
        s = ic.iloc[k::step]
        offset_t[f"t_off{k}"] = (s.mean() / s.std()) * np.sqrt(s.count())
    offset_df = pd.DataFrame(offset_t)
    summary = summary.join(offset_df)
    summary["stable"] = (
        (offset_df > 2).all(axis=1)
        |
        (offset_df < -2).all(axis=1)
    )
    return ic, summary


# ---------- Chạy ----------

"""
composite_ic.py
So sánh 2 điểm gộp để quyết định có giữ oc_return hay không:
    A = close_ma5 + hlrange_returns_day
    B = close_ma5 + hlrange_returns_day + oc_return

Cách gộp (mỗi ngày t):
    - Xếp hạng phần trăm (0..1) từng feature giữa các mã.
    - Lấy trung bình các hạng, rồi đổi dấu (vì cả 3 feature đều có IC âm).
    => Điểm càng cao = kỳ vọng label_5d càng cao. IC của điểm gộp nên DƯƠNG.

Cần đặt file này cùng thư mục với partial_ic.py (dùng lại test_ic từ đó).
"""

def add_composite(df, cols, new_col):
    """
    Điểm gộp = -(trung bình hạng phần trăm của các cột trong cols), tính theo từng ngày.
    Dòng nào thiếu bất kỳ cột nào thì điểm = NaN (skipna=False),
    để không trộn lẫn dòng đủ 3 feature với dòng chỉ có 2.
    """
    df = df.copy()
    ranks = pd.DataFrame(index=df.index)
    for col in cols:
        ranks[col] = df.groupby("t")[col].rank(pct=True)
    df[new_col] = -ranks.mean(axis=1, skipna=False)
    return df


def compare_ic(ic, col_new, col_base, step=5):
    """
    Kiểm tra trực tiếp: IC(col_new) - IC(col_base) theo từng ngày có > 0 ổn định không.
    In t-stat cho từng offset giống cách test_ic làm.
    """
    diff = (ic[col_new] - ic[col_base]).dropna()
    print(f"\n===== {col_new} - {col_base} =====")
    print(f"mean diff = {diff.mean():.5f}   (số ngày: {len(diff)})")
    print(f"tỷ lệ ngày {col_new} tốt hơn: {(diff > 0).mean():.1%}")
    for k in range(step):
        s = diff.iloc[k::step]
        t = s.mean() / s.std() * np.sqrt(s.count())
        print(f"t_off{k} = {t:.3f}")


if __name__ == "__main__":
    df = pd.read_parquet("data/data.parquet")
    df["t"] = pd.to_datetime(df["t"]).dt.normalize()
    df = df.reset_index(drop=True)

    label_col = "label_5d"
    cols_A = ["close_ma5", "hlrange_returns_day"]
    cols_B = ["close_ma5", "hlrange_returns_day", "oc_return"]

    missing = [c for c in cols_B + [label_col] if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    # So sánh công bằng: A và B phải tính trên CÙNG một tập dòng.
    # Nếu không, B có thể ít dòng hơn A (do oc_return NaN) và kết quả bị lệch.
    common = df[cols_B + [label_col]].notna().all(axis=1)
    print(f"Giữ {common.sum()} / {len(df)} dòng có đủ cả 3 feature và label")
    df = df[common].copy()

    df = add_composite(df, cols_A, "score_A")
    df = add_composite(df, cols_B, "score_B")

    feature_cols = ["score_A", "score_B", "close_ma5", "oc_return", "hlrange_returns_day"]
    ic, summary = test_ic(df, feature_cols, label_col=label_col, step=5, min_n=30)

    print("\n===== COMPOSITE IC SUMMARY =====")
    print(summary.to_string())

    compare_ic(ic, "score_B", "score_A", step=5)

    os.makedirs("data/ic_results", exist_ok=True)
    summary.to_csv("data/ic_results/composite_ic_summary.csv", index=True)
    print("\nSaved: data/ic_results/composite_ic_summary.csv")