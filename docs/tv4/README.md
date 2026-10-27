# Hướng dẫn bàn giao TV4 Tuan

Phần TV4 gồm oracle độc lập, chuẩn hóa bộ mẫu, kiểm thử mã thật, hồ sơ từ khóa và đối chiếu dữ liệu TV2. Nhánh `TV4-Tuan` được tạo từ main `2ca31d9`; không đổi mã BF/KMP/k-KMP/AC của các thành viên. Các phần chưa nộp của thành viên khác được ghi là phụ thuộc, không gộp thành lỗi thuật toán.

## Chạy trên máy nhóm

Python 3.10+, chỉ thư viện chuẩn. Đứng ở thư mục gốc repo. Trên Windows dùng `py`; có thể thay bằng `python` hoặc `python3` tùy máy.

```powershell
py -B -X utf8 -m unittest discover -v
py -B -X utf8 -m tv4.validate --seed 11 --fuzz-cases 10000 --out docs/tv4/reports/my_seed11
py -B -X utf8 -m tv4.validate --seed 29 --fuzz-cases 10000 --out docs/tv4/reports/my_seed29
py -B -X utf8 -m tv4.validate --seed 47 --fuzz-cases 10000 --out docs/tv4/reports/my_seed47
```

**Hai loại kết quả khác nhau:** unittest xác nhận bộ công cụ và các test gốc chạy đúng; validator đánh giá mã thành viên và các hợp đồng còn mở. Validator trả mã 1 và trạng thái `canonical_pass_contract_issues_open` nếu tìm kiếm trên mẫu chuẩn đạt nhưng vẫn còn vấn đề hợp đồng/phần đếm chưa có. Không đổi mã 1 thành pass hoặc xóa các vấn đề để làm báo cáo xanh.

Mỗi seed chạy 10.000 input, chia đều 2.500 ca cho byte bảng chữ cái nhỏ, byte đủ 256 giá trị, Unicode NFC/NFD và tiền tố/hậu tố/overlap. So đầy đủ danh sách cặp pos/pid. BF/KMP được gọi riêng từng mẫu chỉ để so đáp án; k-KMP thật vẫn quét một lượt. Mỗi ca thứ 10 kiểm thêm chế độ đếm BF/KMP/k-KMP. Ca biên có cả mẫu 1.024 byte trên T4 nhỏ.

## Module và quy ước

| File | Vai trò |
|---|---|
| `oracle.py` | `oracle_find`, `iter_matches`, `checksum`, `summarize_matches`; byte, overlap, giữ pid gốc |
| `tv4/preprocessing.py` | NFC→UTF-8, loại trùng tập trung, ánh xạ dòng mẫu gốc sang pid chuẩn |
| `tv4/adapters.py` | Đọc kết quả từ module thật; không phải mã thay thế hoặc adapter đo thời gian |
| `tv4/validate.py` | Ca biên/fuzzing, thu nhỏ lỗi, hash mã, kiểm hợp đồng và fixture dòng |
| `tv4/keyword_analysis.py` | k, L, độ dài, biên mẫu, Trie và tiền tố chung, tần suất nếu có corpus |
| `tv4/review_tv2.py` | So oracle/LineCollector TV2 và tính lại throughput, median, speedup, tổng chi phí bằng stdlib |
| `test_tv4*.py` | Test công cụ TV4 bằng các giá trị biết trước |

Offset tính trên byte của bản sau NFC. Oracle bytes không tự normalize, lowercase hoặc loại trùng. `prepare_keywords` mới thực hiện chuẩn hóa/loại trùng; metadata lưu `source_to_pid`. Bộ mẫu chính không chứa LF. Số dòng là tách bằng LF, có dòng rỗng cuối. `lines_flagged` là số dòng có hit, không phải độ chính xác phân loại độc hại.

Fixture `tv4/fixtures/lines_vi.json` có bảy dòng và nhãn khớp từ khóa viết tay; các dòng 0,2,4,6 có hit. `she` khớp `he`; `VIỆT` không khớp `Việt` vì phân biệt hoa thường; `xaaaa` có hai hit `aaa` chồng lấn. Không tuyên bố nhãn độc hại/PII do người thật đánh giá.

## Hồ sơ từ khóa

```powershell
py -B -X utf8 -m tv4.keyword_analysis --keywords PATH_TO_KEYWORDS.txt --text PATH_TO_CORPUS_UTF8.txt --source-status TV5_official --out docs/tv4/reports/official_keywords
```

Bỏ `--text` khi chưa có corpus: cột tần suất để trống, không thay bằng 0. Hash bộ mẫu dùng độ dài big-endian 4 byte rồi nội dung mẫu theo thứ tự, khớp định dạng TV2. Tệp CSV/JSON đi kèm ở `reports/keyword_stub_vi_seed11_k1000/` phân tích bộ stub TV2, **không phải từ khóa chính thức của TV5**. Khi TV5 bàn giao bộ thật phải chạy lại, ghi hash mới và thêm corpus để đo tần suất.

## Kiểm tra phần TV2

TV2 thực tế nằm trên nhánh `tv2-benchmark`. Để không đổi nhánh đang làm, có thể xuất riêng snapshot của nhánh đó rồi truyền đường dẫn chứa `bench.py`, `common.py`, `pilot_standin/`:

```powershell
py -B -X utf8 -m tv4.review_tv2 --tv2-dir PATH_TO_TV2/benchmark_stats --out docs/tv4/reports/tv2_audit_local.json
```

Lệnh chỉ tính lại số và so oracle; không đo hiệu năng lại. `reports/tv2_audit.json` ghi snapshot `5f60d7b`: 1.000 ca oracle/LineCollector trùng; kiểm raw/derived CSV không phát hiện sai công thức đã kiểm trong ngưỡng làm tròn 6 chữ số có nghĩa, nhưng per_cell.csv làm tròn các trường số nguyên. Mỗi dòng vấn đề có ví dụ và giá trị đúng; checksum không đi qua float trong bộ kiểm của TV4. Pilot luôn được gắn nhãn stand-in.

## Đọc bằng chứng và xử lý lỗi

- `reports/seed*/verification.json`: môi trường, seed, hash các file, số ca và trạng thái.
- `error_cases.json`: lỗi đã quan sát, input hex, đáp án/actual và phần thu nhỏ nếu có lỗi tìm kiếm trong fuzzing.
- Các hợp đồng raw được kiểm riêng, ngay cả khi tầng chuẩn bị mẫu đã tránh chúng trong so sánh công bằng.
- Sửa mã phải chạy lại unittest và validator; báo cáo đi kèm là bằng chứng của phiên bản/hash tại thời điểm chạy, không tự xác nhận mã mới.
- Xem `VALIDATION.md` để dùng phần phân tích trong báo cáo nhóm; `TEAM_PROGRESS.md` cho tiến độ theo đúng trách nhiệm người dùng đã xác nhận.

TV4 đã cung cấp công cụ và bằng chứng có thể tái lập. Để nghiệm thu toàn nhóm vẫn cần dữ liệu thật, bộ mẫu chính thức, thống nhất hợp đồng, phần instrumentation và kết quả thực nghiệm từ các chủ RQ.
