from Datastock import *

def calc_return_features(df, periods = [10,20,40,60]): #lấy df từ all_data
    df = df.copy()
    df = df.sort_values(["symbol", "t"])
    for days in periods:
        df[f"return{days}day"] = df.groupby("symbol")["c"].pct_change(days,fill_method=None)
    return df

def calc_high_low_range(df):
    df = df.copy()
    df = df.sort_values(["symbol", "t"]) 
    df[f"hlrange_returns_day"] = ((df["h"] - df["l"])/df["c"]).replace([np.inf,
-np.inf],np.nan)
    return df

def calc_open_close_range(df):
    df = df.copy()
    df = df.sort_values(["symbol", "t"])
    df["oc_return"] = (
    (df["c"] - df["o"]) / df["o"]
).replace([np.inf, -np.inf], np.nan)
    return df 

def calc_overnight_gap(df):
    df = df.copy()
    df = df.sort_values(["symbol", "t"])
    overnight_gap = (df["o"] / df.groupby("symbol")["c"].shift(1)).replace([np.inf, -np.inf], np.nan)
    df[f"gap_overnight"] = overnight_gap - 1
    return df

def calc_ma_features(df, n): #lấy df từ all_data
    df = df.copy()
    df = df.sort_values(["symbol", "t"])
    ma = df.groupby("symbol")["c"].transform(
        lambda x:
        x.rolling(n).mean())
    ma_features = (df["c"]/ma).replace([np.inf,-np.inf],np.nan)
    df[f"close_ma{n}"] = ma_features - 1
    return df

def calc_ma_volatility_features(df, n):
    df = df.copy()
    df = df.sort_values(["symbol", "t"])
    ma = df.groupby("symbol")["c"].transform(
        lambda x: x.rolling(n).mean()
    )
    std = ma.groupby(df["symbol"]).transform(
        lambda x: x.rolling(n).std()
    )
    result = (std/df["c"]).where(df["c"]>0)
    df[f"return_ma_volatility_{n}day"] = result
    return df


def calc_volatility(df,periods = [5,10,20]):
    df = df.copy()
    df = df.sort_values(["symbol", "t"])
    df = calc_return_features(df, periods = [1])
    for days in periods:
        vol = df.groupby("symbol")[f"return1day"].transform(lambda x:
            x.rolling(days).std()
        )
        df[f"return{days}volatility"] = vol
    return df

def calc_atr_features(df, n=14):
    df = df.copy()
    df = df.sort_values(["symbol", "t"])
    parts = []
    for _, g in df.groupby("symbol"):
        atr = AverageTrueRange(g["h"], g["l"], g["c"], window=n).average_true_range()
        parts.append(atr)
    df["atr"] = pd.concat(parts)
    pos = df.groupby("symbol").cumcount()
    df.loc[pos < n - 1, "atr"] = np.nan
    df["atr_pct"] = (df["atr"] / df["c"]).where(df["c"] > 0)
    return df

def calc_volume_ratio(df, periods=[5,20,60]):
    df = df.copy()
    df = df.sort_values(["symbol", "t"])
    for days in periods:
        avg = (
        df.groupby("symbol")["v"].transform(lambda x: x.shift(1).rolling(days).mean()))
        df[f"return_volume_ratio_{days}day"] = df["v"]/avg.replace([np.inf, -np.inf], np.nan).where(avg > 0)
    return df

def get_vpct_change(df,n): #nhận df đã sort_values("t" tăng dần)
    df = df.copy()
    df = df.sort_values(["symbol", "t"])
    now = df["v"]
    before = df.groupby("symbol")["v"].shift(n)  
    result = ((now - before) / before).where(before > 0)
    df["v_pct"] = result
    return df

def calc_turnover(df):
    df = df.copy()
    df["turnover"] = df["c"] * df["v"]
    return df

