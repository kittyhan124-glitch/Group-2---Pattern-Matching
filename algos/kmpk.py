"""Wrapper cho runner: nối kmp_k.py (TV3) vào giao diện bench.py. Không chứa logic thuật toán."""
import kmp_k as _m

NAME, VARIANT, SOURCE = "kmp-k", "", "kmp_k.py"


def build(patterns):
    return _m.build(list(patterns))


def scan(text, S, hit):
    _m.scan(text, S, hit=hit)


def scan_counted(text, S, hit):
    _, comparisons, failure_steps = _m.scan_stats(text, S, hit=hit)
    return {"comparisons": comparisons, "failure_steps": failure_steps}


def size(S):
    return S["states"], None
