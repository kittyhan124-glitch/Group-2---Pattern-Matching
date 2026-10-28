# benchmark_protocol.md — Quy trình đo (TV2)

Đề tài lọc dữ liệu huấn luyện NLP theo danh sách từ khóa · CSD203 · Nhóm 5 người
Phiên bản giao thức: 0.1 (bản của TV2, chờ cả nhóm xác nhận ở buổi họp cuối ngày 2)

> **Quy ước nhãn.** Mục nào là *yêu cầu của đề gốc* thì ghi **[Đề]**; mục nào là *đề xuất vận hành của nhóm* thì ghi **[ĐX]**
> và phải được ghi vào `decisions.md`. Không trình bày [ĐX] thành yêu cầu của giảng viên.

---

## 1. Câu hỏi và ma trận thực nghiệm

| Mã | Thiết kế | Thuật toán | Số ô cấu hình |
| --- | --- | --- | --- |
| RQ1 | T1 (vi) và T3 σ=26; S = 1, 2, 4, 8, 16 MiB; m = 16 byte; seed 11, 29, 47 | bf, kmp | 2 × 2 × 5 × 3 seed = **60** (20/seed) |
| RQ2 A | T3 4 MiB; m = 64 byte; σ = 2, 4, 26, 256; seed 11, 29, 47 | bf, kmp | 2 × 4 × 3 = **24** (8/seed) |
| RQ2 B | T4 4 MiB; mẫu aᵐ⁻¹b; m = 8, 64, 1.024 | bf, kmp | 2 × 3 = **6** (T4 xác định, không có seed) |
| RQ3 | T1 (vi) và T2 (en) [ĐX], 4 và 16 MiB; k = 1, 10, 100, 1.000; mẫu 16 byte [ĐX]; 3 bộ từ khóa theo seed | kmp-k, ac (fail); lib-find làm mốc | 2 × 2 × 4 × 2 thuật toán chính = 32/seed ⇒ **96**; cộng lib-find = **144** |
| DFA | Mở rộng, chỉ khi nhóm cài và đo thật | ac (dfa) | ngoài ma trận bắt buộc |

Tổng: **234 ô** (gồm lib-find), **93 nhóm** (nhóm = các thuật toán dùng *cùng* văn bản và *cùng* bộ mẫu).
Mỗi ô cần 1 lượt warm-up + 3 lượt đo thời gian + 1 lượt đếm + 1 lượt bộ nhớ = 6 tiến trình, mỗi nhóm thêm 1 lượt oracle
⇒ **1.497 tiến trình**. TV2 tính lại số này mỗi khi cấu hình đổi (`python3 bench.py plan`).

## 2. Các bất biến bắt buộc để so sánh công bằng

1. **Một máy, một phiên bản Python** cho mọi số liệu chính thức; ghi vào `machine_log.json` (`python3 bench.py machine`). Nghiêm cấm ghép số đo từ hai máy trong cùng một bảng/biểu đồ.
2. **Cùng văn bản, cùng bộ mẫu, cùng quy tắc đầu ra** cho mọi thuật toán trong một nhóm. Runner so sánh chỉ trong phạm vi một `group_id`.
3. **Không trộn chế độ:** `timing`, `count`, `mem` là ba lượt tách biệt, ba tiến trình riêng. Thời gian chỉ lấy từ lượt `timing`; không bao giờ lấy từ lượt `count` hoặc `mem`.
4. **Ngoài vùng bấm giờ:** tải file, giải mã UTF-8, kiểm NFC, sinh mẫu, tính hash, oracle. **Trong vùng bấm giờ:** `build` và `scan`.
5. **Mọi thuật toán dùng chung một bộ thu kết quả** `Collector.hit(pos, pid)` (chỉ tăng `count` và cập nhật `check`), nên chi phí này nằm trong `elapsed_ms` của *tất cả* thuật toán và được công khai. Không lưu danh sách hit.
6. **Luân phiên thứ tự thuật toán** giữa các lượt đo (rep 1: A,B; rep 2: B,A; …) để triệt tiêu thiên lệch do nhiệt/bộ nhớ đệm.
7. **GC giữ trạng thái mặc định bật** trong mọi lượt; không gọi `gc.disable()` trong vùng đo. `PYTHONHASHSEED=0`.
8. **Seed ghi trước khi chạy** (11, 29, 47), không chọn seed theo kết quả. **[ĐX]**
9. **Đúng trước, nhanh sau [Đề]:** nếu `count/check` lệch oracle, lượt đó mang `status=wrong`, không đưa vào so hiệu năng, và gửi lỗi cho chủ thuật toán theo quy trình ở mục 11 của bản phân công.

