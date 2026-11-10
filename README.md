1. Giá và giao dịch

Giá mở, cao, thấp, đóng, khối lượng (OHLCV): đã có
% thay đổi so với giá tham chiếu: làm được một phần
Giá trần, sàn, tham chiếu: làm được một phần
Giá trị giao dịch: chưa xong
Vốn hóa: làm được một phần

2. Chỉ số thị trường

VN-Index, VN30, HNX-Index, UPCoM-Index: đang làm, mới chạy được VN100
Thanh khoản toàn thị trường: chưa xong
Khối ngoại mua/bán ròng: làm được một phần
Top tăng, giảm, khối lượng lớn nhất: làm được một phần

3. Chỉ số kỹ thuật

MA 20, 50, 200: đã có hàm
RSI: đã có
MACD: đã có
Khối lượng so với trung bình: đã có

4. Chỉ số cơ bản

EPS, P/E, P/B: chưa làm
ROE, ROA: chưa làm
Doanh thu, lợi nhuận sau thuế, tăng trưởng theo năm/quý: chưa làm
Nợ/vốn chủ sở hữu: chưa làm
Cổ tức: chưa làm

5. Danh mục của người dùng

Giá vốn trung bình, số lượng: chưa làm
Lãi/lỗ (đồng và %): chưa làm
Tỷ trọng từng mã: chưa làm




todolist 10/28/2026
VN Stock Puller – TODO

Quy ước: [ ] chưa làm, [~] đang làm / làm một phần. Mục "Kiểm tra" là thứ cần chạy thật để xác minh, chưa được xác minh trong code.

Phase 1 – Pipeline dữ liệu (làm trước)
 Chạy run_update.py, mở log.txt, đọc traceback cuối. Sau đó so ngày mới nhất trong all_data với ngày giao dịch gần nhất.
 auto_update_all_data: xóa pass và hai continue thừa. Cân nhắc đổi print sang logging để lỗi vào log.txt. Làm tương tự cho auto_update_all_index_info.
 volume_ratio: query chỉ select v nhưng to_datetime cần cột t → KeyError. Thêm t vào SELECT.
 Bảng top100_foreigntrade, top100_trade: schema DB còn cột date, code xuất cột t → save_append báo no such column. Chọn một: đổi tên cột trong DB hoặc đổi code. Chưa có ràng buộc UNIQUE.
 top100_trade: cột value, original_value đang là TEXT, cần ép số.
 Chỉ số: chỉ chạy được VN100. Chạy riêng từng index, in df.columns, so với schema all_index_info (không có va). Lỗi save_append khi có cột thừa là nghi vấn, chưa xác minh.
 Chỉ số: HNX30 là rổ khác HNX-Index. Quyết định có thêm HNX-Index không.
 Chỉ chạy cập nhật sau 15h30, vì save_append không ghi đè dòng đã có nên số liệu dở dang của ngày đang giao dịch sẽ bị giữ lại.
 find_missing: chưa phát hiện thiếu phần đầu (so days.iloc[0] với start_date). Tùy chọn.
 fundamentals: FID là kỳ báo cáo (vd 2025/12), nên khóa ("SB", "FID") là đúng. Kiểm tra: SELECT DISTINCT FID FROM fundamentals. Lưu ý: số liệu sửa lại của cùng kỳ sẽ không được cập nhật.
Phase 2 – Thống kê thị trường
 Thanh khoản toàn thị trường: TẠM BỎ (rổ symbols không đủ mã). Tùy chọn sau: SUM(value) của top100_trade.
 Top tăng/giảm: chưa làm.
 Giá trị giao dịch: kiểm tra va có đúng là giá trị giao dịch không và đơn vị.
 % thay đổi so với giá tham chiếu: hiện calc_daily_returns so với close phiên trước, khác giá tham chiếu.
 Vốn hóa: cal_market_cap dùng số cổ phiếu 2025, chưa lưu ra bảng. Đối chiếu với MC trong fundamentals.
 Khối ngoại: kiểm tra FT là mua ròng hay tổng mua + bán.
Phase 3 – Kỹ thuật
 MA20/50/200: nối calc_ma với dữ liệu giá. get_recent_prices mặc định 100 phiên, không đủ cho MA200.
Phase 4 – Cơ bản
 P/E, P/B (hàm cal_pe đang viết dở):
Chạy SELECT DISTINCT FID và SELECT SB, FID, EPS, BVPS FROM fundamentals WHERE SB='VNM'.
Kiểm tra đơn vị c (đồng/nghìn đồng) so với EPS, BVPS.
Kiểm tra EPS là cả năm hay một quý (đối chiếu CafeF/Vietstock).
Sửa query: data.symbol = ? có tiền tố bảng, chọn dòng giá mới nhất bằng max(t), chọn dòng fundamentals mới nhất bằng max(FID), c * 1.0 / EPS, thêm pd.read_sql_query với params đủ số dấu ?.
EPS <= 0 → để NaN (CASE WHEN EPS > 0).
Đưa cột FID vào kết quả để biết P/E dựa trên kỳ nào.
Viết bản tính tất cả mã trước, lọc một mã sau (tham số symbol tùy chọn). Không cần lưu vào DB.
 ROE, ROA, EPS, BVPS, cổ tức: đã kéo về qua EPS_puller, chưa có phân tích.
 Doanh thu, lợi nhuận sau thuế, tăng trưởng năm/quý: chưa có code.
 Nợ/vốn chủ sở hữu: chưa có code.
Phase 5 – Danh mục
 Bảng giao dịch (chưa có trong schema).
 Giá vốn trung bình, lãi/lỗ (đồng và %), tỷ trọng từng mã.
Phase 6 – Streamlit
 Chỉ bắt đầu khi Phase 1 ổn định.