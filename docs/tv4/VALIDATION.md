# Validation và phân tích của TV4

## Mục tiêu và điều kiện so sánh

TV4 xác thực mã thật của TV1/TV3/TV5 bằng oracle độc lập dùng bytes.find, không thay bằng các thuật toán tham khảo. Snapshot thuật toán là main `2ca31d9921b34c065af91d030a30c1befa8edb39`. Oracle giữ overlap bằng bước pos+1 và bảo toàn pid theo danh sách byte đầu vào. Khi so hiệu năng hoặc kết quả chung, nhóm cần chuẩn bị NFC→UTF-8 và loại trùng tập trung trước mọi thuật toán; các vi phạm hợp đồng ở đầu vào raw vẫn được báo riêng.

Mục tiêu tính đúng là cùng toàn bộ danh sách (pos,pid) sau sắp xếp. count/check dùng làm thông tin tóm tắt; không thay cho danh sách đầy đủ trong fuzzing. Offset thuộc bản byte sau chuẩn hóa. Không gộp byte ngẫu nhiên 0–255 vào đường decode Unicode.

## Thiết kế và kết quả kiểm chứng

| Lớp | Quy mô | Kết quả và giới hạn |
|---|---|---|
| Test gốc KMP/k-KMP | 15 phương thức, gồm 3.000 input ngẫu nhiên riêng của TV3 | Chạy được và đạt sau khi TV4 cung cấp oracle.py; trước đó là thiếu phụ thuộc, không phải thuật toán trượt đáp án |
| Unit TV4 | Oracle, chuẩn hóa, dòng, profile, validator, CSV | Kết quả đầy đủ ở unit_tests.txt; chạy lại khi mã thay đổi |
| Fuzzing độc lập | 10.000 ca/seed, seeds 11,29,47 | 30.000 cấu hình input, bốn nhóm bằng nhau mỗi seed; zero sai khác trên mẫu chuẩn trong lượt đã ghi |
| Ca biên | 10 ca/seed | Overlap, ushers, hậu tố, rỗng, mẫu dài, byte 0/255, NFC/NFD, CRLF, T4 nhỏ m=1.024 |
| Chế độ đếm | Mỗi ca fuzz thứ 10 | Đối chiếu đầu ra BF/KMP/k-KMP; chưa xác nhận instrumentation của AC vì chưa có |
| Fixture dòng | 7 dòng, nhãn khớp từ khóa viết tay | Cả bốn thuật toán đánh dấu đúng dòng 0,2,4,6; 5 hit; không phải nhãn độc hại |
| Oracle/LineCollector TV2 | 1.000 ca byte có LF/CRLF, seed 47 | count, check, lines_flagged, lines_total khớp oracle TV4 |

`verification.json` của mỗi seed lưu môi trường và hash nguồn tại thời điểm chạy. Validator mã thoát 1 khi còn hợp đồng/phần việc mở; không công bố toàn bộ nhóm pass chỉ vì canonical fuzzing đạt. Số ca là số input, không nhân số thuật toán để gọi thành các input độc lập hơn.

## Các lỗi và phụ thuộc đang mở

| ID | Loại | Chủ phần việc | Bằng chứng | Hướng xử lý |
|---|---|---|---|---|
| BF_EMPTY_COUNT | Contract issue | TV1 | scan(b'abc',b'') báo ValueError; scan_with_comparisons lại trả 4 vị trí | Kiểm đầu vào giống nhau tại các public entrypoint; build đã chặn nên cần phân biệt đường gọi trực tiếp |
| AC_DUPLICATE_PID | Contract issue | TV5 và nhóm | text ab, mẫu [ab,ab,b]: k-KMP có 3 hit với pid 0,1,2; AC có 2 hit với pid 0,1 | Chốt loại trùng tập trung hoặc bảo toàn pid nhất quán. TV4 đã có tiền xử lý tập trung, vẫn ghi bất nhất raw |
| AC_COUNT_PENDING | Pending dependency | TV5 | Chưa có scan_counted/scan_stats trên module AC | Bổ sung instrumentation theo hợp đồng trước số liệu chính thức; không gọi đây là sai kết quả tìm kiếm |
| TV2_ADAPTER_PENDING | Pending integration | TV2 và chủ thuật toán | Runner đòi NAME, VARIANT, callback scan/scan_counted/size và tên kmpk.py/ac.py khác module hiện có | Thống nhất giao diện hoặc thêm adapter đo thật, không lấy số stand-in thay mã thành viên |
| TV2_INTEGER_EXPORT | Observed export issue | TV2 | per_cell.csv: check 1449035347093 bị ghi 1.44904e+12; N=1048576 thành 1.04858e+06 | Giữ số nguyên chính xác cho checksum/count/N; tránh float và định dạng 6 chữ số với các trường này |
| TV2_WINDOWS_MACHINE | Observed portability issue | TV2 | Trên Windows, bench.py machine lỗi AttributeError ở os.getloadavg() | Kiểm khả năng hỗ trợ và dùng fallback trên Windows |

