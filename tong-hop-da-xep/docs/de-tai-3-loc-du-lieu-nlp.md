# ĐỀ TÀI 3: LỌC DỮ LIỆU HUẤN LUYỆN NLP THEO DANH SÁCH TỪ KHÓA

**Học phần:** CSD203 (Data Structures and Algorithms with Python) | **Lớp:** AI21B — FA26

| Hạng mục | Nội dung quy định |
|---|---|
| Tên đề tài chính thức | Khảo sát thực nghiệm các thuật toán khớp mẫu chuỗi và Automaton Aho–Corasick trong bài toán Lọc dữ liệu Huấn luyện Mô hình Ngôn ngữ |
| Chương / Chuẩn đầu ra | Chương 8: String Pattern Matching \| CLO8 |
| Thuật toán giáo trình | Brute Force String Matching, Knuth–Morris–Pratt (KMP), k-KMP |
| Thuật toán ngoài Syllabus | Aho–Corasick Automaton (Cấu trúc Trie kết hợp Failure Link và Output Link) |
| Ngữ liệu thực tế | Ngữ liệu Wikipedia tiếng Việt (chứa ký tự có dấu Unicode) và Wikipedia tiếng Anh; chuẩn hóa Unicode NFC |

## 1. Bối cảnh Kỹ thuật và Tầm quan trọng trong Huấn luyện AI/LLM

Trong quy trình tiền xử lý và làm sạch dữ liệu (Data Preprocessing & Cleansing) trước khi huấn luyện các Mô hình Ngôn ngữ Lớn (LLM), bài toán lọc dữ liệu theo danh mục từ khóa (Corpus Filtering) là một mắt xích tối quan trọng: phát hiện và loại bỏ các đoạn văn bản độc hại, ngôn từ kích động, lọc thông tin nhận dạng cá nhân (PII), hoặc gắn nhãn phân loại chủ đề. Trong các bài toán này, danh mục từ khóa cần tìm kiếm đồng thời có thể lên tới hàng trăm, thậm chí hàng nghìn từ/cụm từ, trong khi kho ngữ liệu văn bản cần quét có quy mô khổng lồ.

Các thuật toán khớp mẫu kinh điển như Brute Force hoặc Knuth–Morris–Pratt (KMP) được thiết kế cho bài toán tìm kiếm đơn mẫu (Single Pattern Matching). Khi áp dụng vào bài toán thực tế chứa k mẫu từ khóa, việc chạy lặp k lần KMP (k-KMP) sẽ dẫn đến độ phức tạp O(k × N), gây nghẽn cổ chai nghiêm trọng trong data pipeline.

Thuật toán Aho–Corasick (1975) đã giải quyết triệt để bài toán này bằng cách tổng quát hóa bảng Failure của KMP lên cấu trúc cây Trie chứa toàn bộ tập từ khóa. Automaton này cho phép quét toàn bộ kho văn bản chỉ trong đúng một lượt duyệt duy nhất (Single-pass Streaming) với độ phức tạp tuyến tính O(N + L + Z) độc lập với số lượng từ khóa k.

## 2. Ba Câu hỏi Nghiên cứu Trọng tâm (Research Questions)

Nhóm phải trả lời câu hỏi tổng quát: *Làm thế nào để tìm kiếm đầy đủ và chính xác một hoặc hàng nghìn từ khóa trong kho ngữ liệu văn bản tiếng Việt và tiếng Anh với thông lượng tối ưu khi được cài đặt bằng Python thuần?*

| Mã RQ | Câu hỏi nghiên cứu chi tiết | Biến độc lập (Thay đổi) | Biến kiểm soát (Cố định) |
|---|---|---|---|
| RQ1 | Brute Force và KMP khác biệt như thế nào về thời gian thực thi, thông lượng (Throughput) và số phép so sánh byte khi kích thước văn bản tăng trưởng tuyến tính? | Quy mô văn bản S = 1; 2; 4; 8; 16 MiB trên ngữ liệu T1 (Tiếng Việt) và T3 (Ngẫu nhiên) | Độ dài từ khóa cố định 16 byte, 3 seed ngẫu nhiên |
| RQ2 | Kích thước bảng chữ cái σ, độ dài từ khóa m và cấu trúc tiền tố lặp lại ảnh hưởng như thế nào đến sự chênh lệch hiệu năng giữa Brute Force và KMP? | Thí nghiệm A: Bảng chữ cái σ = 2; 4; 26; 256 (mẫu 64 byte) \| Thí nghiệm B: Dữ liệu bất lợi T4 với độ dài mẫu m = 8; 64; 1.024 byte | Kích thước văn bản cố định S = 4 MiB |
| RQ3 | Khi tìm kiếm k từ khóa đồng thời, Aho–Corasick vượt trội k-KMP như thế nào về thời gian tiền xử lý, thời gian quét và bộ nhớ? Sự đánh đổi giữa biến thể dùng Failure Link và biến thể DFA đầy đủ là gì? | Số lượng từ khóa k = 1; 10; 100; 1.000; đối chiếu 4 cài đặt tại Bảng 3 | Ngữ liệu Wikipedia T1 (4 MiB và 16 MiB) và T2 (Tiếng Anh) |

