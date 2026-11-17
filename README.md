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

Phase 1 – Pipeline dữ liệu (làm trước).
Phase 2 – Thống kê thị trường
 Khối ngoại: kiểm tra FT là mua ròng hay tổng mua + bán.

Phase 4 – Cơ bản

 ROE, ROA, EPS, BVPS, cổ tức: đã kéo về qua EPS_puller, chưa có phân tích.
 Doanh thu, lợi nhuận sau thuế, tăng trưởng năm/quý: chưa có code.
 Nợ/vốn chủ sở hữu: chưa có code.
Phase 5 – Danh mục
 Bảng giao dịch (chưa có trong schema).
 Giá vốn trung bình, lãi/lỗ (đồng và %), tỷ trọng từng mã.
Phase 6 – Streamlit
 Chỉ bắt đầu khi Phase 1 ổn định.