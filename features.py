from Datastock import *
def get_pct_change(df,n): #nhận df đã sort_values("t" tăng dần)
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
    df[f"oprange_returns"] = df["o"] / df.groupby("symbol")["c"].shift(1)
    return df

def calc_ma_features(df, n): #lấy df từ all_data
    df = df.copy()
    df = df.sort_values(["symbol", "t"])
    ma = df.groupby("symbol")["c"].transform(
        lambda x:
        x.rolling(n).mean())
    df[f"close_ma{n}"] = df["c"]/ma -1
    return df

def calc_ma_rolling_features(df, n):
    df = df.copy()
    df = df.sort_values(["symbol", "t"])
    ma =df.groupby("symbol")["c"].transform(lambda  x: x.rolling(n).mean())    
    df[f"close_ma_std{n}"] = np.std(ma)
    return df
  
def calc_votality(df,periods = [1,5,10,20,40,60]):
    df = df.copy()
    df = df.sort_values(["symbol", "t"])
    df = calc_return_features(df, periods = [1])
    for days in periods:
        vol = df.groupby("symbol")["return1days"].transform(lambda x:
            x.rolling(days).std()
            )
        df[f"return{days}votality"] = vol
    return df


