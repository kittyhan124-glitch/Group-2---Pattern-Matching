"""ABLATION RQ3: AC tắt Failure Link (chỉ dùng Trie, bắt đầu lại từ gốc ở mỗi vị trí). Mã nằm trong ac_fail.py."""
import ac_fail as _m

NAME, VARIANT, SOURCE = "ac-nofail", "trie-only", "src/ac_fail.py"


def build(patterns):
    return _m.build(list(patterns))


def scan(text, S, hit):
    S.scan_no_fail(text, hit)


def scan_counted(text, S, hit):
    S.scan_no_fail(text, hit)
    return {"comparisons": None, "failure_steps": None}


def size(S):
    return S.size()