def calc_turnover_mean(df,periods=[20]):
    df = calc_turnover(df)
    df = df.copy()
    df = df.sort_values(["symbol", "t"])
    for days in periods:
        df[f"turnover_mean_{days}day"] = (
        df.groupby("symbol")["turnover"]
        .transform(lambda x: x.shift(1).rolling(days).mean())
    )
    return df

def calc_rsi(df, window=14):
    df = df.copy()
    df = df.sort_values(["symbol", "t"])

    df["rsi"] = df.groupby("symbol")["c"].transform(
        lambda x: RSIIndicator(x, window=window).rsi()
    )
    return df

def calc_macd(df, window_fast=12, window_slow=26, window_sign=9):
    df = df.copy()
    df = df.sort_values(["symbol", "t"])
    macd_list, sig_list, hist_list = [], [], []
    for _, g in df.groupby("symbol"):
        macd_indicator = MACD(
            g["c"],
            window_fast=window_fast,
            window_slow=window_slow,
            window_sign=window_sign
        )
        c = g["c"].where(g["c"] > 0)
        #macd_list.append(macd_indicator.macd() / c)
        sig_list.append(macd_indicator.macd_signal() / c)
        #hist_list.append(macd_indicator.macd_diff() / c)
    #df["macd_norm"] = pd.concat(macd_list)
    df["signal_norm"] = pd.concat(sig_list)
    #df["hist_norm"] = pd.concat(hist_list)
    return df

def calc_ema(df, periods = [26,50]):
    df = df.copy()
    df = df.sort_values(["symbol", "t"])
    for days in periods:
        df[f"ema_{days}_day"] = df.groupby("symbol")["c"].transform(
            lambda x: x.ewm(span=days, adjust=False, min_periods = days).mean()
        )
        df[f"norm_ema_{days}_day"] = (df[f"ema_{days}_day"]/df["c"]).where(df["c"]>0)
    return df

def calc_adx(df, window = 14):
    df = df.copy()
    df = df.sort_values(["symbol","t"])
    adx_list, pos_list, neg_list = [], [], []
    for _, g in df.groupby("symbol"):
        indicator = ADXIndicator(
            high = g["h"],
            low = g["l"],
            close = g["c"],
            window = window
        )
        adx_list.append(indicator.adx())
        pos_list.append(indicator.adx_pos())
        neg_list.append(indicator.adx_neg())
    df["adx"] = pd.concat(adx_list)
    df["adx_pos"] = pd.concat(pos_list)
    df["adx_neg"] = pd.concat(neg_list)
    pos = df.groupby("symbol").cumcount()
    df.loc[pos < 2 * window, ["adx", "adx_pos", "adx_neg"]] = np.nan
    return df

def calc_label(df, df_index, days = 5):
    df = df.copy()
    df = df.sort_values(["symbol", "t"])
    fut = df.groupby("symbol")["c"].shift(-days)
    valid = (df["c"]>0) & (fut>0)
    df[f"ret_fwd{days}"] = (fut/df["c"] -1).where(valid)
    
    idx = df_index[df_index["symbol"]=="VNINDEX"][["t", "c"]].copy()
    idx = idx.sort_values("t")
    fut_idx = idx["c"].shift(-days)
    valid_idx = (idx["c"]>0) & (fut_idx >0)
    idx[f"idx_ret_fwd{days}"] = (fut_idx/idx["c"]-1).where(valid_idx)
    idx = idx[["t", f"idx_ret_fwd{days}"]]
    
    df = df.merge(idx, on = "t",how = "left")
    df = df.sort_values(["symbol", "t"])
    df[f"label_{days}d"] = df[f"ret_fwd{days}"] - df[f"idx_ret_fwd{days}"]
    return df

def filter_liquidity(df, min_turnover=1_000_000_000, col="turnover_mean_20day"):
    df = df.copy()
    keep = df[col] > min_turnover
    print(f"Giữ {keep.sum()} / {len(df)} dòng ({keep.mean():.1%})")
    return df[keep].copy()

