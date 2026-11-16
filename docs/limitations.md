# Danh sách giới hạn nghiên cứu (TV2 tổng hợp; cả nhóm bổ sung và duyệt)

Mỗi giới hạn ghi: *điều gì*, *vì sao*, *ảnh hưởng đến kết luận nào*. Những mục đánh dấu ★ đã xác nhận từ dữ liệu trong `data.zip`;
các mục còn lại là giới hạn theo thiết kế, cần cập nhật khi có kết quả chính thức.

## Về dữ liệu
1. ★ **Ba seed không phải ba corpus độc lập trên T1/T2** — chỉ có một file mỗi kích thước; seed đổi vị trí mẫu/bộ từ khóa. Dao động giữa seed phản ánh khác biệt mẫu, không phải khác biệt ngữ liệu. *Ảnh hưởng:* RQ1, RQ3.
2. ★ **T1/T2 là các tiền tố lồng nhau.** Tăng S đồng thời thêm nội dung mới; khó tách tác động "kích thước" khỏi "nội dung". *Ảnh hưởng:* RQ1.
3. ★ **T2 không toàn ASCII**: 0,304 % → 0,678 % byte ≥ 128 từ 1 MiB đến 16 MiB; tỷ lệ không đồng nhất giữa các kích thước. *Ảnh hưởng:* RQ3 trên T2.
4. ★ **T3 σ=2, 4, 256 và T4 chỉ có một file**; σ=256 không hợp lệ UTF-8 (byte thô, ngoại lệ NFC). *Ảnh hưởng:* RQ2 A.
5. **T4 và T3 là ngữ liệu tổng hợp**; một kết quả trên T4 (trường hợp bất lợi) không đại diện cho văn bản tự nhiên và không đủ để nêu thuật toán tốt nhất cho mọi đầu vào. *Ảnh hưởng:* RQ2 B.
6. **Một nguồn miền (Wikipedia)**; chưa kiểm tra tin tức hoặc văn bản học thuật. *Ảnh hưởng:* mọi RQ trên T1/T2.
7. `data/corpus_manifest.json` ghi kích thước và SHA-256, nhưng chưa đủ metadata để chứng thực nguồn gốc từng bài viết; cần TV1 bổ sung nguồn và quy trình tạo corpus.

## Về mẫu và từ khóa
8. **Mẫu RQ1/RQ2 cắt từ 1 MiB đầu** của file; trên T3 σ=26 mẫu thường chỉ có mặt ở 1 MiB, nên mật độ hit khác nhau theo S. *Ảnh hưởng:* RQ1.
9. **Mẫu RQ3 dài 16 byte cố định** (ĐX); m ổn định giúp tách tác động của k, nhưng không bao quát độ dài biến thiên, chia sẻ tiền tố hay mật độ output (thuộc phần mở rộng).
10. **Bộ từ khóa là từ khóa trung tính để đo hiệu năng**, không phải danh sách từ cấm đã được xác thực. *Ảnh hưởng:* mọi nhận định về "lọc nội dung".
11. **`lines_flagged / lines_total` không phải độ chính xác lọc**: khớp byte chính xác không phân biệt ngữ cảnh, ranh giới từ. Precision/recall chỉ báo khi có nhãn độc lập.

## Về phép đo
12. **Một máy, một phiên bản Python thuần**; không suy sang ngôn ngữ, phần cứng hay hệ thống huấn luyện LLM khác.
13. **Chỉ 1 lượt warm-up và 3 lượt đo/seed, 3 seed**: đủ để mô tả xu hướng và min–max, không đủ để suy độ tin cậy thống kê cao; không dùng kiểm định ý nghĩa.
14. **`tracemalloc` chỉ theo dõi khối nhớ Python ở vùng build**, không phải RSS của tiến trình và không gồm bộ nhớ lúc scan. *Ảnh hưởng:* RQ3 (bộ nhớ theo Q).
15. **Bộ thu kết quả dùng chung (count + check) nằm trong thời gian scan** của mọi thuật toán. Chi phí này là như nhau về cấu trúc nhưng làm giảm chênh lệch tương đối khi nhiều hit.
16. **`lib-find` (`bytes.find`) chạy trong C**, nên chỉ là mốc tham chiếu; không so công bằng với cài đặt Python thuần.
17. **Ca timeout/lỗi** làm thiếu điểm dữ liệu (dự kiến kmp-k ở k lớn); các ca đó nằm trong bảng, không bị bỏ.
18. **`comparisons` là số phép so sánh ở mức Python** theo định nghĩa D09; không tương đương số chu kỳ CPU hoặc số phép so sánh của `bytes.find`.
19. **DFA 256 cột:** nếu nhóm không cài và đo, phần Discussion về DFA chỉ dựa trên mô hình/tài liệu, không có benchmark của nhóm.
20. **T3 σ = 2, 4, 256 dùng chung seed 42.** Các corpus ở ba alphabet này không phải các lần sinh độc lập; không diễn giải khác biệt của chúng như biến thiên giữa seed.
21. **Mẫu T3 σ = 26 được cắt từ file 1 MiB.** Do các corpus theo kích thước được sinh độc lập, mẫu có thể rất hiếm hoặc không xuất hiện trong file lớn hơn; phải xác nhận số occurrence bằng manifest/profiling trước khi kết luận về hiệu năng có hit.
