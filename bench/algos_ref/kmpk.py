NAME, VARIANT = "kmp-k", ""

def _prefix_table(p):
    pi = [0] * len(p)
    k = 0
    for i in range(1, len(p)):
        while k and p[i] != p[k]:
            k = pi[k - 1]
        if p[i] == p[k]:
            k += 1
        pi[i] = k
    return pi

def build(patterns):
    return [(p, _prefix_table(p)) for p in patterns]

def scan(t, S, hit):
    """Một lượt đọc văn bản; mỗi byte cập nhật k máy KMP."""
    P = [s[0] for s in S]; PI = [s[1] for s in S]; M = [len(p) for p in P]
    J = [0] * len(S)
    rng = range(len(S))
    for i, c in enumerate(t):
        for q in rng:
            p = P[q]; j = J[q]
            while True:
                if p[j] == c:
                    j += 1
                    break
                if not j:
                    break
                j = PI[q][j - 1]
            if j == M[q]:
                hit(i - j + 1, q)
                j = PI[q][j - 1]
            J[q] = j

def scan_counted(t, S, hit):
    P = [s[0] for s in S]; PI = [s[1] for s in S]; M = [len(p) for p in P]
    J = [0] * len(S)
    cmp_ = fail = 0
    for i, c in enumerate(t):
        for q in range(len(S)):
            p = P[q]; j = J[q]
            while True:
                cmp_ += 1
                if p[j] == c:
                    j += 1
                    break
                if not j:
                    break
                fail += 1
                j = PI[q][j - 1]
            if j == M[q]:
                hit(i - j + 1, q)
                j = PI[q][j - 1]
            J[q] = j
    return {"comparisons": cmp_, "failure_steps": fail}

def size(S):
    return sum(len(s[0]) + 1 for s in S), None