## 3. Quy chuẩn Kỹ thuật Cài đặt Thuật toán

- **Chuẩn hóa Unicode NFC bắt buộc:** Toàn bộ văn bản và từ khóa bắt buộc phải được chuẩn hóa Unicode về định dạng chuẩn NFC bằng thư viện chuẩn: `unicodedata.normalize('NFC', text)`, sau đó mã hóa UTF-8 thành chuỗi byte (`bytes`). Tiếng Việt chứa nhiều tổ hợp dấu thanh khác nhau; nếu không chuẩn hóa NFC, việc khớp mẫu sẽ sai lệch hoàn toàn.
- **Khớp mẫu trên mức Byte:** Thuật toán vận hành trực tiếp trên mảng byte (`bytes`). Vị trí khớp mẫu được tính bằng offset byte bắt đầu từ 0.
- **Khớp mẫu chồng lấn:** Thuật toán phải báo cáo đầy đủ mọi vị trí xuất hiện, kể cả các vị trí xuất hiện chồng lấn nhau (overlapping matches).

| Thuật toán | Tên CSV | Yêu cầu kỹ thuật bắt buộc |
|---|---|---|
| Brute Force | `bf` | So khớp trượt từ trái sang phải tại mọi vị trí byte của văn bản; dừng ngay khi gặp byte sai khớp đầu tiên. |
| KMP | `kmp` | Xây dựng bảng hàm chuyển (Failure function / Prefix table) theo đúng giáo trình chuẩn. |
| k-KMP | `kmp-k` | Mốc so sánh cho bài toán đa mẫu: Quét văn bản một lượt duy nhất; tại mỗi byte, cập nhật đồng thời trạng thái của k máy KMP độc lập (không duyệt lại văn bản k lần). |
| Aho–Corasick (Failure Link) | `ac (fail)` | Cây Trie trên byte. Mỗi nút lưu các cạnh chuyển trong một dict. Xây dựng Failure Link bằng BFS; sử dụng Output Link (Dictionary Suffix Link) để báo đủ các mẫu con. |
| Aho–Corasick (DFA đầy đủ) | `ac (dfa)` | Biến thể tính trước bảng chuyển trạng thái 256 cột (DFA) theo Thuật toán 4 trong bài báo gốc của Aho & Corasick [2]. Khi quét chỉ tra bảng 1 bước. |
| Mốc thư viện | `lib-find` | Hàm `bytes.find()` viết bằng C của Python. Dùng làm mốc Oracle kiểm tra tính đúng. |

## 4. Thiết kế Ngữ liệu Thực nghiệm và Danh mục Từ khóa

| Mã | Tên ngữ liệu | Nguồn dữ liệu & Đặc tính kiểm thử |
|---|---|---|
| T1 | Wikipedia tiếng Việt | Tập dữ liệu chuẩn `wikimedia/wikipedia` (cấu hình `20231101.vi` trên Hugging Face). Nối các bài viết, chuẩn hóa NFC, mã hóa UTF-8. Đặc trưng bởi các ký tự đa byte tiếng Việt có dấu. |
| T2 | Wikipedia tiếng Anh | Tương tự T1 với cấu hình `20231101.en`. Toàn bộ là ký tự ASCII đơn byte; dùng đối chứng trong RQ3. |
| T3 | Ngẫu nhiên đều σ ký hiệu | Chuỗi byte sinh ngẫu nhiên đều từ σ ký tự đầu tiên (σ = 2; 4; 26; 256). |
| T4 | Dữ liệu cấu trúc bất lợi | Văn bản toàn bộ là byte `a`; từ khóa gồm m - 1 byte `a` và kết thúc bằng byte `b` (kịch bản trường hợp xấu nhất của Brute Force). |

## 5. Yêu cầu Kiểm thử và Xác thực Oracle

