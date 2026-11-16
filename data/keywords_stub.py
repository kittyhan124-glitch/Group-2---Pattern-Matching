#!/usr/bin/env python3
"""BỘ TỪ KHÓA TẠM (stub) chỉ để chạy thử RQ3 khi TV5 chưa giao generator thật.
Định dạng giữ nguyên để TV5 ghi đè: data/keywords/kw_<vi|en>_seed<seed>_k<K>.txt, mỗi dòng một mẫu UTF-8
(không chứa LF, đã NFC, đã loại trùng), pid = số dòng (từ 0). Tập lồng nhau: k nhỏ là phần đầu của k lớn.
Mẫu 16 byte cắt từ 1 MiB đầu của corpus tại ranh giới UTF-8 hợp lệ."""
import os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
M = 16

def make(lang, seed, kmax=1000):
    buf = open(os.path.join(HERE, f"{'T1_vi' if lang == 'vi' else 'T2_en'}_1MiB.bin"), "rb").read()
    rng, out, seen = random.Random(seed), [], set()
    while len(out) < kmax:
        i = rng.randrange(0, len(buf) - M)
        if (buf[i] & 0xC0) == 0x80 or (buf[i + M] & 0xC0) == 0x80:
            continue
        p = buf[i:i + M]
        if b"\n" in p or p in seen:
            continue
        seen.add(p); out.append(p)
    return out

if __name__ == "__main__":
    for lang in ("vi", "en"):
        for seed in (11, 29, 47):
            pats = make(lang, seed)
            for k in (1, 10, 100, 1000):
                with open(os.path.join(HERE, "keywords", f"kw_{lang}_seed{seed}_k{k}.txt"), "wb") as f:
                    f.write(b"\n".join(pats[:k]))
    print("đã sinh data/keywords/ (STUB)")
