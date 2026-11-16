# QUY ĐỊNH CHUNG ĐỒ ÁN NHÓM — CSD203

**Học phần:** Data Structures and Algorithms with Python | **Lớp:** AI21B — Học kỳ Fall 2026

| Thông số | Quy định chi tiết |
|---|---|
| Học phần & Đối tượng | CSD203 — Cấu trúc dữ liệu và giải thuật với Python (Dành riêng cho sinh viên chuyên ngành Trí tuệ Nhân tạo - AI) |
| Lớp áp dụng & Học kỳ | AI21B — Học kỳ Fall 2026 (FA26) |
| Hình thức triển khai | Đồ án nghiên cứu thực nghiệm theo nhóm (6 sinh viên/nhóm; nhóm 5 người có quy chế điều chỉnh tải) |
| Thời gian thực hiện | 14 ngày làm việc tập trung (D0 đến D14) |
| Sản phẩm đầu ra cốt lõi | Báo cáo nghiên cứu theo chuẩn IEEE Conference Paper (tối đa 6 trang), mã nguồn Python thuần, bộ runner đo đạc tự động, dữ liệu và bộ kết quả CSV có khả năng tái lập độc lập 100% |

## 1. Mục tiêu và Triết lý Đồ án

Đồ án nhóm môn CSD203 được thiết kế nhằm đưa sinh viên ngành AI thoát khỏi lối mòn lập trình học thuật thụ động. Thay vì chỉ cài đặt các thuật toán mẫu trên quy mô nhỏ, đồ án đặt trọng tâm vào phương pháp Nghiên cứu Thực nghiệm có Kiểm soát (Controlled Empirical Evaluation) trên nền tảng ngôn ngữ Python — môi trường làm việc bản địa của kỹ sư AI.

Thông qua việc đối chiếu giữa các cấu trúc/giải thuật kinh điển trong giáo trình với các giải thuật tối tân đang vận hành trong thực tế (CPython Internals, Tokenizer LLM, NLP Data Filtering), sinh viên phải hoàn thành 4 năng lực cốt lõi:

1. **Hiểu sâu bản chất thuật toán:** Nắm vững cơ chế vận hành nội tại (CPython Internals), phân tích sâu độ phức tạp lý thuyết và truy vết chính xác thuật toán trên tập dữ liệu biên/dữ liệu nhỏ.
2. **Năng lực thiết kế thực nghiệm:** Xác định rõ ràng biến độc lập (yếu tố thay đổi), biến kiểm soát (giữ cố định) và biến phụ thuộc (thời gian xử lý, đỉnh bộ nhớ cấp phát, số phép tính toán) nhằm thiết lập quy trình đo đạc khách quan, tái lập được.
3. **Tiếp cận mã nguồn và tài liệu chuẩn:** Đọc trực tiếp tài liệu kỹ thuật chuẩn, đặc tả kỹ thuật và mã nguồn CPython chính thức để xác định rõ cơ chế cốt lõi và ánh xạ vào code cài đặt.
4. **Lập luận và kết luận khoa học:** Đưa ra các nhận định khoa học có điều kiện ràng buộc dựa trên số liệu đo thật; phân tích thấu đáo các trường hợp bất thường và chỉ rõ giới hạn của thực nghiệm.

## 2. Danh mục Đề tài Đồ án

Mỗi nhóm sinh viên đảm nhận một đề tài thuộc một chương kiến thức nâng cao sau Graph, gắn liền trực tiếp với bài toán thực tiễn của ngành AI:

| Đề | Tên đề tài nghiên cứu | Chương / CLO | Thuật toán giáo trình | Thuật toán thực tế ngoài Syllabus |
|---|---|---|---|---|
| Đề 1 | Sắp xếp dữ liệu gần có thứ tự trong Data Pipeline | Chương 6 / CLO6 | Quick Sort, Merge Sort, Heap Sort, Radix Sort | Timsort kết hợp chính sách gộp Powersort (Thuật toán chính thức của `list.sort` trong CPython) |
| Đề 2 | Bảng băm cho khóa có quy luật & Dò nhiễu loạn | Chương 7 / CLO7 | Separate Chaining, Linear Probing | Dò nhiễu loạn (Perturbation Probing) của `dict` trong CPython Internals |
| Đề 3 | Lọc dữ liệu huấn luyện NLP theo danh sách từ khóa | Chương 8 / CLO8 | Brute Force, KMP | Aho–Corasick Automaton (Quét đa mẫu trên ngữ liệu Wikipedia) |
| Đề 4 | Nén văn bản và Tokenizer mô hình ngôn ngữ (BPE) | Chương 8 / CLO8 | RLE, Huffman, LZW | Byte Pair Encoding (BPE Tokenizer họ GPT) |

