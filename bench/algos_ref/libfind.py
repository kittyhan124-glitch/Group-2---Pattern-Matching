NAME, VARIANT = "lib-find", ""

def build(patterns):
    return list(patterns)

def scan(t, S, hit):
    find = t.find
    for pid, p in enumerate(S):
        start = 0
        while True:
            pos = find(p, start)
            if pos < 0:
                break
            hit(pos, pid)
            start = pos + 1

def scan_counted(t, S, hit):
    scan(t, S, hit)
    return {"comparisons": None, "failure_steps": None}   # bytes.find chạy trong C, không đếm được ở mức Python

def size(S):
    return None, None
