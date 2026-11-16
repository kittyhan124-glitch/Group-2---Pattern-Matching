#!/usr/bin/env python3
"""Bộ trích xuất từ khóa cho RQ3 (đề §7, Cặp 3) — thay cho keywords_stub.py.

Từ khóa là các TỪ và CỤM TỪ (1–3 từ) thật xuất hiện trong ngữ liệu Wikipedia T1 (vi) / T2 (en), không phải
các đoạn byte cắt ngẫu nhiên. Cách chọn:

  1. Đọc corpus nguồn data/T1_vi_4MiB.bin, data/T2_en_4MiB.bin (là TIỀN TỐ của bản 16 MiB vì create_t1_t2.py cắt
     cùng một luồng bài viết -> mọi từ khóa có trong cả corpus 4 MiB lẫn 16 MiB của RQ3), giải mã UTF-8, NFC.
  2. Tách từ bằng regex Unicode \\w+ (giữ nguyên chữ hoa/thường vì thuật toán khớp theo byte, phân biệt hoa thường),
     bỏ token toàn chữ số hoặc có dấu gạch dưới.
  3. Sinh ứng viên n-gram (n = 1, 2, 3) nối bằng 1 dấu cách, chỉ lấy n-gram nằm trọn trong một dòng, độ dài
     MIN_BYTES..MAX_BYTES byte sau UTF-8, xuất hiện ít nhất MIN_FREQ lần.
  4. Chia ứng viên thành 3 dải tần suất (cao / trung bình / thấp theo phân vị log-tần suất) và lấy mẫu xoay vòng
     đều giữa các dải theo seed -> bộ từ khóa có cả từ phổ biến lẫn từ hiếm, giống danh mục lọc thực tế.
  5. Một hoán vị theo seed, k nhỏ là PHẦN ĐẦU của k lớn (tập lồng nhau 1 ⊂ 10 ⊂ 100 ⊂ 1000), nên thay đổi
     giữa các mức k chỉ do số từ khóa.

Ràng buộc đầu ra (khớp bench/common.py::make_patterns và check_patterns):
  - mỗi dòng một từ khóa UTF-8, đã NFC, không rỗng, không chứa LF, không trùng; pid = số dòng (từ 0);
  - tên tệp data/keywords/kw_<vi|en>_seed<seed>_k<K>.txt.

Ghi kèm data/keywords/keywords_manifest.json (tham số, SHA-256 của corpus nguồn, SHA-256 và keyword_hash của
từng tệp) rồi XÓA data/keywords/STUB_NOTICE.txt để runner cho phép chạy RQ3.

Chạy (sau khi đã có T1/T2 từ create_t1_t2.py):
    python data/extract_keywords.py
    python data/extract_keywords.py --check      # chỉ kiểm tra lại các tệp đã sinh với manifest
"""
import argparse
import hashlib
import json
import math
import os
import random
import re
import sys
import unicodedata
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
KW_DIR = os.path.join(HERE, "keywords")
SEEDS = (11, 29, 47)
KS = (1, 10, 100, 1000)
LANGS = {"vi": "T1_vi_4MiB.bin", "en": "T2_en_4MiB.bin"}
MAX_N = 3
MIN_BYTES = 4
MAX_BYTES = 32
MIN_FREQ = 2
N_BANDS = 3

_WORD = re.compile(r"\w+")


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def keyword_hash(patterns):
    """Giống bench/common.py::keyword_hash (danh sách có thứ tự, pid = chỉ số)."""
    h = hashlib.sha256()
    for p in patterns:
        h.update(len(p).to_bytes(4, "big"))
        h.update(p)
    return h.hexdigest()


def _ok_token(t):
    return not t.isdigit() and "_" not in t


def candidate_counts(text, max_n=MAX_N, min_bytes=MIN_BYTES, max_bytes=MAX_BYTES):
    """Đếm n-gram (n=1..max_n) trong từng dòng; chỉ giữ n-gram có độ dài byte trong [min_bytes, max_bytes]."""
    counts = Counter()
    for line in text.split("\n"):
        toks = _WORD.findall(line)
        for i in range(len(toks)):
            for n in range(1, max_n + 1):
                if i + n > len(toks):
                    break
                gram = toks[i:i + n]
                if not all(_ok_token(t) for t in gram):
                    break                      # n-gram dài hơn cũng chứa token này
                phrase = " ".join(gram)
                bl = len(phrase.encode("utf-8"))
                if bl > max_bytes:
                    break                      # n-gram dài hơn chỉ càng dài
                if bl >= min_bytes:
                    counts[phrase] += 1
    return counts


def _phrase_in_text(phrase, text):
    return phrase in text


