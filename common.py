"""Thành phần dùng chung cho runner (TV2): bộ thu kết quả, oracle tối thiểu, sinh mẫu.

Quy ước (khớp mục 11 của bản phân công):
  - pos là offset BYTE bắt đầu (từ 0) trên văn bản đã NFC->UTF-8; pid từ 0.
  - check = (check + (pos + 1) * 1_000_003 + pid) mod 2**64, khởi tạo 0.
  - dòng = text.split(b"\\n"); lines_total = len(...) (kể cả phần rỗng cuối).
"""
import hashlib, json, os, random, unicodedata
from bisect import bisect_right

MASK = (1 << 64) - 1
MUL = 1_000_003


class Collector:
    """Bộ thu chuẩn cho lượt timing: chỉ count + check (chi phí này nằm trong elapsed_ms)."""
    __slots__ = ("count", "check")

    def __init__(self):
        self.count = 0
        self.check = 0

    def hit(self, pos, pid):
        self.count += 1
        self.check = (self.check + (pos + 1) * MUL + pid) & MASK


class LineCollector(Collector):
    """Dùng ở lượt --count (KHÔNG đo thời gian): thêm ánh xạ hit -> line_id."""
    __slots__ = ("nl", "lines")

    def __init__(self, text):
        super().__init__()
        self.nl = _newlines(text)
        self.lines = set()

    def hit(self, pos, pid):
        Collector.hit(self, pos, pid)
        # line_id = số LF nằm trước pos (hit không chứa LF nên mọi byte của hit cùng một dòng)
        self.lines.add(bisect_right(self.nl, pos - 1))


def _newlines(text):
    out, i = [], text.find(b"\n")
    while i != -1:
        out.append(i)
        i = text.find(b"\n", i + 1)
    return out


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def keyword_hash(patterns):
    """Hash của danh sách mẫu có thứ tự (pid = chỉ số)."""
    h = hashlib.sha256()
    for p in patterns:
        h.update(len(p).to_bytes(4, "big"))
        h.update(p)
    return h.hexdigest()


def check_patterns(patterns):
    if not patterns:
        raise ValueError("bộ mẫu rỗng")
    for p in patterns:
        if len(p) == 0:
            raise ValueError("mẫu rỗng không hợp lệ")
        if b"\n" in p:
            raise ValueError("bộ mẫu chính không được chứa LF")
    if len(set(patterns)) != len(patterns):
        raise ValueError("mẫu trùng: phải loại trùng sau NFC trước khi build")


# ---------- oracle tối thiểu (bytes.find, lần tìm kế tiếp bắt đầu ở pos + 1) ----------
def oracle(text, patterns):
    """Trả (count, check, lines_flagged, lines_total). Thay bằng oracle của TV4 khi có."""
    count = check = 0
    nl = _newlines(text)
    lines = set()
    for pid, p in enumerate(patterns):
        start = 0
        while True:
            pos = text.find(p, start)
            if pos < 0:
                break
            count += 1
            check = (check + (pos + 1) * MUL + pid) & MASK
            lines.add(bisect_right(nl, pos - 1))
            start = pos + 1
    return count, check, len(lines), len(nl) + 1


# ---------- sinh mẫu xác định theo seed ----------
def _boundary_ok(buf, i, utf8):
    return (not utf8) or i >= len(buf) or (buf[i] & 0xC0) != 0x80


def cut_pattern(path, m, seed, utf8=True, region=1 << 20, salt=0):
    """Cắt mẫu m byte từ `region` byte đầu của file, tại ranh giới UTF-8 hợp lệ, không chứa LF."""
    buf = open(path, "rb").read(region)
    rng = random.Random(seed * 1_000_003 + salt)
    for _ in range(100_000):
        i = rng.randrange(0, len(buf) - m)
        if not (_boundary_ok(buf, i, utf8) and _boundary_ok(buf, i + m, utf8)):
            continue
        p = buf[i:i + m]
        if b"\n" in p:
            continue
        return p
    raise RuntimeError(f"không cắt được mẫu {m} byte hợp lệ từ {path}")


def make_patterns(spec, base_dir="."):
    """spec là dict (đọc từ plan.csv):
         {"kind":"cut","from":"data/x.bin","m":16,"seed":11,"utf8":true}
         {"kind":"t4","m":64}                      -> a^(m-1) b
         {"kind":"file","path":"keywords/x.txt"}   -> mỗi dòng một mẫu (UTF-8), pid = số dòng
    """
    kind = spec["kind"]
    if kind == "cut":
        return [cut_pattern(os.path.join(base_dir, spec["from"]), spec["m"], spec["seed"],
                            spec.get("utf8", True))]
    if kind == "t4":
        m = spec["m"]
        return [b"a" * (m - 1) + b"b"]
    if kind == "file":
        raw = open(os.path.join(base_dir, spec["path"]), "rb").read()
        pats = [unicodedata.normalize("NFC", l.decode("utf-8")).encode("utf-8")
                for l in raw.split(b"\n") if l]
        seen, out = set(), []
        for p in pats:               # loại trùng sau NFC, giữ thứ tự đầu tiên
            if p not in seen:
                seen.add(p)
                out.append(p)
        return out
    raise ValueError(kind)


def load_text(path, binary=False):
    """Nạp văn bản; với corpus chữ phải là UTF-8 hợp lệ và đã NFC (kiểm 1 lần, ngoài thời gian đo)."""
    b = open(path, "rb").read()
    if not binary:
        s = b.decode("utf-8")
        if unicodedata.normalize("NFC", s) != s:
            raise ValueError(f"{path} chưa ở dạng NFC")
    return b
