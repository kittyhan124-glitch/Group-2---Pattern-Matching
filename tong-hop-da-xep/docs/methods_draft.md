# Khung phần Methods (TV2) — bản nháp để ghép vào báo cáo IEEE

> Chỗ ghi **[ĐIỀN]** là số liệu hoặc quyết định chỉ có sau khi chạy chính thức bằng mã thật; **không điền số từ pilot stand-in**.
> Chỗ ghi **[XN]** là quyết định còn chờ nhóm xác nhận trong `decisions.md`.

## III. METHODS

### A. Môi trường và đồng hồ đo
Mọi phép đo chạy trên một máy duy nhất: **[ĐIỀN: CPU, RAM, hệ điều hành]**, CPython **[ĐIỀN: phiên bản]**, cài đặt Python thuần. Thời gian
được đo bằng `time.perf_counter_ns()` [7] và tách thành `build_ms` (tạo bảng tiền tố hoặc automaton) và `elapsed_ms` (quét văn bản và tiêu thụ đủ các kết quả).
Việc tải tệp, giải mã UTF-8, kiểm tra NFC, sinh mẫu và oracle nằm ngoài vùng bấm giờ. Bộ gom rác Python giữ bật mặc định trong mọi lượt.

### B. Ba lượt đo tách biệt
Mỗi cấu hình được đo ở ba lượt, mỗi lượt trong một tiến trình mới: (i) *timing* — chỉ ghi thời gian, `count` và `check`; (ii) *count* — đếm số phép so sánh byte
(`comparisons`), số lần lùi theo Prefix Table hoặc Failure Link (`failure_steps`), số trạng thái và `lines_flagged`; (iii) *mem* — `tracemalloc` [8] bật ngay trước
`build` để lấy đỉnh bộ nhớ của vùng xây cấu trúc. `tracemalloc` chỉ theo dõi khối nhớ do Python cấp nên không đồng nhất với RSS của tiến trình. Thời gian chỉ lấy từ lượt *timing*.
Một "phép so sánh" là một lần thực thi phép đối chiếu giữa một byte văn bản và một byte mẫu **[XN D09]**.

### C. Thiết kế thực nghiệm
Ma trận RQ1–RQ3 như Bảng **[ĐIỀN: số bảng]**: RQ1 so BF và KMP trên T1 (tiếng Việt) và T3 σ = 26 với S = 1…16 MiB, m = 16 byte; RQ2 A thay σ ∈ {2, 4, 26, 256}
với m = 64 byte trên T3 4 MiB, RQ2 B thay m ∈ {8, 64, 1.024} trên T4 4 MiB; RQ3 so k-KMP và Aho–Corasick (Failure Link + Output Link) với `bytes.find` làm mốc,
k ∈ {1, 10, 100, 1.000} trên T1/T2 **[XN D16]**. Trong mỗi nhóm cấu hình, mọi thuật toán dùng cùng văn bản, cùng bộ mẫu và cùng bộ thu kết quả (`count`, `check`).
Với mỗi (cấu hình, seed) có một lượt làm nóng bị loại và ba lượt đo; thứ tự thuật toán xoay vòng giữa các lượt. Ba seed 11, 29, 47 được ghi trước khi chạy.
Lượt đo có tỉ lệ CPU-time/wall-time dưới ngưỡng **[ĐIỀN: 0,90]** bị coi là nhiễu, được lưu với nhãn *discarded* và đo lại tối đa **[ĐIỀN: 2]** lần.
Ca vượt thời hạn **[ĐIỀN: timeout]** giây được ghi `status = timeout`, không thay bằng 0.

### D. Tính đúng
Trước khi so hiệu năng, `count` và `check` của từng lượt được đối chiếu với oracle `bytes.find` (lần tìm tiếp theo bắt đầu ở `pos + 1` để giữ khớp chồng lấn);
`check = (check + (pos + 1) · 1.000.003 + pid) mod 2⁶⁴`. Ô nào lệch oracle bị loại khỏi so sánh hiệu năng. Chi tiết kiểm thử ở phần Validation (TV4).

### E. Chỉ số và tổng hợp thống kê
Thông lượng = (N / 2²⁰) / (elapsed_ms / 1.000) MiB/s, N là số byte thực tế. Speedup = t_baseline / t_candidate trên cùng cấu hình và cùng seed (> 1: candidate nhanh hơn).
Khi một bộ từ khóa được dùng lại r lần, tổng chi phí là build_ms + r × elapsed_ms; ngưỡng hòa vốn r\* = (build_c − build_b) / (scan_b − scan_c) chỉ được nêu khi
`build_c > build_b` và `scan_b > scan_c` đồng thời trong điều kiện đo. Với mỗi (cấu hình, seed) báo median, min, max của ba lượt đo; sau đó báo median và dải min–max giữa các seed.
Dao động do đo lặp và dao động giữa seed được báo riêng. Chín lượt đo từ ba seed **không** được coi là chín mẫu độc lập (với T1/T2, ba seed chung một corpus), và với ba seed
nhóm không đưa ra khoảng tin cậy hay kiểm định ý nghĩa; các so sánh được diễn giải ở mức mô tả.

