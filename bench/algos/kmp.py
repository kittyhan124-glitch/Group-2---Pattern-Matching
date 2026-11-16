"""Wrapper nối src/kmp.py (TV3) vào giao diện runner; không chứa logic thuật toán."""
import kmp as _m

NAME, VARIANT, SOURCE = "kmp", "", "src/kmp.py"


def build(patterns):
    if len(patterns) != 1:
        raise ValueError("kmp là thuật toán đơn mẫu: cần đúng 1 mẫu")
    return _m.build(patterns[0])


def scan(text, S, hit):
    _m.scan(text, S, hit=hit)


def scan_counted(text, S, hit):
    _, comparisons, failure_steps = _m.scan_stats(text, S, hit=hit)
    return {"comparisons": comparisons, "failure_steps": failure_steps}


def size(S):
    return S["states"], None
