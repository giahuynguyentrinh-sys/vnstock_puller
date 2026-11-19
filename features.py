from Datastock import *
def get_pct_change(df,n): #nhận df đã sort_values("t" tăng dần)
    df = df.copy()
    df = df.sort_values(["symbol", "t"])
    if len(df) < n+1:
        return None
    now = df["c"].iloc[-1]
    before = df["c"].iloc[-(n+1)]
    if before <= 0:
        return None
    return (now - before) / before
def calc_return_features(df, periods = [1,5,10,20,40,60]): #lấy df từ all_data
    df = df.copy()
    df = df.sort_values(["symbol", "t"])
    for days in periods:
        df[f"return{days}day"] = df.groupby("symbol")["c"].pct_change(days)
    return df
    
def calc_log_features(df,periods = [1,5,10,20,40,60]):
    df = df.copy()
    df = df.sort_values(["symbol", "t"])
    for days in periods:
            df[f"log_return{days}day"] = np.log(df.groupby("symbol")["c"].transform(
            lambda x: x/ x.shift(days)))
    return df

def calc_high_low_range(df):
    df = df.copy()
    df = df.sort_values(["symbol", "t"])
    df[f"hlrange_returns_day"] = (df["h"] - df["l"])/df["c"]
    return df
def calc_open_close_range(df):
    df = df.copy()
    df = df.sort_values(["symbol", "t"])
    df[f"oprange_returns_day"] = (df["c"] - df["o"])/df["o"]
    return df 
def calc_overnight_gap(df):
    df = df.copy()
    df = df.sort_values(["symbol", "t"])
    df[f"oprange_returns"] = df["o"] / df.groupby("symbol")["c"].shift(1) -1
    return df

def calc_ma_features(df, n): #lấy df từ all_data
    df = df.copy()
    df = df.sort_values(["symbol", "t"])
    ma = df.groupby("symbol")["c"].transform(
        lambda x:
        x.rolling(n).mean())
    df[f"close_ma{n}"] = df["c"]/ma -1
    return df

def calc_ma_votality_features(df, n):
    df = df.copy()
    df = df.sort_values(["symbol", "t"])
    
def calc_ma_rolling_features(df, n):
    df = df.copy()
    df = df.sort_values(["symbol", "t"])

    ma = df.groupby("symbol")["c"].transform(
        lambda x: x.rolling(n).mean()
    )

    df[f"close_ma_std{n}"] = (
        ma.groupby(df["symbol"])
        .transform(lambda x: x.rolling(n).std())
        / df["c"]
    )  

def calc_votality(df,periods = [1,5,10,20,40,60]):
    df = df.copy()
    df = df.sort_values(["symbol", "t"])
    df = calc_return_features(df, periods = [1])
    for days in periods:
        vol = df.groupby("symbol")[f"return{days}days"].transform(lambda x:
            x.rolling(days).std()
            )
        df[f"return{days}votality"] = vol
    return df

def calc_atr_features(df, n=14):
    df = df.copy()
    df = df.sort_values(["symbol", "t"])
    df["atr"] = df.groupby("symbol", group_keys=False).apply(
        lambda g: AverageTrueRange(g["h"], g["l"], g["c"], window=n).average_true_range())
    df["atr_pct"] = df["atr"] / df["c"]
    return df

def calc_volume_ratio(df, periods=[5,20,60]):
    df = df.copy()
    df = df.sort_values(["symbol", "t"])
    for days in periods:
        avg = (
        df.groupby("symbol")["v"]
        .transform(lambda x: x.shift(1).rolling(days).mean())
    )
        df[f"return_volume_ratio_{days}day"] = df["v"]/avg
    return df

def get_vpct_change(df,n): #nhận df đã sort_values("t" tăng dần)
    df = df.copy()
    df = df.sort_values(["symbol", "t"])
    if len(df) < n+1:
        return None
    now = df["v"]
    before = df.groupby("symbol")["v"].shift(n)  
    result = (now - before) / before
    result = result.where(before > 0)
    return (now - before) / before

def calc_turnover(df):
    df["turnover"] = df["c"] * df["v"]
    return df

def calc_turnover_mean(df,periods=[20]):
    df = calc_turnover(df)
    df = df.copy()
    df = df.sort_values(["symbol", "t"])
    for days in periods:
        df[f"return_{days}_day"] = (
        df.groupby("symbol")["v"]
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

def cal_macd(df, window_fast=12, window_slow=26, window_sign=9):
    df = df.copy()
    df = df.sort_values(["symbol", "t"])
    macd_indicator = MACD(
        df["c"],
        window_fast=window_fast,
        window_slow=window_slow,
        window_sign=window_sign
    )
    df["macd"] = macd_indicator.macd()
    df["signal"] = macd_indicator.macd_signal()
    df["Histogram"] = macd_indicator.macd_diff()
    return df

def calc_ema(df, periods = [12,26,50]):
    df = df.copy()
    df = df.sort_values(["symbol", "t"])
    for days in periods:
        df[f"ema_{days}_day"] = df.groupby("symbol")["c"].transform(
            lambda x: x.ewm(span=days, adjust=False).mean()
        )
        df[f"norm_ema_{days}_day"] = df[f"ema_{days}_day"]/df["c"]
    return df

def calc_adx(df, window = 14):
    df = df.copy()
    df = df.sort_values(["symbol","t"])
    indicator = ADXIndicator(
    high=df["h"],
    low=df["l"],
    close=df["c"],
    window=window
)   
    
def calc_adx(df, window = 14):
    df = df.copy()
    df = df.sort_values(["symbol","t"])
    
    def calculate(group):
        indicator = ADXIndicator(
            high = group["h"],
            low = group["l"],
            close = group["c"],
            window = window
        )
        group["adx"] = indicator.adx()
        group["adx_pos"]=indicator.adx_pos()
        group["adx_neg"]= indicator.adx_neg()
        return group
    df = df.groupby("symbol",group_keys = False).apply(calculate)
    return df

