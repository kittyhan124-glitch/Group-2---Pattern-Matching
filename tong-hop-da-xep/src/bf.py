"""Module Brute Force (BF) theo hợp đồng kỹ thuật môn CSD203

Quy định:
- Đầu vào: bytes (không dùng chuỗi string thông thường)
- Trả về đủ các vị trí trùng khớp kể cả khi chồng lấn (overlap)
- Dừng so sánh ngay khi gặp byte đầu tiên sai khớp
- Mẫu rỗng phải báo lỗi ValueError
"""


def build(pattern_bytes: bytes):
    """Tiền xử lý mẫu."""
    if not isinstance(pattern_bytes, (bytes, bytearray)):
        raise TypeError("Pattern phải là kiểu bytes hoặc bytearray")
    if len(pattern_bytes) == 0:
        raise ValueError("Pattern không được rỗng")
    return pattern_bytes


def scan(text_bytes: bytes, pattern_bytes: bytes, hit=None):
    """Tìm tất cả các lần xuất hiện của pattern_bytes trong text_bytes.

    hit=None: trả về danh sách các cặp (pos, pid) với pid mặc định là 0.
    hit=hàm : gọi hit(pos, 0) cho mỗi khớp, không lưu danh sách (dùng khi đo thời gian).
    """
    if not isinstance(text_bytes, (bytes, bytearray)):
        raise TypeError("Text phải là kiểu bytes hoặc bytearray")

    n = len(text_bytes)
    m = len(pattern_bytes)

    if m == 0:
        raise ValueError("Pattern không được rỗng")

    results = []
    report = hit if hit is not None else (lambda pos, pid: results.append((pos, pid)))

    for i in range(n - m + 1):
        match = True
        for j in range(m):
            if text_bytes[i + j] != pattern_bytes[j]:
                match = False
                break
        if match:
            report(i, 0)

    return results if hit is None else None


def scan_with_comparisons(text_bytes: bytes, pattern_bytes: bytes, hit=None):
    """Phiên bản phụ dành riêng cho lượt đo --count của RQ1 (đếm số phép so sánh byte)."""
    n = len(text_bytes)
    m = len(pattern_bytes)

    if m == 0:
        raise ValueError("Pattern không được rỗng")

    comparisons = 0
    results = []
    report = hit if hit is not None else (lambda pos, pid: results.append((pos, pid)))

    for i in range(n - m + 1):
        match = True
        for j in range(m):
            comparisons += 1
            if text_bytes[i + j] != pattern_bytes[j]:
                match = False
                break
        if match:
            report(i, 0)

    return results, comparisons