## 3. Khung Ba Câu hỏi Nghiên cứu (Research Questions - RQ)

Mọi đề tài đều tuân thủ chặt chẽ cấu trúc 3 câu hỏi nghiên cứu chuẩn hóa:

| Câu hỏi | Bản chất khoa học | Yêu cầu thực nghiệm cụ thể |
|---|---|---|
| RQ1 | Khảo sát Định luật Tải (Scalability) | Khảo sát và so sánh hiệu năng của các thuật toán giáo trình khi quy mô dữ liệu N tăng dần qua ít nhất 5 mức tải. Đánh giá tính tiệm cận lý thuyết O(·) trên môi trường thực tế. |
| RQ2 | Khảo sát Độ nhạy Điều kiện (Condition Sensitivity) | Giữ cố định quy mô dữ liệu, chủ động thay đổi các đặc trưng của dữ liệu đầu vào (mức độ có thứ tự, tần suất trùng khóa, tính chất chuỗi, histogram) trên ít nhất 3 mức để xác định ranh giới đổi ngôi hiệu năng giữa các thuật toán. |
| RQ3 | Đánh giá Giải thuật Thực tế & Bóc tách Cơ chế (Ablation Study) | So sánh giải thuật thực tế tiên tiến với các giải thuật giáo trình trên cùng giao thức đo chuẩn. Bắt buộc thực hiện thí nghiệm bóc tách cơ chế (ablation study): tắt lần lượt từng kỹ thuật tối ưu thành phần để lượng hóa chính xác mức độ đóng góp của kỹ thuật đó. |

## 4. Tổ chức Nhóm và Quy chuẩn Phân công

- **Phân cặp chuyên trách:** Mỗi nhóm gồm 6 thành viên, bắt buộc phân tách thành 3 cặp (Pair Programming). Mỗi cặp phụ trách trọn vẹn một module thuật toán và chủ trì phân tích một câu hỏi nghiên cứu tương ứng (Cặp 1: RQ1, Cặp 2: RQ2, Cặp 3: RQ3).
- **Trách nhiệm chéo:** Trong mỗi cặp, hai thành viên luân phiên vai trò Cài đặt (Implementer) và Kiểm thử (Tester/Reviewer). Nghiêm cấm tuyệt đối phân công thụ động (như một người chỉ viết code, một người chỉ làm slide/soạn văn bản).
- **Minh bạch đóng góp:** Cặp phụ trách phải review chéo mã nguồn và kiểm thử của cặp khác. Toàn bộ thông tin phân công, vai trò cụ thể, commit log và module thực hiện phải được công khai minh bạch trong file `PHAN_CONG.md`.
- **QUY CHẾ NHÓM 5 NGƯỜI:** Đối với nhóm có 5 sinh viên: Một cặp sẽ có 1 thành viên. Nhóm được hưởng quy chế giảm tải phạm vi kỹ thuật được ghi rõ trong đặc tả riêng của từng đề tài (ví dụ: bỏ cơ chế Galloping ở Đề 1, bỏ mở rộng bảng ở Đề 2, bỏ biến thể DFA ở Đề 3, hoặc bỏ bộ đếm `noheap` ở Đề 4).

## 5. Môi trường Kỹ thuật và Quy tắc Lập trình

