NAME, VARIANT = "ac", "fail"
from collections import deque

def build(patterns):
    goto, term, plen = [{}], [-1], [0]
    for pid, p in enumerate(patterns):
        s = 0
        for c in p:
            nxt = goto[s].get(c)
            if nxt is None:
                goto.append({}); term.append(-1); plen.append(0)
                nxt = len(goto) - 1
                goto[s][c] = nxt
            s = nxt
        term[s] = pid
        plen[s] = len(p)
    fail = [0] * len(goto)
    outl = [0] * len(goto)           # Output Link: trạng thái terminal gần nhất theo chuỗi failure (0 = không có)
    dq = deque(goto[0].values())
    while dq:
        u = dq.popleft()
        for c, v in goto[u].items():
            f = fail[u]
            while f and c not in goto[f]:
                f = fail[f]
            w = goto[f].get(c, 0)
            fail[v] = w if w != v else 0
            outl[v] = fail[v] if term[fail[v]] >= 0 else outl[fail[v]]
            dq.append(v)
    return goto, fail, term, outl, plen

def scan(t, S, hit):
    goto, fail, term, outl, plen = S
    s = 0
    for i, c in enumerate(t):
        while s and c not in goto[s]:
            s = fail[s]
        s = goto[s].get(c, 0)
        if term[s] >= 0:
            hit(i - plen[s] + 1, term[s])
        o = outl[s]
        while o:
            hit(i - plen[o] + 1, term[o])
            o = outl[o]

def scan_counted(t, S, hit):
    """comparisons = số lần tra cạnh (c in goto[s]) ; failure_steps = số lần lùi theo Failure Link."""
    goto, fail, term, outl, plen = S
    s = 0
    cmp_ = fs = 0
    for i, c in enumerate(t):
        while s:
            cmp_ += 1
            if c in goto[s]:
                break
            s = fail[s]; fs += 1
        cmp_ += 1 if not s else 0
        s = goto[s].get(c, 0)
        if term[s] >= 0:
            hit(i - plen[s] + 1, term[s])
        o = outl[s]
        while o:
            hit(i - plen[o] + 1, term[o])
            o = outl[o]
    return {"comparisons": cmp_, "failure_steps": fs}

def size(S):
    goto = S[0]
    return len(goto), sum(len(d) for d in goto)
