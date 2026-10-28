# Bảng theo dõi tiến độ — TV2 (đo lường và thống kê)

Ký hiệu: ✅ xong và đã kiểm thử bằng stand-in · 🟡 chạy được, chờ đầu vào của người khác · ⬜ chưa làm.
Mốc theo mục 12 của bản phân công (14 ngày; họp chốt cuối ngày 2, 5, 9, 12, 14).

## A. Việc của TV2 theo mốc

| Mốc | Việc | Sản phẩm | Trạng thái |
| --- | --- | --- | --- |
| Ngày 1–2 | Lập ma trận RQ1–RQ3, đếm số ô | `plan.csv` (234 ô), `benchmark_protocol.md` §1 | ✅ |
| | Chốt schema CSV và công thức chỉ số | `benchmark_protocol.md` §6, §9 | ✅ |
| | Runner nhỏ: 3 lượt timing/count/mem, timeout, resume | `bench.py` | ✅ |
| | Ghi quyết định còn thiếu | `decisions.md` (D01–D24) | ✅ (nhiều mục CẦN XN) |
| | Hợp đồng giao diện cho TV1/TV3/TV5 | `benchmark_protocol.md` §3 | ✅ — **gửi cho 3 bạn ngay** |
| Ngày 3–5 | Pilot: ước lượng thời gian, dự báo timeout | `workload_estimate.csv` | 🟡 (đã chạy trên stand-in; **chạy lại trên máy chính thức với mã thật**) |
| | Chốt timeout công khai | `decisions.md` D11 | ⬜ chờ nhóm |
| | Nhật ký máy | `machine_log.json` | 🟡 (máy sandbox; chạy lại trên máy chính thức) |
| Ngày 6–9 | Chạy RQ1 → RQ2 → RQ3, tổng hợp | `raw_results.csv`, `summary.csv`, `speedup.csv`, `total_cost.csv` | ⬜ chờ mã thật đã qua test của TV4 |
| | Vẽ biểu đồ | `figs/*.png` (`plots.py`) | 🟡 đã thử trên dữ liệu pilot |
| | Hỗ trợ TV5: biểu đồ + đo bộ nhớ RQ3 | `fig_rq3_*.png` | 🟡 |
| Ngày 10–12 | Viết Methods + thống kê RQ1; bảng chọn thuật toán | `methods_draft.md` (khung) | 🟡 khung xong, số liệu ⬜ |
| | Ghép bản báo cáo IEEE đầu, kiểm nguồn và đơn vị | báo cáo | ⬜ |
| Ngày 13–14 | Kiểm bảng/hình, đóng gói, dẫn nguồn | gói nộp | ⬜ |

## B. Cổng kiểm soát trước khi chạy chính thức (chưa đủ thì **không** chạy ma trận)

- [ ] `bf.py` (TV1), `kmp.py` + `kmpk.py` (TV3), `ac.py` (TV5) theo đúng giao diện §3 và qua ca biên + 10.000 ca của TV4.
- [ ] `keywords/kw_*.txt` thật của TV5 (thay stub); `keyword_hash` đã ghi.
- [ ] `corpus_manifest.json` của TV1 (nguồn gốc dữ liệu); `data_hashes.csv` khớp.
- [ ] Nhóm xác nhận D01 (máy), D07–D09, D11 (timeout), D16–D18.
- [ ] `python3 bench.py estimate` đã chạy trên máy chính thức với mã thật; tổng lượt chạy đã tính lại.

## C. Phụ thuộc vào người khác

| Cần từ | Cái gì | Hạn đề nghị | Dùng để |
| --- | --- | --- | --- |
| TV1 | `bf.py`, manifest, xác nhận seed/tên file T3 σ=2/4/256 và T4, quyết định D07/D08/D13/D14 | cuối ngày 3 | RQ1, mô tả Dataset |
| TV3 | `kmp.py`, `kmpk.py`, định nghĩa "phép so sánh" (D09) | cuối ngày 4 | RQ1, RQ2, RQ3 |
| TV4 | oracle + bộ test; đối chiếu `oracle_min` của runner; kiểm công thức `stats.py` | cuối ngày 5 | nghiệm thu tính đúng |
| TV5 | `ac.py`, `keywords/` thật, xác nhận D16–D18 | cuối ngày 5 | RQ3 |

## D. Việc TV2 giao/nhận cho nhóm

- Gửi: `benchmark_protocol.md` §3 (giao diện) cho TV1/TV3/TV5; `corpus_hash`/`keyword_hash` cần ghi vào bảng kết quả của từng người.
- Nhận: module thuật toán; từng chủ RQ đọc `summary.csv` của mình và viết phần kết luận (TV2 không viết thay).
- TV2 hỗ trợ TV5: biểu đồ và đo bộ nhớ RQ3; TV4 kiểm công thức của TV2 và một mẫu CSV (ghi vào bảng đóng góp).
