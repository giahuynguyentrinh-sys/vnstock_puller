from Datastock import *
before = dem()
with sqlite3.connect("stock.db") as conn:
    conn.execute("DELETE FROM all_data WHERE symbol='VNM' AND t BETWEEN '2025-03-01' AND '2025-03-31'")
print(find_missing("VNM", "all_data"))      # phải thấy đoạn tháng 3/2025
auto_update_all(["VNM"], "all_data")
print(before, dem())                       # hai số phải bằng nhau