- **Phiên bản Python:** Toàn bộ nhóm phải thống nhất một phiên bản CPython chính thức từ 3.11 trở lên (khuyến nghị 3.11 hoặc 3.12). Nghiêm cấm dùng PyPy hoặc các trình thông dịch có JIT để đảm bảo tính nhất quán của bộ đo.
- **Nguyên tắc Pure Python:** Toàn bộ giải thuật khảo sát bắt buộc phải được cài đặt bằng Python thuần (Pure Python). Tuyệt đối không sử dụng thư viện viết bằng C (NumPy, SciPy, Numba, Cython) trong phạm vi thuật toán khảo sát. Các thư viện có sẵn của Python (`sorted`, `list.sort`, `dict`, `bytes.find`, `zlib`) CHỈ ĐƯỢC PHÉP dùng làm mốc đối chứng (Oracle/Baseline) với tiền tố `lib-`.
- **Xử lý đệ quy:** Tuyệt đối không sử dụng `sys.setrecursionlimit` để che giấu lỗi tràn ngăn xếp do giải thuật đệ quy chưa tối ưu. Khi gặp lỗi đệ quy, hệ thống ghi nhận trạng thái crash.
- **Cách ly tiến trình:** Chỉ đo thuật toán đơn luồng (single-thread), không sử dụng multi-threading hay multi-processing trong vùng đo thực nghiệm.

## 6. Tiêu chuẩn Bộ đo Tự động (Benchmark Harness)

Nhóm phải tự phát triển script đo đạc tự động (`runner.py`) đảm bảo các nguyên tắc thực nghiệm nghiêm ngặt sau:

- **Cô lập tiến trình & Timeout:** Mỗi lượt đo cấu hình phải được kích hoạt độc lập trong một tiến trình riêng biệt thông qua `subprocess.run([sys.executable, ...], timeout=60)`. Nếu vượt quá 60 giây, runner tự động ngắt và gán trạng thái `timeout`.
- **Đo lường thời gian chính xác:** Sử dụng hàm thời gian có độ phân giải nano-giây `time.perf_counter_ns()`. Phạm vi đo CHỈ bao bọc đúng khối lệnh thực thi thuật toán. Tuyệt đối không tính thời gian sinh dữ liệu, nạp file, in ấn màn hình hay ghi CSV vào thời gian chạy.
- **Quản lý Garbage Collection:** Bộ thu gom rác tự động của Python (Garbage Collector) bắt buộc giữ ở trạng thái bật mặc định (default). Không sử dụng lệnh `timeit` tắt GC làm sai lệch thực tế.
- **Đo bộ nhớ đỉnh (Peak Memory):** Đo lường bộ nhớ đỉnh cấp phát thêm bằng thư viện chuẩn `tracemalloc`. Vì `tracemalloc` gây overhead rất lớn, lượt đo bộ nhớ bắt buộc phải chạy ở một lượt tiến trình riêng biệt với cờ `--mem` (không đo gộp cùng lượt đo thời gian).
- **Đo số phép toán (Operations Count):** Đếm số phép so sánh, số lần dò ô, số lượt truy cập mảng CHỈ được kích hoạt trong lượt riêng biệt với cờ `--count`. Lượt đo thời gian chuẩn phải tắt toàn bộ bộ đếm.
- **Lặp lại và Phục hiện:** Mỗi cấu hình chính thức chạy lặp lại 3 lượt với 3 seed ngẫu nhiên khác nhau. Báo cáo trong paper phải nêu đủ giá trị Trung vị (Median), Min và Max.

| Mã trạng thái (`status`) | Ý nghĩa kỹ thuật | Quy định xử lý số liệu |
|---|---|---|
| `ok` | Hoàn thành trọn vẹn và kết quả trùng khớp 100% với Oracle | Ghi nhận đầy đủ thời gian `elapsed_ms` và tổng kiểm tra |
| `timeout` | Tiến trình bị ngắt cưỡng bức do vượt ngưỡng 60 giây | Để trống thời gian, ghi nhận điểm đo '> 60s' trên biểu đồ |
| `crash` | Tiến trình kết thúc bất thường (lỗi `RecursionError`, v.v.) | Ghi nhận nguyên nhân lỗi; là kết quả hợp lệ để phân tích ranh giới thuật toán |
| `oom` | Tiến trình bị tràn bộ nhớ (`MemoryError`) | Ghi nhận ngưỡng phá hủy của thuật toán |
| `wrong` | Thuật toán chạy xong nhưng sai lệch kết quả so với Oracle | Xác định lỗi cài đặt; không được dùng để tính tốc độ |

## 7. Cấu trúc Báo cáo Khoa học (IEEE Conference Paper)

Bài báo cáo là sản phẩm học thuật cao nhất của đồ án, được soạn thảo theo định dạng chuẩn IEEE Conference (2 cột, tối đa 6 trang nội dung):