### F. Tái lập
Mỗi dòng trong `raw_results.csv` mang `corpus_hash` (SHA-256 của tệp), `keyword_hash` (SHA-256 của danh sách mẫu có thứ tự), `seed`, `code_version` và `status`;
mã nguồn, dữ liệu thô và nhật ký máy được nộp kèm báo cáo.

## Giới hạn cần nêu ở Limitations (rút gọn từ `limitations.md`)
Ba seed chung corpus trên T1/T2; T1/T2 là tiền tố lồng nhau; một máy, Python thuần; `tracemalloc` ≠ RSS; bộ từ khóa trung tính chưa phải từ cấm đã xác thực;
`lines_flagged` không phải độ chính xác lọc; `bytes.find` chạy bằng C nên chỉ là mốc; DFA chỉ thảo luận lý thuyết nếu không cài đặt.

## Discussion — hai phân tích bắt buộc

### Vì sao Brute Force có thể ngang hoặc nhanh hơn KMP trên T1/T2
KMP có bảo đảm tuyến tính, nhưng tốc độ thực tế còn phụ thuộc hằng số triển khai. Trên văn bản tự nhiên, mismatch thường xảy ra sớm; Brute Force khi đó thực hiện ít phép so sánh Python cho mỗi vị trí. KMP phải duy trì trạng thái tiền tố và có nhánh lùi theo prefix table khi mismatch, nên chi phí điều khiển luồng có thể làm giảm lợi thế tiệm cận. Với mẫu ngắn, chênh lệch này có thể lấn át số phép so sánh tiết kiệm được. Đây là giải thích dựa trên cơ chế; chỉ được kết luận rằng BF ngang/nhanh hơn nếu timing chính thức trên T1/T2 xác nhận và `oracle_ok=1`.

### Đánh đổi bộ nhớ và tốc độ giữa Failure Link và DFA
Failure Link lưu cấu trúc chuyển thưa, nên bộ nhớ thường tăng theo số trạng thái và số cạnh thực tế; khi không có cạnh trực tiếp, quá trình quét có thể phải lần theo một hay nhiều failure link. DFA lưu chuyển trạng thái cho mọi ký tự trong alphabet, giúp tra chuyển trạng thái trực tiếp nhưng có thể cần bộ nhớ tỷ lệ với số trạng thái nhân kích thước alphabet. Vì vậy DFA có tiềm năng giảm chi phí chuyển trạng thái để đổi lấy bộ nhớ lớn hơn. Nhóm không cài và đo DFA 256 cột; phần này là phân tích thuật toán, không phải kết quả benchmark.

## Threats to Validity
T2 không hoàn toàn ASCII. Các corpus T3 với σ = 2, 4 và 256 được sinh bằng cùng seed 42, vì vậy không đại diện cho các lần lấy mẫu độc lập. Mẫu σ = 26 được cắt từ file 1 MiB trong khi corpus theo kích thước là độc lập; mẫu có thể gần như không xuất hiện trong file lớn hơn. Cần kiểm tra manifest và số occurrence thực tế trước khi diễn giải kết quả có hit/miss.

## Bảng lựa chọn thuật toán ở kết luận (TV2 tổng hợp — điền sau khi có kết quả)

| Tình huống | Thuật toán đề xuất | Bằng chứng (dòng trong summary.csv) | Chi phí bộ nhớ | Giới hạn |
| --- | --- | --- | --- | --- |
| Một mẫu, văn bản tự nhiên, quét một lần | **[ĐIỀN]** | **[ĐIỀN]** | **[ĐIỀN]** | **[ĐIỀN]** |
| Một mẫu bất lợi (lặp tiền tố) | **[ĐIỀN]** | **[ĐIỀN]** | **[ĐIỀN]** | **[ĐIỀN]** |
| k từ khóa, quét một lần | **[ĐIỀN]** | **[ĐIỀN]** | **[ĐIỀN]** | **[ĐIỀN]** |
| k từ khóa, dùng lại r lần | **[ĐIỀN: r\* nếu đo được]** | **[ĐIỀN]** | **[ĐIỀN]** | **[ĐIỀN]** |

Không điền trước "AC luôn tốt nhất"; không suy kết quả của một máy Python thuần sang ngôn ngữ, dữ liệu hay hệ thống huấn luyện LLM khác.
