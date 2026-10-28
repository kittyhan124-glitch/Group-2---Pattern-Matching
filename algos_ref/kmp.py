NAME, VARIANT = "kmp", ""

def build(patterns):
    if len(patterns) != 1:
        raise ValueError("kmp chỉ nhận một mẫu")
    p = patterns[0]
    pi = [0] * len(p)
    k = 0
    for i in range(1, len(p)):
        while k and p[i] != p[k]:
            k = pi[k - 1]
        if p[i] == p[k]:
            k += 1
        pi[i] = k
    return p, pi

def scan(t, S, hit):
    p, pi = S
    m, j = len(p), 0
    for i, c in enumerate(t):
        while True:
            if p[j] == c:
                j += 1
                break
            if not j:
                break
            j = pi[j - 1]
        if j == m:
            hit(i - m + 1, 0)
            j = pi[j - 1]

def scan_counted(t, S, hit):
    p, pi = S
    m, j = len(p), 0
    cmp_ = fail = 0
    for i, c in enumerate(t):
        while True:
            cmp_ += 1
            if p[j] == c:
                j += 1
                break
            if not j:
                break
            fail += 1
            j = pi[j - 1]
        if j == m:
            hit(i - m + 1, 0)
            j = pi[j - 1]
    return {"comparisons": cmp_, "failure_steps": fail}

def size(S):
    return len(S[0]) + 1, None