- **Title, Abstract & Keywords (Tiếng Anh bắt buộc):** Tiêu đề mang tính nghiên cứu cụ thể, tóm tắt cô đọng 150–250 từ (vấn đề, phương pháp, số liệu định lượng, kết luận chính) và 3–5 từ khóa chuyên môn.
- **Section I. Introduction:** Nêu rõ bối cảnh ứng dụng trong AI, phát biểu câu hỏi nghiên cứu chung và chi tiết hóa 3 RQ.
- **Section II. Background & Related Work:** Cơ sở lý thuyết thuật toán giáo trình và phân tích sâu cơ chế của thuật toán mới từ nguồn tài liệu gốc.
- **Section III. Methods:** Quy ước cài đặt, mã giả các hàm cốt lõi, phân tích độ phức tạp lý thuyết, bảng ánh xạ các cơ chế kỹ thuật vào hàm mã nguồn cụ thể.
- **Section IV. Experimental Setup:** Mô tả máy đo, phiên bản CPython, cấu hình dữ liệu, seed, phương thức làm nóng, timeout, kiểm soát GC.
- **Section V. Results & Discussion:** Ba tiểu mục trả lời trực tiếp RQ1, RQ2, RQ3; đối chiếu thẳng thắn với giả thuyết nghiên cứu ban đầu; giải thích thuyết phục các kết quả trái dự đoán.
- **Section VI. Threats to Validity:** Phân tích thẳng thắn các yếu tố gây nhiễu (GC, OS), giới hạn của Python thuần và phạm vi suy rộng kết quả.
- **Section VII. Conclusion:** Đưa ra khuyến nghị lựa chọn thuật toán có điều kiện ràng buộc dựa trên bằng chứng thực nghiệm rõ ràng.
- **Acknowledgment (Tuyên bố sử dụng AI):** Khai báo minh bạch các công cụ AI hỗ trợ, phạm vi ứng dụng và quy trình kiểm chứng của nhóm.

## 8. Quy chuẩn Gói Nộp và Cấu trúc Thư mục

Gói sản phẩm nộp của nhóm phải được tổ chức khoa học theo đúng cấu trúc sau:

- `paper/`: Bao gồm bản PDF chính thức và file nguồn (.docx hoặc .tex).
- `src/`: Toàn bộ mã nguồn thuật toán, phân chia rõ ràng theo từng cặp và module.
- `tests/`: Bộ kiểm thử tự động với unit test, test ca biên và test đối chiếu Oracle.
- `bench/`: Bộ runner tự động, kịch bản benchmark và các script vẽ biểu đồ trực tiếp từ CSV.
- `results/`: Chứa toàn bộ dữ liệu CSV gốc đo đạc thực tế (`raw/`) và hình biểu đồ vector/ảnh độ phân giải cao (`figures/`).
- `data/`: Chứa script generator dữ liệu, tài liệu hướng dẫn tải ngữ liệu công khai và mã kiểm tra SHA-256.
- `README.md`: Tài liệu kỹ thuật tổng thể: phiên bản Python, hướng dẫn cài đặt môi trường, lệnh chạy test và lệnh chạy kiểm chứng một cấu hình bất kỳ trong dưới 60 giây.

## 9. Kế hoạch Tiến độ 14 Ngày

| Giai đoạn | Nhiệm vụ trọng tâm | Sản phẩm bàn giao bắt buộc |
|---|---|---|
| D0 – D2 | Nghiên cứu tài liệu gốc, phân công 3 cặp, thống nhất giao diện code, khởi tạo khung IEEE paper | Kế hoạch nghiên cứu 1 trang (3 RQ, giả thuyết nghiên cứu, bảng phân công) |
| D3 – D6 | Cài đặt thuật toán giáo trình, thuật toán mới, viết generator và bộ runner đo đạc; soạn mục Methods | 100% thuật toán vượt qua bộ test tính đúng; runner sinh được file CSV mẫu hợp lệ |
| D7 | Kiểm tra tiến độ trên lớp (10 phút/nhóm) | Vấn đáp tiến độ: chạy test đúng, demo chạy runner 1 cấu hình và trình bày kế hoạch đo đạc |
| D8 – D10 | Chạy thực nghiệm toàn diện RQ1, RQ2, RQ3 và thí nghiệm bóc tách cơ chế; thu thập CSV | Dữ liệu CSV thô hoàn chỉnh của 3 RQ |
| D11 – D12 | Chạy script sinh biểu đồ tự động; hoàn thiện mục Results, Discussion, Threats và Conclusion | Bản dự thảo hoàn chỉnh bài báo IEEE |
| D13 | Review chéo giữa các cặp, kiểm tra đối chiếu tài liệu trích dẫn, chạy hồi quy toàn bộ test suite | Gói nộp hoàn chỉnh đã đóng gói |
| D14 | Nộp bài chính thức và tham gia buổi Bảo vệ Đồ án | Bảo vệ đồ án trực tiếp trước Giảng viên |