- **Ca kiểm thử biên cố định:** Mọi thuật toán bắt buộc phải vượt qua các ca biên cố định: mẫu rỗng báo lỗi, văn bản `aaaaa` khớp `aaa` tại 0, 1, 2; văn bản `abababab` khớp `abab` tại 0, 2, 4; văn bản `ushers` khớp tập từ khóa {`he`, `she`, `his`, `hers`}; văn bản tiếng Việt dạng NFD khớp mẫu dạng NFC.
- **Fuzzing Test ngẫu nhiên:** Sinh ngẫu nhiên 10.000 cặp văn bản và từ khóa ngẫu nhiên; đối chiếu kết quả khớp mẫu tuyệt đối với hàm chuẩn `bytes.find()`.
- **Mã băm tổng kiểm tra:** Tổng kiểm tra đầu ra được tính độc lập với thứ tự phát hiện: mỗi lần khớp tại vị trí `pos` với mã mẫu `pid`, cộng dồn: `check = (check + (pos + 1) * 1000003 + pid) % (2**64)`. Mọi thuật toán phải cho ra cùng `count` và `check`.
- **Chỉ số lọc dữ liệu thực tế:** Ghi nhận chỉ số ứng dụng thực tế: số lượng dòng văn bản bị đánh dấu chứa từ khóa cấm (`lines_flagged`).

## 6. Chỉ số Đo lường và Biện giải Khoa học

- **Thời gian & Thông lượng:** Thời gian quét văn bản thuần túy `elapsed_ms`, thời gian xây dựng cấu trúc `build_ms`, Thông lượng MiB/giây.
- **Số phép tính toán:** Tỷ lệ số phép so sánh byte trên tổng số byte văn bản (với BF, KMP); số lần chuyển trạng thái và số lần lùi Failure Link (với Aho–Corasick) đo ở lượt `--count`.
- **Chi phí Automaton:** Số lượng trạng thái của Trie và bộ nhớ đỉnh `mem_peak_bytes` khi xây dựng Automaton ở lượt `--mem`.

**YÊU CẦU THẢO LUẬN BẮT BUỘC:** Trong phần Discussion của báo cáo IEEE, nhóm bắt buộc phải phân tích:

1. Tại sao trên văn bản tự nhiên T1 và T2, Brute Force lại có tốc độ ngang ngửa hoặc thậm chí nhanh hơn KMP (do phần lớn các phép so sánh đều sai khớp ngay ở byte đầu tiên, khiến overhead quản lý vòng lặp KMP trở nên bất lợi);
2. Phân tích sự đánh đổi bộ nhớ vs. tốc độ giữa biến thể Failure Link và biến thể DFA đầy đủ của Aho–Corasick.

## 7. Phân công Trách nhiệm và Quy chế Nhóm 5 Người

| Cặp phụ trách | Nhiệm vụ Cài đặt & Kiểm thử | Chủ trì phân tích |
|---|---|---|
| Cặp 1 | Cài đặt Brute Force, pipeline tải và chuẩn hóa T1, T2, generator T3, T4, bộ runner | Chủ trì thực nghiệm & viết báo cáo RQ1 |
| Cặp 2 | Cài đặt KMP, k-KMP, bộ test Fuzzing ngẫu nhiên đối chiếu Oracle | Chủ trì thực nghiệm & viết báo cáo RQ2 |
| Cặp 3 | Cài đặt Aho–Corasick (fail và dfa), bộ trích xuất từ khóa, chỉ số `lines_flagged` | Chủ trì thực nghiệm & viết báo cáo RQ3 |

**Quy chế cho nhóm 5 sinh viên:** Cặp 3 chỉ gồm 1 thành viên. Nhóm được phép miễn giảm cài đặt biến thể DFA 256 cột; Aho–Corasick chỉ cần cài đặt biến thể Failure Link (`fail`).

## 8. Tài liệu Tham khảo Bắt buộc

[1] D. E. Knuth, J. H. Morris, and V. R. Pratt, "Fast pattern matching in strings," *SIAM Journal on Computing*, vol. 6, no. 2, pp. 323–350, 1977.

[2] A. V. Aho and M. J. Corasick, "Efficient string matching: An aid to bibliographic search," *Communications of the ACM*, vol. 18, no. 6, pp. 333–340, 1975.

[3] M. T. Goodrich, R. Tamassia, and M. H. Goldwasser, *Data Structures and Algorithms in Python*. Wiley, 2013, ch. 13.

[4] Wikimedia Foundation, "wikimedia/wikipedia," Hugging Face Datasets. [Online]. https://huggingface.co/datasets/wikimedia/wikipedia
