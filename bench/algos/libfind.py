"""Mốc thư viện lib-find (đề §3): bytes.find viết bằng C. Chỉ dùng làm mốc đối chứng, đúng quy định chung §5."""
NAME, VARIANT, SOURCE = "lib-find", "", None


def build(patterns):
    for p in patterns:
        if len(p) == 0:
            raise ValueError("Pattern không được rỗng")
    return list(patterns)


def scan(text, S, hit):
    find = text.find
    for pid, p in enumerate(S):
        pos = find(p)
        while pos >= 0:
            hit(pos, pid)
            pos = find(p, pos + 1)


def scan_counted(text, S, hit):
    scan(text, S, hit)
    return {"comparisons": None, "failure_steps": None}   # chạy trong C, không đếm được ở mức Python


def size(S):
    return None, None