def select_keywords(text, seed, kmax=max(KS), min_freq=MIN_FREQ, n_bands=N_BANDS, counts=None):
    """Trả danh sách kmax từ khóa (bytes, NFC) theo thứ tự lồng nhau của seed."""
    text = unicodedata.normalize("NFC", text)
    if counts is None:
        counts = candidate_counts(text)
    # Chỉ giữ cụm từ thật sự xuất hiện nguyên văn (n-gram nối bằng 1 dấu cách có thể không có trong văn bản
    # nếu giữa hai từ là dấu câu); kiểm tra lười để không quét toàn bộ từ điển.
    cands = sorted((p for p, c in counts.items() if c >= min_freq), key=lambda p: (-counts[p], p))
    if not cands:
        raise ValueError("không có ứng viên từ khóa nào đạt MIN_FREQ")
    # dải tần suất theo phân vị của log(tần suất)
    logs = sorted(math.log(counts[p]) for p in cands)
    cuts = [logs[min(len(logs) - 1, (len(logs) * i) // n_bands)] for i in range(1, n_bands)]
    bands = [[] for _ in range(n_bands)]
    for p in cands:
        lf = math.log(counts[p])
        b = sum(lf >= c for c in cuts)         # 0 = thấp ... n_bands-1 = cao
        bands[b].append(p)
    rng = random.Random(seed)
    for b in bands:
        b.sort()
        rng.shuffle(b)
    order = list(range(n_bands - 1, -1, -1))   # bắt đầu từ dải cao để k=1 là từ khóa có trúng
    out, seen, idx = [], set(), [0] * n_bands
    while len(out) < kmax:
        progressed = False
        for b in order:
            while idx[b] < len(bands[b]):
                p = bands[b][idx[b]]
                idx[b] += 1
                pb = p.encode("utf-8")
                if pb in seen or b"\n" in pb or not _phrase_in_text(p, text):
                    continue
                seen.add(pb)
                out.append(pb)
                progressed = True
                break
            if len(out) >= kmax:
                break
        if not progressed:
            raise ValueError(f"chỉ chọn được {len(out)} < {kmax} từ khóa; hãy giảm MIN_FREQ hoặc dùng corpus lớn hơn")
    return out


def validate_patterns(pats):
    if not pats:
        raise ValueError("bộ từ khóa rỗng")
    if len(set(pats)) != len(pats):
        raise ValueError("có từ khóa trùng")
    for p in pats:
        if not p or b"\n" in p:
            raise ValueError(f"từ khóa không hợp lệ: {p!r}")
        s = p.decode("utf-8")
        if unicodedata.normalize("NFC", s) != s:
            raise ValueError(f"từ khóa chưa NFC: {p!r}")


def generate(data_dir=HERE, kw_dir=KW_DIR, langs=LANGS, seeds=SEEDS, ks=KS, remove_stub=True):
    os.makedirs(kw_dir, exist_ok=True)
    manifest = {"generator": "data/extract_keywords.py",
                "params": {"max_n": MAX_N, "min_bytes": MIN_BYTES, "max_bytes": MAX_BYTES, "min_freq": MIN_FREQ,
                           "n_bands": N_BANDS, "seeds": list(seeds), "ks": list(ks), "nested": True},
                "sources": {}, "files": {}}
    for lang, fname in langs.items():
        src = os.path.join(data_dir, fname)
        raw = open(src, "rb").read()
        text = unicodedata.normalize("NFC", raw.decode("utf-8"))
        counts = candidate_counts(text)
        manifest["sources"][lang] = {"file": f"data/{fname}", "sha256": sha256_bytes(raw),
                                     "n_candidates": sum(c >= MIN_FREQ for c in counts.values())}
        for seed in seeds:
            pats = select_keywords(text, seed, kmax=max(ks), counts=counts)
            for k in ks:
                sub = pats[:k]
                validate_patterns(sub)
                body = b"\n".join(sub)
                name = f"kw_{lang}_seed{seed}_k{k}.txt"
                with open(os.path.join(kw_dir, name), "wb") as f:
                    f.write(body)
                manifest["files"][name] = {"k": k, "sha256": sha256_bytes(body), "keyword_hash": keyword_hash(sub),
                                           "m_min": min(map(len, sub)), "m_max": max(map(len, sub)),
                                           "L_bytes": sum(map(len, sub))}
            print(f"{lang} seed{seed}: {len(pats)} từ khóa, ví dụ: {[p.decode() for p in pats[:5]]}")
    with open(os.path.join(kw_dir, "keywords_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    stub = os.path.join(kw_dir, "STUB_NOTICE.txt")
    if remove_stub and os.path.exists(stub):
        os.remove(stub)
        print("đã xóa STUB_NOTICE.txt -> runner cho phép chạy RQ3")
    return manifest


def check(kw_dir=KW_DIR):
    mpath = os.path.join(kw_dir, "keywords_manifest.json")
    if not os.path.exists(mpath):
        print("chưa có keywords_manifest.json (bộ từ khóa vẫn là stub)")
        return False
    manifest = json.load(open(mpath, encoding="utf-8"))
    ok = True
    for name, info in manifest["files"].items():
        body = open(os.path.join(kw_dir, name), "rb").read()
        pats = [p for p in body.split(b"\n") if p]
        good = sha256_bytes(body) == info["sha256"] and keyword_hash(pats) == info["keyword_hash"]
        try:
            validate_patterns(pats)
        except ValueError as exc:
            good = False
            print(name, exc)
        ok &= good
        print(("OK   " if good else "SAI  ") + name)
    for lang, s in manifest["sources"].items():
        src = os.path.join(os.path.dirname(kw_dir), os.path.basename(s["file"]))
        if os.path.exists(src):
            same = sha256_bytes(open(src, "rb").read()) == s["sha256"]
            ok &= same
            print(("OK   " if same else "SAI  ") + s["file"])
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="chỉ kiểm tra các tệp đã sinh với manifest")
    ap.add_argument("--keep-stub-notice", action="store_true", help="không xóa STUB_NOTICE.txt")
    a = ap.parse_args()
    if a.check:
        sys.exit(0 if check() else 1)
    missing = [f for f in LANGS.values() if not os.path.exists(os.path.join(HERE, f))]
    if missing:
        sys.exit(f"thiếu corpus {missing}; chạy python data/create_t1_t2.py trước")
    generate(remove_stub=not a.keep_stub_notice)


if __name__ == "__main__":
    main()
