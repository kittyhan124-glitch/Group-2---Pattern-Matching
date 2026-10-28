# Nhóm 2 — Pattern Matching (CSD203, AI21B, FA26)

Đề tài 3: Lọc dữ liệu huấn luyện NLP theo danh sách từ khóa — Brute Force, KMP, k-KMP, Aho–Corasick (Failure Link).
Nhóm 5 người: được miễn biến thể DFA 256 cột (đề §7). Phân công xem `PHAN_CONG.md`.

## Môi trường
- CPython **3.11 trở lên** (nhóm thống nhất một bản; ghi vào `machine_log.json` bằng `python3 bench.py machine`). Không dùng PyPy.
- Thuật toán viết bằng Python thuần. `pandas`, `numpy`, `matplotlib` chỉ dùng cho thống kê và vẽ biểu đồ.

```bash
pip install pandas matplotlib pytest
pip install datasets        # chỉ cần khi tự tạo lại T1/T2 từ Hugging Face
```

## Dữ liệu
Repo chỉ kèm `data/T4_worst_4MiB.bin`; các file lớn bị `.gitignore` loại. Tạo lại bằng:

```bash
python3 create_t1_t2.py     # T1 (20231101.vi), T2 (20231101.en) từ wikimedia/wikipedia, NFC → UTF-8
python3 create_t3_t4.py     # T3 σ = 2, 4, 26, 256 và T4 toàn byte 'a'
```
Đối chiếu SHA-256 với `corpus_manifest.json` / `data_hashes.csv` trước khi đo chính thức.

## Chạy kiểm thử
```bash
python3 -m pytest -q test_*.py                 # unit test + ca biên (đề §5)
python3 -m tv4.validate --fuzz-cases 10000     # ca biên cố định + 10.000 ca fuzz đối chiếu bytes.find
```

## Kiểm chứng nhanh một cấu hình (dưới 60 giây)
```bash
python3 bench.py run --rq RQ2B --limit 1 --out check.csv
```
Chạy BF và KMP trên T4 (m = 8) với mã thật trong `algos/`; mỗi dòng của `check.csv` phải có `status=ok` và `oracle_ok=1`.

## Chạy thực nghiệm đầy đủ
```bash
python3 bench.py machine
python3 bench.py plan                           # plan.csv: 306 ô (RQ1 60, RQ2A 24, RQ2B 6, RQ3 144, RQ3ABL 72)
python3 bench.py estimate                       # ước lượng khối lượng trên máy chính thức
python3 bench.py run --out raw_results.csv      # mặc định dùng algos/ (mã thật)
python3 stats.py --raw raw_results.csv --outdir .
python3 plots.py --summary summary.csv --outdir figs
```
Mỗi tiến trình đo bị giới hạn 60 giây; GC giữ bật mặc định; thời gian, đếm phép toán và bộ nhớ là ba lượt tiến trình riêng.
Khi chạy: đóng ứng dụng khác, cắm điện, không chạy hai `bench.py` song song.

## Tệp
| Tệp | Nội dung |
| --- | --- |
| `bf.py` · `kmp.py` · `kmp_k.py` · `ac_fail.py` | Mã thuật toán của các thành viên |
| `algos/` | Wrapper nối mã thật vào giao diện runner (`build/scan/scan_counted/size`), gồm 2 biến thể ablation `ac_noout.py`, `ac_nofail.py` và mốc `libfind.py` |
| `algos_ref/` | Cài đặt thay thế chỉ để thử runner — **không** dùng làm số liệu báo cáo |
| `bench.py` `common.py` `stats.py` `plots.py` | Runner, thành phần dùng chung, thống kê, biểu đồ |
| `tv4/`, `test_*.py`, `oracle.py` | Bộ kiểm thử, oracle, fuzz |
| `benchmark_protocol.md` | Giao thức đo, giao diện module, công thức, schema CSV |
| `decisions.md` · `limitations.md` · `progress.md` · `methods_draft.md` | Nhật ký quyết định, giới hạn, tiến độ, khung Methods |
| `keywords/`, `keywords_stub.py` | Bộ từ khóa RQ3 (hiện là stub, TV5 thay bằng bộ thật) |
| `pilot_standin/` | Kết quả chạy thử trên stand-in, không dùng cho báo cáo |

## Ablation RQ3 (quy định chung §3)
`RQ3ABL` so AC đầy đủ (`ac`) với AC tắt Output Link (`ac-noout`: duyệt cả chuỗi Failure Link để báo khớp) và AC tắt Failure Link
(`ac-nofail`: chỉ dùng Trie, bắt đầu lại từ gốc tại mỗi byte), trên T1/T2 4 MiB, k = 1, 10, 100, 1.000. Speedup trong `speedup.csv`
= t(biến thể tắt) / t(ac) là mức đóng góp của cơ chế bị tắt; biểu đồ `figs/fig_rq3_ablation.png`.
