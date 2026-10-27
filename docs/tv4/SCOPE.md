# Phạm vi TV4 Tuan

Theo mục Thành viên 4 trong bản phân công hai tuần đã được nhóm giao: xây oracle độc lập, ca biên và 10.000 ca fuzzing; kiểm Unicode, overlap, hậu tố, mẫu trùng; phân tích từ khóa; kiểm lines_flagged và đối chiếu số liệu TV2; ghi lỗi để chủ thuật toán xử lý; viết phần Validation và tiến độ nhóm.

Nhánh đích do người dùng yêu cầu: `TV4-Tuan`, xuất phát từ main `2ca31d9921b34c065af91d030a30c1befa8edb39`. Nhánh TV2 thực tế: `tv2-benchmark` tại `5f60d7b9e4cb3665da084df76bbd1a54c829cf18` (người dùng gọi tv2/benchmark). Phân công thành viên theo người dùng, không suy từ author commit: TV1 tonydoan007-coder, TV2 nhánh benchmark, TV3 kittyhan124-glitch, TV4 Tuan, TV5 kittyhan124-glitch.

## Cách thực hiện

Bổ sung `oracle.py` đúng import mà test_kmp.py đang dùng; package `tv4/` gồm tiền xử lý tập mẫu, phân tích từ khóa, validator và kiểm CSV. Dùng thư viện chuẩn Python 3.10+, không phụ thuộc Wikipedia hoặc mạng để chạy bộ kiểm thử chính. Các module thuật toán hiện tại được đọc nguyên trạng, không đổi API hay âm thầm sửa lỗi của thành viên khác.

Oracle dùng bytes.find, bước pos+1, bảo toàn pid và mẫu trùng ở tầng bytes, sắp xếp kết quả. Tầng tiền xử lý Unicode áp dụng NFC→UTF-8, loại trùng tập trung và ghi ánh xạ. Kiểm thử công bằng dùng bộ mẫu đã loại trùng; các vi phạm hợp đồng raw được kiểm riêng và phải xuất hiện trong báo cáo, không bị bỏ qua.

Kiểm dòng dùng LF, tính cả dòng rỗng cuối; mẫu chứa LF không được dùng cho chỉ số dòng. Nhãn fixture là đáp án khớp từ khóa viết tay, không phải nhãn độc hại được người thật xác thực. Hồ sơ từ khóa của TV2 được ghi là stub, không gọi bộ chính thức của TV5. Không có dữ liệu corpus thật thì tần suất corpus để trống.

Tiến độ dùng bằng chứng sản phẩm so với nhiệm vụ, không suy tỷ lệ hoàn thành từ số commit. Phần thiếu do phụ thuộc chưa hoàn thành được ghi `pending_dependency`; lỗi chạy trên đầu vào hợp lệ là `algorithm_failure`; sai hợp đồng là `contract_issue`. Validator phải báo riêng tính đúng trên đầu vào chuẩn và các vấn đề nghiệm thu còn mở.

## Tiêu chí nghiệm thu

- Test gốc test_kmp.py chạy được nhờ oracle.py; test mới cho oracle, chuẩn hóa, keyword profile, dòng, CSV và validator đạt.
- Chạy 10.000 ca mỗi seed 11,29,47; so đầy đủ cặp pos/pid, lưu hash mã, seed và lỗi nhỏ nhất tái hiện được.
- Có hồ sơ từ khóa, fixture dòng có đáp án biết trước, nhật ký lỗi, phần Validation và bảng tiến độ năm thành viên.
- Có đối chiếu oracle tối thiểu TV2 và công thức CSV trên pilot; ghi rõ đây chưa là số liệu nghiên cứu chính thức.
- Không gọi toàn nhóm pass nếu validator còn phát hiện hợp đồng chưa thống nhất.

## Quyết định triển khai

Giữ module của thành viên nguyên trạng và thêm adapter đọc kết quả để kiểm tra. Đổi toàn bộ module sang giao diện TV2 hoặc chỉ kiểm stand-in đều không đáp ứng nhiệm vụ xác thực độc lập mã thật. Chọn cách bổ sung trên để dễ review và đưa lỗi về đúng chủ phần việc.
