from datetime import datetime
import traceback
from Datastock import *

with open("log.txt", "a", encoding="utf-8") as f:
    f.write(f"{datetime.now()} bắt đầu\n")
    try:
        print("loading")
        auto_update_all_data(symbols, "all_data")
        auto_update_all_index_info(indexs, "all_index_info")
        auto_update_EPS(table = "fundamentals")
        auto_update_top_stock() 
        f.write(f"{datetime.now()} xong\n")
    except Exception:
        f.write(traceback.format_exc() + "\n")

