# TV4 validation implementation plan

Goal: hoàn thành các công cụ, kiểm chứng và tài liệu TV4 theo SCOPE.md trên TV4-Tuan.
Spec: docs/tv4/SCOPE.md. Python 3.10+, standard library, giữ nguyên module TV1/TV3/TV5 và nhánh TV2.

## Task 1 Oracle và chuẩn hóa

- [x] Viết test đáp án tay cho overlap, pid trùng, checksum, dòng, NFC/NFD, kiểu sai và mẫu rỗng; xem test fail khi thiếu oracle.
- [x] Thêm oracle.py: oracle_find(text, patterns), iter_matches, checksum, summarize_matches; thêm tv4/preprocessing.py: prepare_keywords.
- [x] Chạy test mới và test_kmp gốc; commit.

## Task 2 Kiểm chứng thuật toán và hồ sơ từ khóa

- [x] Viết test literal cho keyword statistics, line fixture và phân loại lỗi validator; xem fail trước khi có module.
- [x] Thêm tv4/keyword_analysis.py, adapters.py, validate.py; fixed edge, fuzz generator, shrinker, source hashes, issue records.
- [x] Kiểm các cài đặt chuẩn và raw contract riêng; chạy 30.000 ca tổng ba seed; ghi báo cáo không che lỗi; commit.

## Task 3 Đối chiếu TV2 và bàn giao

- [x] Viết test CSV sai throughput, checksum lớn, warmup loại khỏi thống kê và timeout không điền 0; xem fail.
- [x] Thêm tv4/review_tv2.py kiểm oracle và CSV bằng stdlib; chạy trên snapshot TV2 bên ngoài nhánh.
- [x] Hồ sơ stub từ khóa, Validation, tiến độ bằng chứng theo member, hướng dẫn chạy; kiểm full suite, reviewer độc lập, commit và push TV4-Tuan.

## Review focus

Mẫu rỗng ở mọi entrypoint; mẫu trùng đổi pid; NFC và byte offset; LF và CRLF; checksum 64 bit không qua float; báo cáo không gọi pilot/stub là chính thức; đường dẫn và file thiếu báo dependency; fuzz không bỏ oracle sai; tiến độ không quy trách nhiệm từ author.
