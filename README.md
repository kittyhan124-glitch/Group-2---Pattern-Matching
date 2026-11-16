# Nhóm 2 — Pattern Matching (CSD203, AI21B, FA26)

Đề tài 3: Lọc dữ liệu huấn luyện NLP theo danh sách từ khóa bằng Brute Force, KMP, k-KMP và Aho–Corasick (Failure Link). Bố cục thư mục tuân theo §8; phân công nhóm ở [PHAN_CONG.md](PHAN_CONG.md).

## Môi trường

- CPython 3.11 trở lên; không dùng PyPy.
- Số liệu trong bài báo (`paper/main.pdf`) được đo bằng **CPython 3.14.8** trên Windows 11 build 26300, Intel Core 7 240H, 32 GiB RAM. Kết quả thô nằm ở `results/`: phiên chính `results/recorded_20261103_234305/` (RQ1, RQ2B, RQ3, ablation) và phiên bổ sung `results/supplement_20261104_025037/` (RQ2A, thí nghiệm phụ về BF).
- `pandas`, `numpy`, `matplotlib` chỉ phục vụ thống kê và biểu đồ.

```powershell
python -m pip install pandas numpy matplotlib pytest
python -m pip install datasets  # chỉ cần khi tạo lại T1/T2 từ Hugging Face
```

## Tạo dữ liệu

Các corpus lớn bị `.gitignore` loại; cần tạo trước khi chạy ma trận. `create_t1_t2.py` tải Wikipedia (`20231101.vi/en`) từ Hugging Face nên cần mạng; T3/T4 sinh offline. Khi bảo vệ, mang sẵn T1/T2 đã sinh trên máy đo chính để không phụ thuộc mạng phòng thi.

```powershell
python data\create_t1_t2.py
python data\create_t3_t4.py
python data\make_profile_manifest.py
python data\extract_keywords.py          # bộ từ khóa thật cho RQ3 (cần T1/T2 4 MiB)
python data\extract_keywords.py --check  # đối chiếu lại với data\keywords\keywords_manifest.json
```

So sánh SHA-256 với `data\corpus_manifest.json` và `data\data_hashes.csv` trước khi đo chính thức.