## 3. Hợp đồng giao diện cho module thuật toán (TV1, TV3, TV5)

Mỗi thuật toán là **một file .py** trong thư mục `--algo-dir`, tên file theo bảng dưới, với nội dung:

```python
NAME    = "bf"          # 'bf' | 'kmp' | 'kmp-k' | 'ac' | 'lib-find'
VARIANT = ""            # 'fail' | 'dfa' | ''  (ac: 'fail')

def build(patterns: list[bytes]) -> S: ...
def scan(text: bytes, S, hit) -> None:
    """Gọi hit(pos, pid) cho MỌI khớp (kể cả chồng lấn). KHÔNG đếm gì thêm, KHÔNG in, KHÔNG lưu danh sách hit."""
def scan_counted(text: bytes, S, hit) -> dict:
    """Cùng logic với scan nhưng đếm; trả {'comparisons': int|None, 'failure_steps': int|None}. Chỉ chạy ở lượt --count."""
def size(S) -> tuple[int|None, int|None]:   # (states, transitions)
```

| NAME | File | Chủ | `patterns` | Ghi chú |
| --- | --- | --- | --- | --- |
| bf | `bf.py` | TV1 | 1 mẫu | |
| kmp | `kmp.py` | TV3 | 1 mẫu | Prefix Table tính trong `build` |
| kmp-k | `kmpk.py` | TV3 | k mẫu | **Một** vòng quét văn bản; trong mỗi byte cập nhật k trạng thái |
| ac | `ac.py` | TV5 | k mẫu | Failure Link + Output Link, cạnh dict |
| lib-find | `libfind.py` | TV2 | k mẫu | `bytes.find`, lần tìm kế tiếp bắt đầu ở `pos + 1` |

Ràng buộc: mẫu rỗng → `ValueError` (runner cũng kiểm trước khi gọi); `pid` là chỉ số trong `patterns` (từ 0); `pos` là offset byte từ 0.
**Một "phép so sánh"** = một lần *thực thi* phép đối chiếu giữa **một byte của văn bản và một byte của mẫu** (hoặc tra một cạnh trong AC).
Không đếm phép kiểm biên chỉ số hay điều kiện vòng lặp. `failure_steps` = số lần lùi theo Prefix Table/Failure Link.
Thư mục `algos_ref/` chỉ là **cài đặt thay thế để kiểm thử runner**, không phải mã của các thành viên và không được dùng làm kết quả báo cáo.

## 4. Ba lượt đo (mỗi lượt một tiến trình mới)

| Lượt | Lệnh nội bộ | Ghi gì | Không được bật |
| --- | --- | --- | --- |
| `timing` | `worker --lane timing` | `build_ms`, `elapsed_ms` (= scan), `count`, `check` | đếm phép toán, tracemalloc, ánh xạ dòng |
| `count` | `worker --lane count` | `comparisons`, `failure_steps`, `states`, `transitions`, `lines_flagged`, `lines_total`, `count`, `check` | đồng hồ (không dùng làm thời gian) |
| `mem` | `worker --lane mem` | `mem_peak_bytes`, `mem_current_bytes`, `states`, `transitions` | scan |

- Đồng hồ: `time.perf_counter_ns()` [7]; `build_ms` và `elapsed_ms` tính theo mili-giây. GC được giữ bật mặc định nên các lần thu gom tự nhiên (nếu xảy ra) thuộc thời gian đo.
- Bộ nhớ: corpus và mẫu đã nạp trước; `tracemalloc.start()` **ngay trước** `build`; `mem_peak_bytes` là đỉnh của **vùng build** (cấu trúc
  tìm kiếm), `mem_current_bytes` là phần còn giữ lại sau build. `tracemalloc` chỉ theo dõi khối nhớ do Python cấp [8]; **không đồng nhất với RSS** của tiến trình.
  Nếu nhóm đo thêm RSS, ghi thành cột riêng.
