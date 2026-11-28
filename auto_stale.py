from datetime import datetime
import traceback
from Datastock import *
with open("log_auto_stale.txt", "a", encoding="utf-8") as f:
    f.write(f"{datetime.now()} bắt đầu\n")
    try:
        print("loading")
        auto_fix_stale(symbols, tol = 0.03)
        f.write(f"{datetime.now()} xong\n")
    except Exception:
        f.write(traceback.format_exc() + "\n")

