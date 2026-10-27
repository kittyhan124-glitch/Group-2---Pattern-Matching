NAME, VARIANT = "bf", ""

def build(patterns):
    if len(patterns) != 1:
        raise ValueError("bf chỉ nhận một mẫu")
    return patterns[0]

def scan(t, p, hit):
    n, m = len(t), len(p)
    for i in range(n - m + 1):
        j = 0
        while j < m and t[i + j] == p[j]:
            j += 1
        if j == m:
            hit(i, 0)

def scan_counted(t, p, hit):
    n, m = len(t), len(p)
    cmp_ = 0
    for i in range(n - m + 1):
        j = 0
        while j < m:
            cmp_ += 1
            if t[i + j] != p[j]:
                break
            j += 1
        if j == m:
            hit(i, 0)
    return {"comparisons": cmp_, "failure_steps": None}

def size(p):
    return None, None