`data\extract_keywords.py` trích từ và cụm 1–3 từ có thật trong T1/T2 (4–32 byte, xuất hiện ≥ 2 lần), lấy mẫu đều theo 3 dải tần suất, k = 1/10/100/1000 lồng nhau theo seed 11/29/47. Script ghi `keywords_manifest.json` (SHA-256 nguồn, `keyword_hash` từng tệp) và xóa `STUB_NOTICE.txt`. Khi `STUB_NOTICE.txt` còn tồn tại, runner từ chối chạy RQ3 vì `data\keywords\` vẫn là bộ stub của `keywords_stub.py`.

## Kiểm thử

```powershell
python -m pytest -q tests
python -m tests.tv4.validate --fuzz-cases 10000
```

## Chạy runner

`bench\runner.py` và `bench\common.py` là đúng bản đã chạy trong hai phiên đo 03–04/11/2026. So với bản trước đó, bản này có thêm ba điểm:

- khóa cache oracle gắn với hash bộ từ khóa thật, và oracle kiểm cả `keyword_hash` của worker;
- `code_version` ghi thêm hash của `common.py`;
- tùy chọn đọc chứng nhận corpus (xem cuối mục này).

Mỗi dòng CSV ghi `code_version` dạng `<hash thuật toán + bộ nối>+<hash runner.py>+<hash common.py>`. Số liệu đã nộp có đuôi `+7f1d342d+bbdf7f96`; ví dụ KMP là `d344426163+7f1d342d+bbdf7f96`.

```powershell
python bench\runner.py machine
python bench\runner.py plan
python bench\runner.py estimate
python bench\runner.py run
```

Plan mặc định là `bench\plan.csv`; khi chạy mới, kết quả mặc định ghi vào `results\raw\raw_results.csv` (thư mục làm việc, **không** phải số liệu trong bài). Để chạy lại đúng một cấu hình, sao chép chính xác `cell_id` từ CSV:

```powershell
python bench\runner.py run --cell "RQ2B|T4|S4|k1|m8|seed|bf" --reps 1 --out results\raw\single_cell.csv
```

Kiểm tra mọi dòng của cell có `status=ok` và `oracle_ok=1`, rồi so `code_version`, `count`, `check` với dòng cùng `cell_id` trong CSV đã nộp (`results\recorded_20261103_234305\raw_results.csv`, `t4_current.csv` cho RQ2B, hoặc `results\supplement_20261104_025037\raw_results.csv` cho RQ2A); thời gian phải nằm trong 0.5×–2.0× median đã nộp. Runner không nối tiếp vào CSV có header cũ; hãy ghi ra file `--out` mới. Mỗi tiến trình benchmark bị giới hạn 60 giây; GC bật mặc định.

Tùy chọn: đặt biến môi trường `PMATCH_VALIDATED_CORPUS_MANIFEST` trỏ tới chứng nhận corpus (JSON có SHA-256, `utf8_valid`, `nfc_stable` theo đường dẫn tuyệt đối) để worker bỏ qua bước chuẩn hóa NFC lặp lại; mọi kiểm tra vẫn nằm ngoài vùng đo. Không đặt biến này thì worker tự kiểm UTF-8/NFC như bình thường, kết quả `count`/`check` không đổi.

## Thống kê và hình

Tính lại các bảng `analysis\` (số liệu trong bài) từ CSV thô đã nộp:

```powershell
python bench\analyze_results.py results\recorded_20261103_234305 --outdir results\raw\recorded
python bench\analyze_results.py results\supplement_20261104_025037 --outdir results\raw\supplement
```

Kết quả trùng từng ô với `analysis\per_cell_exact.csv`, `summary.csv`, `paired_speedup.csv`, `total_cost.csv` đã nộp. Bỏ `--outdir` thì script ghi đè vào `analysis\` của phiên. Quy ước: lượt `discarded` (nhiễu CPU) bị bỏ; `scan_ms` là median 3 lượt timing; RQ3 lấy `build_ms` từ `build_only.csv` (đo ở 4 MiB, cell 16 MiB dùng lại vì thời gian dựng không phụ thuộc N); `summary.csv` lấy median qua 3 seed; speedup là median tỉ số theo từng seed.

`bench\stats.py` và `bench\plots.py` là công cụ của runner cho kết quả chạy mới trong `results\raw\` (định dạng bảng khác `analysis\`):

```powershell
python bench\stats.py
python bench\plots.py
```

Số liệu chính thức trong bài nằm ở `recorded_20261103_234305\` (RQ1, RQ2B, RQ3, ablation; bảng thống kê trong `analysis\`) và `supplement_20261104_025037\` (RQ2A, thí nghiệm phụ BF). `results\raw\` và `results\figures\` chỉ là thư mục đầu ra khi chạy lại. Kết quả demo và pilot được lưu tách biệt trong `results\demo\` và `results\pilot_standin\`, không dùng làm số liệu chính thức.

## Bố cục chính

| Thư mục | Nội dung |
|---|---|
| `src\` | Mã thuật toán thành viên |
| `tests\` | Test, oracle, `tv4\`, trace demo |
| `bench\` | `runner.py`, module dùng chung, `analyze_results.py` (bảng `analysis\` của bài), thống kê, hình, wrappers và plan |
| `data\` | Generator, manifest, hash, corpus và từ khóa |
| `docs\` | Đề tài, quy định, giao thức, quyết định, giới hạn, tiến độ |
| `paper\` | Báo cáo IEEE |
| `results\recorded_20261103_234305\`, `results\supplement_20261104_025037\` | Số liệu chính thức của bài (CSV thô, `analysis\`) |
| `results\demo\`, `results\pilot_standin\` | Chạy thử đường ống, không phải số liệu chính thức |
| `results\raw\`, `results\figures\` | Đầu ra khi chạy lại runner / thống kê / hình |

RQ3 ablation so sánh AC đầy đủ với biến thể tắt Output Link và tắt Failure Link; lượt count ghi thêm `state_transitions` (số lần chuyển trạng thái khi quét, ≤ 2N) và `output_steps`. Có thể gọi worker bằng cờ `--timing`, `--count`, `--mem` đúng như quy định chung §6. Chi tiết giao thức ở `docs\benchmark_protocol.md`; các giới hạn dữ liệu cần báo cáo ở `docs\limitations.md`.