- Với `bf` và `lib-find`, cấu trúc gần như không có nên `mem_peak_bytes` ≈ 0 là kết quả đúng, không phải lỗi.
- `lines_flagged` chỉ tính ở lượt `count`: mỗi `line_id` phân biệt chỉ đếm một lần; dòng = `text.split(b"\n")`.

### Quy trình cho mỗi nhóm (`group_id`)

1. Tính SHA-256 của file corpus; sinh mẫu; tính `keyword_hash`.
2. Chạy **oracle** (`bytes.find`) → `count`, `check`, `lines_flagged`; cache trong `oracle_cache.json` theo (corpus_hash, spec mẫu).
3. **Warm-up** mỗi thuật toán (kết quả lưu với `mode=warmup`, loại khỏi thống kê).
4. **3 lượt đo `timing`**, thứ tự thuật toán xoay vòng.
5. 1 lượt `count` và 1 lượt `mem` cho mỗi thuật toán.
6. Mỗi lượt `timing/count` so `count` và `check` với oracle ⇒ `oracle_ok`. Lệch ⇒ `status=wrong`.

## 5. Dữ liệu và mẫu

### 5.1 Ngữ liệu có sẵn (29 file .bin trong `data.zip`)

| Họ | File | Ghi chú đo được |
| --- | --- | --- |
| T1 (vi) | `T1_vi_{1,2,4,8,16}MiB.bin` | UTF-8 hợp lệ, đã NFC; **các file nhỏ là tiền tố của file 16 MiB** |
| T2 (en) | `T2_en_{1,2,4,8,16}MiB.bin` | UTF-8 hợp lệ, đã NFC; tiền tố lồng nhau; byte ≥ 128: 0,30 % (1 MiB) → 0,68 % (16 MiB), **không phải toàn ASCII** |
| T3 σ=26 | `T3_sigma26_{1,2,4,8,16}MiB_seed{11,29,47}.bin` | mỗi (S, seed) là một file **độc lập**, không phải tiền tố của nhau |
| T3 σ=2, 4, 256 | `T3_sigma{2,4,256}_4MiB.bin` | chỉ một file mỗi σ, không mang seed; σ=256 là byte thô, **không hợp lệ UTF-8** (ngoại lệ NFC đã nêu trong bảng làm rõ) |
| T4 | `T4_worst_4MiB.bin` | toàn byte `a`, xác định |

`data_hashes.csv` ghi SHA-256 và kiểm tra UTF-8/NFC của từng file. **Gói zip không kèm `corpus_manifest.json`** — cần TV1 cấp
(id bài, thứ tự chọn, phiên bản nguồn, seed, dấu phân cách) để truy vết nguồn gốc; TV2 chỉ chứng thực được tính toàn vẹn byte.

### 5.2 Ý nghĩa của seed theo từng ngữ liệu

| Ngữ liệu | Seed ảnh hưởng tới | Hệ quả thống kê |
| --- | --- | --- |
| T1, T2 | chỉ vị trí cắt mẫu (hoặc bộ từ khóa) | **ba seed dùng chung một corpus** ⇒ không phải ba mẫu ngữ liệu độc lập |
| T3 σ=26 | file ngữ liệu **và** mẫu | seed thật sự thay đổi dữ liệu |
| T3 σ=2, 4, 256 | chỉ mẫu | như T1 |
| T4 | không | ba lượt đo là ba lần lặp, không có seed |

### 5.3 Quy tắc sinh mẫu đơn (RQ1, RQ2 A) **[ĐX]**

Cắt `m` byte từ **1 MiB đầu** của file cùng họ (RQ1: `T1_vi_1MiB` hoặc `T3_sigma26_1MiB_seed{s}`; RQ2 A: chính file 4 MiB),
vị trí chọn bằng `random.Random(seed)`, đầu và cuối đoạn nằm ở **ranh giới UTF-8 hợp lệ**, không chứa LF. Cùng một mẫu được giữ cho mọi S
trong cùng (họ, seed). Hệ quả cần nhớ khi đọc kết quả: trên T1, mẫu có mặt ở mọi S; trên T3 σ=26 mẫu thường chỉ có mặt ở 1 MiB và vắng mặt ở các
file lớn hơn. Số hit thực tế (`count`) được ghi lại cho từng ô; không so hiệu năng giữa hai chế độ có mật độ hit khác nhau mà không nêu rõ.
Nếu cần chế độ "mẫu vắng mặt được oracle xác nhận" thì thêm vào ma trận như một cấu hình riêng, không trộn trung bình.

