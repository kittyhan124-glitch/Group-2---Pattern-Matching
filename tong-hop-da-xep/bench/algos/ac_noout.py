"""ABLATION RQ3: AC tắt Output Link (duyệt cả chuỗi Failure Link để báo khớp). Mã nằm trong ac_fail.py."""
import ac_fail as _m

NAME, VARIANT, SOURCE = "ac-noout", "fail-no-output", "src/ac_fail.py"


def build(patterns):
    return _m.build(list(patterns))


def scan(text, S, hit):
    S.scan_no_output(text, hit)


def scan_counted(text, S, hit):
    S.scan_no_output(text, hit)
    return {"comparisons": None, "failure_steps": None}


def size(S):
    return S.size()
