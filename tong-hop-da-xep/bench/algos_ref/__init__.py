"""CÀI ĐẶT THAY THẾ (stand-in) chỉ để kiểm thử runner của TV2.
KHÔNG phải mã của TV1/TV3/TV5 và KHÔNG dùng để rút kết luận trong báo cáo.
Khi các thành viên nộp module thật cùng giao diện, chạy runner với --algo-dir trỏ tới thư mục đó.

Giao diện mỗi module (xem benchmark_protocol.md, mục 3):
  NAME                                  : chuỗi 'bf' | 'kmp' | 'kmp-k' | 'ac' | 'lib-find'
  VARIANT                               : 'fail' | 'dfa' | ''
  build(patterns: list[bytes]) -> S
  scan(text: bytes, S, hit) -> None     : gọi hit(pos, pid) cho MỌI khớp (kể cả chồng lấn); KHÔNG đếm gì thêm
  scan_counted(text, S, hit) -> dict    : cùng logic nhưng đếm {'comparisons','failure_steps'} (chỉ chạy ở lượt --count)
  size(S) -> (states, transitions)      : số trạng thái và số cạnh/chuyển (None nếu không áp dụng)
Một "phép so sánh" = một lần thực thi phép đối chiếu byte văn bản với byte mẫu.
"""