### 5.4 Bộ từ khóa RQ3 (TV5 cấp)

Tệp `keywords/kw_<vi|en>_seed<seed>_k<K>.txt`: mỗi dòng một mẫu UTF-8 (đã NFC, đã loại trùng, không chứa LF), `pid` = số dòng từ 0,
tập lồng nhau (k nhỏ là phần đầu của k lớn). `keyword_hash` tính từ **danh sách mẫu byte có thứ tự**, nên đổi thứ tự hoặc nội dung đều đổi hash.
`keywords_stub.py` sinh bộ **tạm** (mẫu 16 byte cắt từ 1 MiB đầu) chỉ để chạy thử; TV5 ghi đè bằng bộ thật cùng định dạng và khi đó phải chạy lại mọi ô RQ3.

## 6. Chỉ số và công thức

| Chỉ số | Công thức | Ghi chú |
| --- | --- | --- |
| Thông lượng | `(N / 2²⁰) / (elapsed_ms / 1000)` MiB/s | N = số byte thực tế của văn bản; dùng median của `elapsed_ms` |
| Speedup | `t_baseline / t_candidate` | cùng cấu hình **và cùng seed**; > 1: candidate nhanh hơn baseline. Cặp: bf→kmp (RQ1–2), kmp-k→ac, lib-find→ac, kmp-k→lib-find (RQ3) |
| Tổng chi phí | `build_ms + r × elapsed_ms` | r = 1, 5, 20 lần quét dùng lại cùng bộ từ khóa |
| Hòa vốn | `r* = (build_c − build_b) / (scan_b − scan_c)` | chỉ tính khi `build_c > build_b` **và** `scan_b > scan_c` và cả hai đủ số seed `ok`; nếu `build_c ≤ build_b` ghi "lợi ngay từ r=1"; nếu `scan_c ≥ scan_b` ghi "không có hòa vốn" |
| Phép so sánh / N | `comparisons / N_bytes` | từ lượt `count`; không so với `failure_steps` như cùng đơn vị |
| Ứng dụng dòng | `lines_flagged / lines_total` | mỗi dòng nhiều hit chỉ đếm một lần; **không phải độ chính xác lọc** |
| `check` | `(check + (pos+1)·1.000.003 + pid) mod 2⁶⁴` | khởi tạo 0; cộng cho từng hit **[Đề]** |

## 7. Thống kê

1. **Mức seed:** với mỗi (ô, seed) lấy **median, min, max của 3 lượt đo** ⇒ `rep_range_pct = (max − min) / median × 100` là *dao động do đo lặp*.
2. **Mức cấu hình:** lấy median của các median theo seed; `between_seed_range_pct = (max − min)/median × 100` giữa các median seed là *dao động giữa seed*.
   Hai đại lượng này được báo **riêng**, không gộp thành một độ lệch chuẩn.
3. **Không coi 9 lượt (3 seed × 3 lần) là 9 mẫu độc lập**, nhất là T1/T2 nơi ba seed chung một corpus (mục 5.2).
4. **Không tính khoảng tin cậy và không dùng kiểm định ý nghĩa** với 3 seed; diễn giải ở mức mô tả (xu hướng, min–max). Nếu nhóm muốn bổ sung thì phải ghi
   đơn vị lấy mẫu và cách tính, và nhận rõ rằng 3 seed chưa đủ để suy độ tin cậy cao.
5. **Ca timeout/lỗi:** giữ `status`, không thay bằng 0, không bỏ khỏi bảng; biểu đồ vẽ dấu **X**; speedup của ô đó để trống.
6. **Không so** các lượt khác chế độ, khác máy, khác tập mẫu hoặc khác mật độ hit mà không nêu rõ điều kiện.
7. Độ phức tạp lý thuyết chỉ mô tả xu hướng tăng trưởng; số đo Python phản ánh cả chi phí cài đặt và bộ thu kết quả. Mọi nhận định "A nhanh hơn B" phải gắn với một cấu hình và một dòng trong `summary.csv`.

## 8. Timeout, lỗi và chạy lại