## 10. Quy trình Bảo vệ và Vấn đáp Cá nhân

Buổi bảo vệ đồ án diễn ra trực tiếp (40 phút cho nhóm 6 người, 35 phút cho nhóm 5 người):

- **Trình bày nhóm (5 phút):** Nhóm trình bày câu hỏi chung, kết quả then chốt của 3 RQ và ít nhất 1 kết quả thực nghiệm trái với dự đoán ban đầu.
- **Kiểm tra tái lập thực nghiệm (3 phút):** Giảng viên chọn ngẫu nhiên 1 dòng kết quả trong file CSV đã nộp. Nhóm phải chạy lại cấu hình đó trên máy đo chính trước sự chứng kiến của Giảng viên. Kết quả được công nhận khi `status` và `output_check` trùng khớp 100%, thời gian xử lý nằm trong biên độ 0.5× đến 2.0× so với median đã nộp.
- **Vấn đáp cá nhân độc lập (5 phút/sinh viên):** Từng sinh viên vấn đáp độc lập trong 5 phút (không dùng AI, không trợ giúp): giải thích phần việc của mình, truy vết thuật toán trên dữ liệu nhỏ, thực hiện một thay đổi nhỏ trong mã nguồn và giải thích ý nghĩa kết quả.

## 11. Thang điểm Đánh giá Toàn diện

| Hạng mục đánh giá | Trọng số | Chi tiết tiêu chí chấm điểm |
|---|---|---|
| 1. Cài đặt & Tính đúng | 1.5 điểm | Thuật toán giáo trình đúng chuẩn: 0.5 \| Thuật toán mới đủ cơ chế & biến thể: 0.5 \| Bộ test ca biên, đối chiếu Oracle: 0.5 |
| 2. Bộ đo & Khả năng Tái lập | 1.5 điểm | Runner chuẩn hóa (tiến trình, GC, timeout): 0.5 \| CSV chuẩn, biểu đồ tái lập từ script: 0.5 \| Chạy lại thực nghiệm khớp: 0.5 |
| 3. Kết quả & Biện giải Khoa học | 2.0 điểm | RQ1 hoàn chỉnh: 0.5 \| RQ2 hoàn chỉnh: 0.5 \| RQ3 & Ablation Study: 0.5 \| Biện luận Discussion & Threats sâu sắc: 0.5 |
| 4. Báo cáo Chuẩn IEEE | 1.0 điểm | Đúng mẫu IEEE, giới hạn trang, Abstract tiếng Anh: 0.5 \| Trích dẫn chuẩn, tài liệu xác thực, khai báo AI: 0.5 |
| **TỔNG ĐIỂM NHÓM** | **6.0 điểm** | Đánh giá chung toàn bộ nhóm |
| 5. Giải thích phần đảm nhiệm | 1.0 điểm | Hiểu và giải thích rõ ràng code, test, số liệu phần mình phụ trách |
| 6. Truy vết thuật toán | 1.0 điểm | Truy vết chính xác từng bước chạy thuật toán trên input kiểm tra của Giảng viên |
| 7. Sửa mã nguồn & Thử nghiệm | 1.0 điểm | Thực hiện chỉnh sửa mã nguồn theo yêu cầu và giải thích đúng kết quả chạy test |
| 8. Diễn giải & Suy luận số liệu | 1.0 điểm | Dự đoán và giải thích logic xu hướng của một cấu hình thực nghiệm mới |
| **TỔNG ĐIỂM CÁ NHÂN** | **4.0 điểm** | Đánh giá năng lực độc lập của từng sinh viên |
| **ĐIỂM TỔNG HỌC PHẦN** | **10.0 điểm** | Điểm sinh viên = Điểm nhóm (0 - 6.0) + Điểm cá nhân (0 - 4.0) |
