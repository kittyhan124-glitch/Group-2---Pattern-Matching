# Nhóm 2 — Pattern Matching (CSD203, AI21B, FA26)

Đề tài 3: Lọc dữ liệu huấn luyện NLP theo danh sách từ khóa bằng Brute Force, KMP, k-KMP và Aho–Corasick (Failure Link). Bố cục thư mục tuân theo §8; phân công nhóm ở [PHAN_CONG.md](PHAN_CONG.md).

## Môi trường

- CPython 3.11 trở lên; không dùng PyPy.
- `pandas`, `numpy`, `matplotlib` chỉ phục vụ thống kê và biểu đồ.

```powershell
python -m pip install pandas numpy matplotlib pytest
python -m pip install datasets  # chỉ cần khi tạo lại T1/T2 từ Hugging Face
```

## Tạo dữ liệu

Các corpus lớn bị `.gitignore` loại; cần tạo trước khi chạy ma trận:

```powershell
python data\create_t1_t2.py
python data\create_t3_t4.py
python data\make_profile_manifest.py
```

So sánh SHA-256 với `data\corpus_manifest.json` và `data\data_hashes.csv` trước khi đo chính thức. `data\keywords\` hiện chứa bộ từ khóa stub; không chạy/đưa RQ3 vào báo cáo cho tới khi TV5 thay bằng bộ thật và xác nhận nguồn.

## Kiểm thử

```powershell
python -m pytest -q tests
python -m tests.tv4.validate --fuzz-cases 10000
```

## Chạy runner

```powershell
python bench\runner.py machine
python bench\runner.py plan
python bench\runner.py estimate
python bench\runner.py run
```

Plan mặc định là `bench\plan.csv`; kết quả mặc định là `results\raw\raw_results.csv`. Để chạy lại đúng một cấu hình, sao chép chính xác `cell_id` từ CSV:

```powershell
python bench\runner.py run --cell "RQ2B|T4|S4|k1|m8|seed|bf" --reps 1 --out results\raw\single_cell.csv
```

Kiểm tra mọi dòng của cell có `status=ok` và `oracle_ok=1`. Không dùng cell RQ3 trước khi có từ khóa thật. Mỗi tiến trình benchmark bị giới hạn 60 giây; GC bật mặc định.

## Thống kê và hình

```powershell
python bench\stats.py
python bench\plots.py
```

CSV thô và bảng thống kê ở `results\raw\`; biểu đồ ở `results\figures\`. Kết quả demo và pilot được lưu tách biệt trong `results\demo\` và `results\pilot_standin\`, không dùng làm số liệu chính thức.

## Bố cục chính

| Thư mục | Nội dung |
|---|---|
| `src\` | Mã thuật toán thành viên |
| `tests\` | Test, oracle, `tv4\`, trace demo |
| `bench\` | `runner.py`, module dùng chung, thống kê, hình, wrappers và plan |
| `data\` | Generator, manifest, hash, corpus và từ khóa |
| `docs\` | Đề tài, quy định, giao thức, quyết định, giới hạn, tiến độ |
| `paper\` | Báo cáo IEEE |
| `results\raw\`, `results\figures\` | Kết quả và biểu đồ chính thức |

RQ3 ablation so sánh AC đầy đủ với biến thể tắt Output Link và tắt Failure Link. Chi tiết giao thức ở `docs\benchmark_protocol.md`; các giới hạn dữ liệu cần báo cáo ở `docs\limitations.md`.