- Mỗi tiến trình đo (`warmup`, `timing`, `count`, `mem`) có timeout **60 giây**, theo quy định chung; không tăng timeout riêng theo thuật toán hay chế độ. `plan.csv` và `raw_results.csv` ghi `timeout_s=60`.
- Nếu `warm-up` không đạt `status=ok`, thuật toán đó được đánh dấu "dead" trong nhóm: lưu dòng warm-up với trạng thái thực tế, bỏ các lượt `timing` và `count` còn lại (trừ khi `--force-count`); lượt `mem` vẫn chạy riêng.
- `status` ∈ {`ok`, `timeout`, `crash`, `oom`, `wrong`}. `timeout`: vượt 60 giây; `crash`: tiến trình kết thúc bất thường hoặc không trả kết quả; `oom`: hết bộ nhớ; `wrong`: kết quả lệch oracle. Ghi lý do cụ thể trong `note`; các trạng thái khác `ok` không được tính vào thống kê hiệu năng.
- **Resume:** `run_id` xác định duy nhất từng lượt; chạy lại cùng lệnh sẽ bỏ qua lượt đã có. Khi dữ liệu, bộ mẫu hoặc mã thay đổi, **tạo file raw mới** (không nối vào file cũ) và ghi quyết định.
- Không chạy bù hoặc nâng timeout cho ô bị timeout trong ma trận chính thức; giữ lại trạng thái `timeout` để phân tích.

## 9. Schema `raw_results.csv`

Mỗi dòng là một lượt chạy. Ô không áp dụng **để trống**, không ghi 0 giả.

| Nhóm | Cột |
| --- | --- |
| Nhận diện | `run_id, rq, cell_id, corpus_id, corpus_hash, keyword_hash, seed, rep, mode (warmup/timing/count/mem), code_version` |
| Cấu hình | `algo, variant, N_bytes, S_MiB, k, m_bytes, m_min, m_median, m_max, L_bytes, sigma` |
| Hiệu năng | `build_ms, elapsed_ms, throughput_MiB_s, mem_peak_bytes, mem_current_bytes, states, transitions, failure_steps, comparisons` |
| Kết quả | `count, check, lines_total, lines_flagged, oracle_ok` |
| Trạng thái | `status, timeout_s, note` |

`code_version = <sha256[:10] của file thuật toán>+<sha256[:8] của bench.py>`; máy và Python nằm trong `machine_log.json`.
Tệp tóm tắt: `summary.csv`, `speedup.csv`, `total_cost.csv`, `consistency.csv`, `per_cell.csv` (sinh bởi `stats.py`).

## 10. Cách chạy

```bash
python3 bench.py machine                       # nhật ký máy
python3 bench.py plan --timeout-s 60           # plan.csv (234 ô)
python3 bench.py estimate --prefix 65536       # pilot: khối lượng + dự báo timeout trên MÁY CỦA NHÓM
python3 bench.py run --plan plan.csv --algo-dir <thư mục module thật> --out raw_results.csv
python3 stats.py --raw raw_results.csv --outdir .
python3 plots.py --summary summary.csv --outdir figs
```
Tùy chọn: `--rq RQ1 RQ2A` (chạy theo nhóm RQ), `--reps 3`, `--no-count`, `--no-mem`, `--force-count`, `--limit N` (debug).
Khi chạy: đóng ứng dụng khác, cắm điện, tắt chế độ tiết kiệm pin, không chạy hai `bench.py` song song, không dùng máy cho việc khác. GC luôn bật mặc định và mọi tiến trình benchmark bị giới hạn 60 giây.

## 11. Truy vết và tái lập (nghiệm thu TV2)

Từ bất kỳ dòng nào trong `raw_results.csv` truy ra được: `corpus_hash` (SHA-256 file), `keyword_hash`, `seed`, `code_version`, máy/Python (`machine_log.json`),
công thức (mục 6) và dữ liệu thô. `count/check` của mọi thuật toán trong cùng nhóm phải trùng oracle (`consistency.csv`). TV4 tính lại độc lập các công thức
và một phần CSV trước nghiệm thu.

## 12. Tài liệu tham chiếu (số theo bản phân công)

[7] Python Software Foundation, `time.perf_counter` / `perf_counter_ns`. [8] Python Software Foundation, `tracemalloc`.
