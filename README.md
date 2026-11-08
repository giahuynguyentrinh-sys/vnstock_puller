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
1. get_index_info_day đã mất đoạn pd.to_numeric và .dt.normalize(). Dòng đầu của API vẫn trả giá trị dạng chuỗi, nên lưu vào SQLite sẽ thành chữ, còn ngày vẫn có đuôi 07:00. Thêm lại hai bước đó trước khi return.
Ghi chú #append trên get_index_info_day: append_sqlite không chặn dòng trùng, chạy hai lần là hai bản. Dùng INSERT OR REPLACE với khóa chính (symbol, t) như save_index mình đưa trước đó.
Thứ tự nên làm tiếp

Theo hướng cho chạy được trước:

1.Viết hàm lưu hằng ngày cho index_prices, top100_trade, top100_foreigntrade (khóa chính, không trùng dòng). Đây là phần lấp đầy mục 2 gần hết.
2.Viết top_movers (top tăng, giảm), mình đã đưa code ở trên, chỉ cần dán vào.
3.Kiểm tra va và FT bằng hai phép so sánh đã nói. Xong thì mục 1 gần xong.
4.Mục 4 và 5 để sau cùng. Mục 4 khó nhất vì cần nguồn báo cáo tài chính (Yahoo thường thiếu cho mã Việt Nam, bạn có thể tìm endpoint KBS bằng DevTools như đã làm với giá). 5.Mục 5 chỉ cần một bảng giao dịch (mã, ngày, mua/bán, số lượng, giá), từ đó tính giá vốn trung bình, lãi lỗ và tỷ trọng bằng giá đóng cửa mới nhất.
