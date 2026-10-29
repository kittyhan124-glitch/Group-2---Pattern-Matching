"""Wrapper nối src/ac_fail.py (TV5) vào giao diện runner; Failure Link + Output Link."""
import ac_fail as _m

NAME, VARIANT, SOURCE = "ac", "fail", "src/ac_fail.py"


def build(patterns):
    return _m.build(list(patterns))


def scan(text, S, hit):
    S.scan_hits(text, hit)


def scan_counted(text, S, hit):
    r = S.scan_counted(text, hit)
    return {"comparisons": r["comparisons"], "failure_steps": r["failure_steps"]}


def size(S):
    return S.size()