Ví dụ tái hiện và dữ liệu máy đọc được có trong reports/seed*/error_cases.json và reports/tv2_audit.json. TV4 chưa sửa mã của chủ thuật toán hoặc nhánh TV2.

## Hồ sơ từ khóa và ý nghĩa cho RQ2 RQ3

Đã phân tích bộ `kw_vi_seed11_k1000.txt` từ snapshot TV2 `5f60d7b`. Đây là **stub dùng pilot**, không phải bộ từ khóa chính thức của TV5:

| Chỉ số | Giá trị |
|---|---:|
| k sau chuẩn hóa và loại trùng | 1.000 |
| Mẫu trùng bị loại | 0 |
| Tổng độ dài L | 16.000 byte |
| m min / median / max | 16 / 16 / 16 byte |
| Trạng thái Trie tính độc lập, gồm gốc | 13.218 |
| Nút tiền tố được ít nhất hai mẫu đi qua | 796 |
| Tiền tố chung dài nhất của ít nhất hai mẫu | 15 byte |

Các số này chứng minh k và m chưa mô tả đủ cấu trúc bộ mẫu. Nếu mẫu chia sẻ nhiều tiền tố, Trie có thể dùng chung trạng thái; biên mẫu dài ảnh hưởng hành vi KMP khi sai. Đây là mô tả cấu trúc, chưa là bằng chứng một thuật toán nhanh hơn trên bộ này. Tần suất, mật độ hit và ảnh hưởng ngữ liệu cần corpus thật; CSV hiện để trống các trường đó vì corpus chưa được cung cấp trong repo.

Mỗi dòng keyword_profile.csv có pid, mẫu NFC, hex byte, m, số ký tự, biên dài nhất, tần suất nếu có corpus. Hash theo thứ tự mẫu tương thích TV2. Khi TV5 giao bộ chính thức, chạy lại profile và phân tích tần suất; không tái sử dụng số của stub để kết luận ứng dụng lọc từ cấm.

## Đối chiếu CSV TV2

Đã đọc 660 dòng raw pilot, 111 per-cell, 55 summary, 171 speedup, 39 total-cost. TV4 tính lại độc lập throughput, median/min/max theo cell, độ dao động, tổng hợp seed, speedup ghép cặp, build+r×scan và hòa vốn ở các dòng có số liệu. Với các đại lượng thực xuất 6 chữ số có nghĩa dùng sai số tương đối 1e-5, tuyệt đối 1e-6.

Không thấy sai các công thức đã kiểm trong ngưỡng trên. Có **80 trường checksum và 109 trường số nguyên khác** ở per_cell.csv bị thay đổi giá trị do định dạng số; đây là 189 ô bị ảnh hưởng bởi vấn đề xuất số nguyên, không phải 189 lỗi thiết kế độc lập. Bộ audit không chuyển checksum qua float, có test phân biệt 9007199254740993 với 9007199254740992.

Nhận xét trên không xác nhận số đo pilot thành số liệu chính thức. Không chạy lại thời gian Wikipedia, không xác thực dữ liệu gốc không có trong Git, không nghiệm thu chất lượng lọc độc hại hoặc hiệu năng của adapter chưa tích hợp.

## Kết luận và bước tiếp theo

TV4 đã bổ sung lớp kiểm chứng còn thiếu để nhóm tiếp tục làm việc có bằng chứng. Trên miền đầu vào chuẩn đã chọn, các lõi BF/KMP/k-KMP/AC không có sai khác được quan sát trong 30.000 ca; phần còn mở là hợp đồng raw, instrumentation, nối runner và đầu vào nghiên cứu thật.

Trước khi chạy ma trận chính thức: chốt hợp đồng mẫu/pid, xử lý các issue thuộc chủ phần việc, chạy lại validator, bàn giao corpus/keyword thật với hash, nối runner bằng mã thành viên rồi mới tính RQ1–RQ3. TV4 cần rà lại profile/tần suất và viết kết luận RQ2 cùng TV3 khi các kết quả thực nghiệm được tạo. Không có kiểm thử hữu hạn nào bảo đảm đúng với mọi đầu vào hay ổn định trên mọi môi trường.

## Nguồn nghiên cứu ban đầu

- Đề tài nhóm: https://docs.google.com/document/d/1hmhCDxGmCDkcC3m0-oT9hLydF285lwkA/edit
- KMP, SIAM 1977: https://epubs.siam.org/doi/10.1137/0206024
- Aho–Corasick, CACM 1975: https://doi.org/10.1145/360825.360855
- Python bytes.find: https://docs.python.org/3/library/stdtypes.html#bytes.find
- Python unicodedata: https://docs.python.org/3/library/unicodedata.html
