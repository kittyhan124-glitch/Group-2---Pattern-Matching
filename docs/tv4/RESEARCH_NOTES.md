# Ghi chú nghiên cứu TV4

## Câu hỏi và giả thuyết

RQ2 cần phân biệt ảnh hưởng của bảng chữ cái, độ dài mẫu và cấu trúc tiền tố. Trước khi giải thích chênh lệch tốc độ, TV4 kiểm tra các thuật toán trả cùng đáp án theo cùng quy ước byte/pid/overlap. Giả thuyết làm việc: một phần chênh lệch quan sát được có thể đến từ sai quy ước hoặc mật độ output khác nhau, không chỉ từ cách tìm kiếm.

## Hai nền tảng dùng để thiết kế oracle

1. Tài liệu Python bytes.find mô tả việc trả vị trí xuất hiện đầu tiên trong vùng tìm kiếm hoặc -1 nếu không có. TV4 gọi lại từ pos+1 để liệt kê cả overlap; không nhảy theo độ dài mẫu. bytes.find chấp nhận mẫu rỗng nhưng hợp đồng đề tài yêu cầu báo lỗi, vì vậy oracle kiểm mẫu trước khi gọi thư viện. Nguồn: https://docs.python.org/3/library/stdtypes.html#bytes.find
2. Tài liệu unicodedata.normalize định nghĩa các dạng chuẩn hóa Unicode, gồm NFC. TV4 chuẩn hóa cả văn bản và từ khóa dạng str rồi mã hóa UTF-8. Không dùng chuẩn hóa để thay lowercase, bỏ dấu hoặc giải mã byte tổng hợp. Nguồn: https://docs.python.org/3/library/unicodedata.html#unicodedata.normalize

## Những lựa chọn bảo đảm kiểm chứng độc lập

Oracle không import BF/KMP/AC. Các đáp án cố định của unit test là giá trị viết tay: aaa trong aaaaa ở 0,1,2; ushers có she@1, he@2 và hers@2. Fuzzing so đầy đủ danh sách cặp thay vì chỉ số hit hoặc checksum. Checksum cộng modulo 2^64 có thể va chạm, nên chỉ là chỉ số tóm tắt và đối chiếu quy mô lớn.

Mẫu trùng là vấn đề về định nghĩa tập mẫu: bảo toàn từng pid là đúng với danh sách raw có trùng, còn loại trùng tập trung là hợp đồng khác. Không được để mỗi thuật toán tự chọn hợp đồng riêng rồi so count/check. TV4 ghi cả hai lớp để nhóm không né lỗi bằng cách chỉ chọn đầu vào thuận lợi.

## Các biến cần ghi để giải thích kết quả

| Biến | Vì sao cần ghi |
|---|---|
| N và m theo byte | Tránh lẫn độ dài ký tự với byte tiếng Việt |
| k và L | Hai tập cùng k có thể có tổng độ dài khác nhau |
| Độ dài biên mẫu | Liên quan trạng thái KMP sau sai hoặc sau hit |
| Q và mức chia sẻ tiền tố | Mô tả cấu trúc Trie, không chỉ số lượng từ khóa |
| Tần suất và mật độ output Z | Xuất nhiều kết quả tự nó tốn thời gian |
| Hash dữ liệu và bộ mẫu | Xác nhận các thuật toán thực sự dùng cùng đầu vào |

Hồ sơ stub 1.000 mẫu đi kèm có Q=13.218 và 796 nút tiền tố chung. Đây mới là quan sát cấu trúc, chưa chứng minh giả thuyết tốc độ. Không có corpus thật thì chưa kết luận về tần suất. Khi có kết quả RQ2/RQ3, ghép các biến trên với elapsed_ms và bộ đếm, giữ phần diễn giải trong phạm vi cấu hình đã đo.

## Kết luận hiện có và giới hạn

Trong 30.000 ca độc lập trên mẫu chuẩn, không thấy sai khác đầu ra giữa các lõi thuật toán và oracle. Hai vấn đề raw contract và instrumentation AC còn mở được ghi đúng phạm vi, không gọi thiếu phần việc là sai thuật toán. Fixture dòng chỉ có đáp án có/không khớp từ khóa; không suy precision/recall nhận diện độc hại khi chưa có nhãn độc lập.

Để viết kết luận RQ2 cùng TV3, bước tiếp theo là nhận số liệu thực nghiệm thật, kiểm hash/count/check và phân tích tác động của sigma/m/tiền tố; ghi rõ các ca timeout và không gộp pilot stand-in vào số liệu chính thức.
