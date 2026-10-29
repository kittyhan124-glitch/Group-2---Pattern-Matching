"""Wrapper nối src/bf.py (TV1) vào giao diện runner; không chứa logic thuật toán."""
import bf as _m

NAME, VARIANT, SOURCE = "bf", "", "src/bf.py"


def build(patterns):
    if len(patterns) != 1:
        raise ValueError("bf là thuật toán đơn mẫu: cần đúng 1 mẫu")
    return _m.build(patterns[0])


def scan(text, S, hit):
    _m.scan(text, S, hit=hit)


def scan_counted(text, S, hit):
    _, comparisons = _m.scan_with_comparisons(text, S, hit=hit)
    return {"comparisons": comparisons, "failure_steps": None}


def size(S):
    return None, None
