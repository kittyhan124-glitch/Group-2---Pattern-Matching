# decisions.md — Nhật ký quyết định (TV2 ghi, cả nhóm xác nhận)

Trạng thái: **ĐX** = đề xuất vận hành của nhóm, chưa phải yêu cầu của giảng viên · **CẦN XN** = cần xác nhận (nhóm hoặc giảng viên) trước khi chạy chính thức ·
**ĐÃ CHỐT** = đã thống nhất · **QUAN SÁT** = sự thật đo được từ dữ liệu, không phải lựa chọn.
Mỗi dòng có chủ trì theo "Nhật ký làm rõ đề bài" của bản phân công. Ngày dùng định dạng dd/mm/2026.

| # | Vấn đề | Quyết định / quan sát | Lý do và hệ quả | Chủ | Trạng thái |
| --- | --- | --- | --- | --- | --- |
| D01 | Máy đo chính thức | Một máy của nhóm, một bản Python, cắm điện, không chạy việc khác. Số pilot trong gói này lấy từ máy sandbox (1 vCPU Xeon 2,30 GHz, Python 3.12.3) **chỉ để thử đường ống** | Không ghép số đo từ hai máy trong một bảng. `estimate` phải chạy lại trên máy chính thức vì tốc độ khác | TV2 | CẦN XN (chọn máy) |
| D02 | Seed | 11, 29, 47, ghi trước khi chạy | Theo bản phân công. Ý nghĩa của seed khác nhau theo ngữ liệu (xem D03) | TV2 | ĐÃ CHỐT |
| D03 | Seed không tạo ba corpus độc lập | T1/T2: 1 file, seed chỉ đổi vị trí mẫu/bộ từ khóa. T3 σ=26: seed đổi cả file. T3 σ=2/4/256: 1 file, seed đổi mẫu. T4: xác định, không seed | Ba seed trên T1/T2 **không** phải ba mẫu ngữ liệu độc lập ⇒ độ dao động giữa seed chỉ phản ánh khác biệt mẫu. Ghi vào Limitations | TV1+TV2 | QUAN SÁT |
| D04 | T4 và seed | Cột `seed` để trống; ba lượt đo là ba lần lặp. RQ2B có 6 ô, không nhân 3 | T4 xác định nên nhân seed chỉ lặp lại cùng phép đo | TV2 | ĐX |
| D05 | Số lượt đo | 1 warm-up + 3 đo/ô/seed, mỗi lượt một tiến trình mới, luân phiên thứ tự thuật toán | Theo hạn hai tuần. Warm-up lưu `mode=warmup`, loại khỏi thống kê | TV2 | ĐX |
| D06 | Kiểm soát nhiễu | `gc.disable()` trong vùng đo; `PYTHONHASHSEED=0`; tiến trình riêng cho timing/count/mem | Giảm dao động do GC; tách ba lượt theo bản phân công | TV2 | ĐX |
| D07 | Mẫu đơn RQ1/RQ2A | Cắt m byte từ 1 MiB đầu của file cùng họ, ranh giới UTF-8, không LF, theo seed | Giữ cùng mẫu qua các S. Trên T1 mẫu có mặt ở mọi S (file lồng nhau); trên T3 σ=26 mẫu thường chỉ có ở 1 MiB (file độc lập) ⇒ `count` khác nhau theo S, phải báo | TV1+TV2 | CẦN XN |
| D08 | Chế độ "mẫu vắng mặt" | Không đưa vào ma trận bắt buộc; thêm như cấu hình riêng nếu nhóm muốn | Bản phân công yêu cầu tách "mẫu có xuất hiện" và "mẫu vắng mặt", không trộn trung bình | TV1+TV2 | CẦN XN |
| D09 | Định nghĩa "phép so sánh" | Một lần thực thi phép đối chiếu một byte văn bản với một byte mẫu (AC: một lần tra cạnh); không đếm kiểm biên chỉ số | Cần cho `comparisons/N`; phải giống nhau ở BF, KMP, k-KMP. `failure_steps` đếm riêng, không cộng chung | TV2+TV3 | CẦN XN |
| D10 | Bộ thu kết quả | `Collector.hit` dùng chung, chỉ `count` + `check`; nằm trong `elapsed_ms` của mọi thuật toán | Bản phân công yêu cầu cùng quy tắc trả kết quả; chi phí này được công khai. `lines_flagged` chỉ ở lượt `count` | TV2 | ĐX |
| D11 | Timeout | 300 s/lượt timing (ĐX), 600 s lượt count, 300 s lượt mem. Ô quá hạn ghi `status=timeout`, không chạy bù | Pilot (stand-in, máy sandbox): BF m=1.024 trên T4 ≈ 176 s và kmp-k k=1.000 ở 4 MiB ≈ 195 s **dưới** hạn; kmp-k k=1.000 ở 16 MiB ≈ 790 s **vượt** hạn (6 ô RQ3). Có thể nâng timeout riêng cho 6 ô này (≥ 1.200 s) nếu thời gian cho phép — nhóm quyết | TV2 | CẦN XN |
| D12 | Bộ nhớ | `tracemalloc` chỉ cho vùng build; `mem_peak_bytes` ≠ RSS | Theo phạm vi của tracemalloc; nếu đo RSS thì cột riêng | TV2 | ĐÃ CHỐT (theo đề) |
| D13 | T3 σ=256 | Byte thô, không NFC/UTF-8; ngoại lệ ghi rõ | Khớp mục T3 trong bảng làm rõ; file thực tế không hợp lệ UTF-8 | TV1 | QUAN SÁT; CẦN XN GV |
| D14 | T2 không phải toàn ASCII | Giữ T2 gốc, báo tỷ lệ byte ≥ 128: 0,304 % (1 MiB) … 0,678 % (16 MiB) | Đúng yêu cầu "không giả định T2 toàn ASCII"; tỷ lệ tăng theo kích thước nên T2 nhỏ và lớn không đồng nhất hoàn toàn | TV1 | QUAN SÁT |
| D15 | T1/T2 là tiền tố lồng nhau | Các kích thước 1…8 MiB là tiền tố của 16 MiB | Đường cong theo S không tách được "kích thước" khỏi "nội dung nằm thêm" hoàn toàn; ghi vào Limitations | TV1+TV2 | QUAN SÁT |
| D16 | Quy mô RQ3 | T1 và T2 đều 4 và 16 MiB, mẫu 16 byte, k = 1, 10, 100, 1.000 | Đề xuất của bản phân công; cần xác nhận trước khi chạy | TV5 | CẦN XN |
| D17 | Bốn cài đặt RQ3 | kmp-k, ac fail, lib-find; ac dfa là mở rộng | Đề gốc chưa nêu rõ bốn tên | TV2 | CẦN XN GV |
| D18 | Bộ từ khóa RQ3 | Định dạng `keywords/kw_<lang>_seed<seed>_k<K>.txt`, một mẫu/dòng, lồng nhau. Bộ trong gói là **stub** | TV5 cấp bộ thật; khi thay phải chạy lại mọi ô RQ3 và tạo `raw_results.csv` mới | TV5 | CẦN XN |
| D19 | Oracle | Runner dùng oracle tối thiểu (`bytes.find`, bước pos+1) để gán `oracle_ok`; oracle của TV4 sẽ đối chiếu và thay thế | Tránh để hiệu năng đi trước tính đúng; TV4 vẫn là người đóng lỗi | TV2+TV4 | ĐX |
| D20 | Thiếu manifest | `data.zip` chỉ có file `.bin`; không có `corpus_manifest.json` | TV2 đã lập `data_hashes.csv` (SHA-256, UTF-8/NFC); TV1 cần bổ sung nguồn gốc (id bài, phiên bản, seed, dấu phân cách) | TV1 | CẦN TV1 |
| D21 | Thống kê | Median/min/max theo seed; dao động đo lặp và giữa seed báo riêng; speedup ghép cặp theo seed; không CI/kiểm định | 3 seed là quá ít để suy độ tin cậy cao | TV2 | ĐÃ CHỐT (theo đề) |
| D22 | Tái sử dụng bộ mẫu | Báo `build + r × scan`, r = 1, 5, 20; hòa vốn chỉ khi `build_c > build_b` và `scan_b > scan_c` | Điều kiện đo phải cho phép; không ngoại suy ngoài k, S đã đo | TV2+TV5 | ĐX |
| D23 | Khối lượng | 234 ô, 93 nhóm, 1.497 tiến trình (gồm lib-find, warm-up, count, mem, oracle) | Tính lại mỗi khi cấu hình đổi; pilot trên stand-in ước ≈ 4 giờ máy sandbox (chỉ mang tính tham khảo, xem `workload_estimate.csv`) | TV2 | ĐX |
| D24 | Mã stand-in | `algos_ref/` chỉ để thử runner; không dùng kết quả của nó làm số liệu báo cáo | Số trong `pilot_*` chạy trên stand-in, không phải mã của TV1/TV3/TV5 | TV2 | ĐÃ CHỐT |
