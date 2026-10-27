# Đánh giá tiến độ nhóm theo sản phẩm đã có

Ngày 28/10/2026. Đối chiếu bản phân công 14 ngày, main `2ca31d9`, TV2 `tv2-benchmark` tại `5f60d7b` và phần TV4 được bổ sung ở nhánh TV4-Tuan. Chỉ đánh giá bằng chứng có trong repo/nhánh và các lượt kiểm đã chạy; không suy tiến độ từ số commit hoặc khẳng định thành viên chưa làm những việc chưa đẩy lên.

Phân công theo người dùng: TV1 tonydoan007-coder; TV2 nhánh benchmark; TV3 kittyhan124-glitch; TV4 Tuan; TV5 kittyhan124-glitch. TV5 được ghi theo phân công này dù author một số commit AC mang tên ntmchau. Nhánh `tv2/benchmark` người dùng nhắc hiện được công bố với tên `tv2-benchmark`.

## Tóm tắt

| Thành viên | Phần đã có bằng chứng | Việc còn lại hoặc cần xác nhận | Đánh giá |
|---|---|---|---|
| TV1 | BF, chế độ đếm, tải T1/T2, sinh T3/T4, profile và manifest 29 file; kiểm byte đầu ra chuẩn đạt | Ràng buộc mẫu rỗng ở hàm đếm; bàn giao corpus ngoài Git/cách tái tạo đúng hash; nguồn bài/phiên bản/selection metadata; biểu đồ và kết luận RQ1 | Cài đặt và pipeline cơ bản đã có; chưa nghiệm thu toàn bộ dữ liệu và RQ1 |
| TV2 | Runner nhiều tiến trình, timing/count/mem, timeout/resume, ma trận 234 ô, schema, stats, pilot raw/summary/figures, khung Methods và decisions | Nối module thật; nguồn plots.py đang được nhắc nhưng không có trong snapshot; sửa xuất số nguyên và machine trên Windows; chốt quyết định còn mở; chạy chính thức và ghép báo cáo | Khung đo/thống kê khá đầy đủ; pilot vẫn là stand-in, chưa là kết quả RQ chính thức |
| TV3 | KMP, k-KMP một lượt, Prefix Table, chế độ đếm, trace, 15 test gốc; test gốc nay đạt khi TV4 cung cấp oracle; 30.000 ca TV4 chuẩn không sai khác | Thống nhất API với TV2; ghi rõ khác biệt số phép so sánh giữa timing và count nếu dùng để giải thích overhead; nghiên cứu/biểu đồ/kết luận RQ2 với TV4 | Lõi thuật toán và test cơ bản có bằng chứng tốt; phần thực nghiệm/báo cáo chưa hoàn tất |
| TV4 Tuan | Trước lượt này chưa có module; nay có oracle, chuẩn hóa/pid, test, 30.000 ca, profile từ khóa, fixture dòng, audit TV2 và Validation | Nghiệm thu lại sau sửa của các chủ phần việc; profile/tần suất trên corpus và bộ mẫu chính thức; đồng viết kết luận RQ2 theo số liệu thật | Hoàn thành gói công cụ và kiểm chứng hiện tại; chưa thể hoàn tất phần nghiên cứu phụ thuộc dữ liệu chưa bàn giao |
| TV5 | AC fail, Trie/dict, BFS failure/output, byte offset, wrapper build/scan, chuẩn hóa/loại trùng và hàm tìm hit đầu trong dòng; đầu vào chuẩn qua kiểm TV4 | Quy ước mẫu trùng/pid; instrumentation transitions/failure; bộ trích từ khóa và manifest chính thức; tổng hợp lines_flagged trên corpus; RQ3 và Discussion bộ nhớ/tốc độ | Lõi AC đã có; các đầu ra nghiên cứu và đo lường RQ3 còn nhiều phần chưa xác nhận |

Không chấm phần trăm vì nhiệm vụ có khối lượng khác nhau và repo không phản ánh công việc chưa đẩy. Tình trạng trên là theo từng đầu ra, không phải điểm cá nhân. DFA được miễn với nhóm 5 người nên không tính thiếu DFA thành chưa hoàn thành bắt buộc của TV5.

## Những phụ thuộc đã được gỡ trong lượt TV4

- Thiếu oracle.py không còn chặn test_kmp.py ở nhánh TV4-Tuan; 15 test gốc đạt.
- Có quy trình chuẩn hóa/loại trùng tập trung và ánh xạ pid; lỗi raw được ghi riêng để nhóm chọn hợp đồng.
- Có bằng chứng kiểm độc lập actual member code, không dùng algos_ref thay thế.
- Có đối chiếu oracle/LineCollector và tính lại số của pilot TV2; các issue xuất số có ví dụ để sửa.

## Thứ tự phối hợp đề nghị

1. TV1 và TV5 chốt/xử lý hợp đồng input; TV2 cùng chủ thuật toán thống nhất adapter cho runner.
2. TV1 bàn giao corpus hoặc quy trình dựng đúng hash, TV5 bàn giao bộ mẫu chính thức. TV4 chạy lại profile và gate; TV2 cập nhật các ghi chú dependency đã lỗi thời.
3. TV2 chạy pilot bằng module thật trên máy chính thức, chốt timeout rồi mới chạy ma trận; không dùng số pilot_standin làm kết quả nghiên cứu.
4. TV1/TV2 viết RQ1; TV3/TV4 viết RQ2; TV5 với TV2/TV4 viết RQ3; toàn nhóm tổng hợp Discussion/Conclusion.

Đánh giá này không tuyên bố main đang có merge conflict. Thiếu module do chưa hoàn thành là pending_dependency; khác giao diện là pending_integration; issue đã tái hiện được mới ghi lỗi cụ thể. Chỉ gộp TV4 vào main sau khi nhóm review và người dùng quyết định.
