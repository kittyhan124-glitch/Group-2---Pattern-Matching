# Gói TV2 — Đo lường và thống kê (Pattern Matching, CSD203)

## Đây là gì
Bộ công cụ benchmark + tài liệu giao thức của TV2. **Chưa có kết quả chính thức** (`raw_results.csv`, `summary.csv` thật) vì
các module thuật toán của TV1/TV3/TV5 chưa được nộp. Thư mục `pilot_standin/` là kết quả chạy thử đường ống bằng **cài đặt thay thế
(`algos_ref/`)** — chỉ để kiểm thử runner, **không dùng làm số liệu báo cáo**.

## Cài đặt
Giải nén `data.zip` để có thư mục `data/` ngay cạnh `bench.py` (hoặc `ln -s <đường dẫn>/data data`). Cần Python 3.10+, pandas, matplotlib.

## Chạy
```bash
python3 bench.py machine
python3 bench.py plan --timeout-s 300
python3 bench.py estimate                       # pilot khối lượng trên máy chính thức
python3 bench.py run --algo-dir <thư mục module thật> --out raw_results.csv
python3 stats.py --raw raw_results.csv --outdir .
python3 plots.py --summary summary.csv --outdir figs
```
Khi chạy: không mở ứng dụng khác (runner tự phát hiện nhiễu CPU qua tỉ lệ cpu/wall và đo lại, nhưng đừng dựa vào đó).

## Tệp
| Tệp | Nội dung |
| --- | --- |
| `benchmark_protocol.md` | Giao thức đo, giao diện module, công thức, schema CSV |
| `decisions.md` | Nhật ký quyết định D01–D24 (nhiều mục CẦN XN) |
| `progress.md` | Tiến độ, cổng kiểm soát trước khi chạy chính thức, phụ thuộc |
| `limitations.md` | Danh sách giới hạn nghiên cứu |
| `methods_draft.md` | Khung phần Methods cho báo cáo IEEE |
| `bench.py` `common.py` `stats.py` `plots.py` | Runner, thành phần dùng chung, thống kê, biểu đồ |
| `algos_ref/` | Cài đặt thay thế để thử runner (KHÔNG phải mã của thành viên) |
| `keywords_stub.py`, `keywords/` | Bộ từ khóa TẠM cho RQ3 (TV5 thay bằng bộ thật) |
| `plan.csv` | 234 ô cấu hình · `workload_estimate.csv` pilot khối lượng (máy sandbox) |
| `data_hashes.csv` | SHA-256, UTF-8/NFC của 29 file dữ liệu · `machine_log.json` nhật ký máy sandbox |
| `pilot_standin/` | Dữ liệu và biểu đồ chạy thử trên stand-in |
