"""Test cho src/ac_fail.py: ca biên của đề §5, pid với mẫu trùng, các biến thể ablation và lượt --count."""
import os
import random
import sys
import unicodedata
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
import ac_fail  # noqa: E402


def oracle(text, patterns):
    out = []
    for pid, p in enumerate(patterns):
        pos = text.find(p)
        while pos >= 0:
            out.append((pos, pid))
            pos = text.find(p, pos + 1)
    return sorted(out)


def collect(fn, text, S):
    out = []
    res = fn(text, lambda pos, pid: out.append((pos, pid)))
    return sorted(out), res


class TestEdgeCases(unittest.TestCase):
    def test_empty_pattern_raises(self):
        with self.assertRaises(ValueError):
            ac_fail.build([b""])
        with self.assertRaises(ValueError):
            ac_fail.build([b"a", b""])
        with self.assertRaises(ValueError):
            ac_fail.build([])

    def test_overlap(self):
        self.assertEqual(sorted(ac_fail.scan(b"aaaaa", ac_fail.build([b"aaa"]))), [(0, 0), (1, 0), (2, 0)])
        self.assertEqual(sorted(ac_fail.scan(b"abababab", ac_fail.build([b"abab"]))), [(0, 0), (2, 0), (4, 0)])

    def test_ushers(self):
        pats = [b"he", b"she", b"his", b"hers"]
        self.assertEqual(sorted(ac_fail.scan(b"ushers", ac_fail.build(pats))), [(1, 1), (2, 0), (2, 3)])

    def test_nfd_text_matches_nfc_pattern(self):
        text = unicodedata.normalize("NFC", unicodedata.normalize("NFD", "đầu Việt Việt")).encode("utf-8")
        pat = unicodedata.normalize("NFC", "Việt").encode("utf-8")
        self.assertEqual(ac_fail.scan(text, ac_fail.build([pat])), oracle(text, [pat]))
        self.assertEqual(len(ac_fail.scan(text, ac_fail.build([pat]))), 2)


class TestDuplicatePid(unittest.TestCase):
    """build() không loại trùng: pid phải luôn bằng chỉ số trong danh sách đầu vào (checksum §5)."""

    def test_bytes_duplicates(self):
        self.assertEqual(sorted(ac_fail.scan(b"ab", ac_fail.build([b"a", b"a", b"b"]))), [(0, 0), (0, 1), (1, 2)])

    def test_str_duplicates(self):
        self.assertEqual(sorted(ac_fail.scan(b"ab", ac_fail.build(["a", "a", "b"]))), [(0, 0), (0, 1), (1, 2)])

    def test_str_nfd_and_nfc_are_same_pattern(self):
        nfc, nfd = unicodedata.normalize("NFC", "á"), unicodedata.normalize("NFD", "á")
        res = sorted(ac_fail.scan(nfc.encode("utf-8"), ac_fail.build([nfd, nfc])))
        self.assertEqual(res, [(0, 0), (0, 1)])

    def test_class_default_still_dedupes(self):
        self.assertEqual(len(ac_fail.AhoCorasickFail(["a", "a", "b"]).manifest), 2)


class TestVariantsAndCounters(unittest.TestCase):
    def setUp(self):
        self.rng = random.Random(2026)

    def _case(self):
        rng = self.rng
        text = bytes(rng.choice(b"abc") for _ in range(rng.randint(0, 60)))
        pats = [bytes(rng.choice(b"abc") for _ in range(rng.randint(1, 6))) for _ in range(rng.randint(1, 8))]
        return text, pats

    def test_all_scans_match_oracle(self):
        for _ in range(2000):
            text, pats = self._case()
            S = ac_fail.build(pats)
            want = oracle(text, pats)
            for name in ("scan_hits", "scan_no_output", "scan_no_fail",
                         "scan_counted", "scan_no_output_counted", "scan_no_fail_counted"):
                got, _ = collect(getattr(S, name), text, S)
                self.assertEqual(got, want, f"{name} sai với text={text!r} pats={pats!r}")

    def test_counter_invariants(self):
        for _ in range(2000):
            text, pats = self._case()
            S = ac_fail.build(pats)
            n = len(text)
            _, r = collect(S.scan_counted, text, S)
            self.assertEqual(r["goto_steps"], n)
            self.assertEqual(r["state_transitions"], r["goto_steps"] + r["failure_steps"])
            self.assertLessEqual(r["state_transitions"], 2 * n)          # định lý Aho–Corasick
            self.assertEqual(r["comparisons"], n + r["failure_steps"])
            _, r2 = collect(S.scan_no_output_counted, text, S)
            self.assertEqual(r2["failure_steps"], r["failure_steps"])  # cùng đường quét, chỉ khác bước báo khớp
            self.assertGreaterEqual(r2["output_steps"], r["output_steps"])
            _, r3 = collect(S.scan_no_fail_counted, text, S)
            self.assertEqual(r3["failure_steps"], 0)

    def test_output_steps_counts_first_hop(self):
        # "she": tại byte 'e' trạng thái 'she' là terminal -> output_link tới 'he' (1 bước).
        S = ac_fail.build([b"he", b"she"])
        _, r = collect(S.scan_counted, b"she", S)
        self.assertEqual(r["output_steps"], 1)
        # Nút 'xhe' không kết thúc -> nhảy Output Link tới 'he': bước đầu tiên này cũng phải được đếm.
        S = ac_fail.build([b"he", b"xhey"])
        _, r = collect(S.scan_counted, b"xhe", S)
        self.assertEqual(r["output_steps"], 1)


if __name__ == "__main__":
    unittest.main()
