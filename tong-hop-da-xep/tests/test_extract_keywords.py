"""Test cho data/extract_keywords.py trên corpus nhỏ tự sinh (không cần tải Wikipedia)."""
import importlib.util
import json
import os
import random
import sys
import tempfile
import unicodedata
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "bench"))
import common  # noqa: E402

_spec = importlib.util.spec_from_file_location("extract_keywords", os.path.join(ROOT, "data", "extract_keywords.py"))
ek = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ek)

VI_WORDS = ["Việt Nam", "thành phố", "Hà Nội", "người", "được", "trong", "những", "năm", "huyện", "tỉnh", "sông",
            "dân số", "lịch sử", "văn hóa", "chiến tranh", "đầu tiên", "quốc gia", "khoa học", "nghiên cứu", "đại học"]
EN_WORDS = ["the", "city", "history", "population", "river", "university", "first", "national", "science",
            "research", "war", "culture", "district", "province", "people", "during", "known", "between", "world"]


def make_corpus(words, seed, n_lines=3000, nfd=False):
    rng = random.Random(seed)
    lines = []
    for _ in range(n_lines):
        sent = " ".join(rng.choice(words) for _ in range(rng.randint(4, 14)))
        if rng.random() < 0.3:
            sent += ", " + rng.choice(words) + " 1975."
        lines.append(sent)
    s = "\n".join(lines) + "\n"
    s = unicodedata.normalize("NFD" if nfd else "NFC", s)
    return s


class TestExtractKeywords(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.data = self.tmp.name
        self.kw = os.path.join(self.data, "keywords")
        os.makedirs(self.kw)
        open(os.path.join(self.kw, "STUB_NOTICE.txt"), "w", encoding="utf-8").write("stub")
        for name, words, seed in (("vi.bin", VI_WORDS, 1), ("en.bin", EN_WORDS, 2)):
            text = make_corpus(words, seed)
            open(os.path.join(self.data, name), "wb").write(unicodedata.normalize("NFC", text).encode("utf-8"))
        self.langs = {"vi": "vi.bin", "en": "en.bin"}

    def tearDown(self):
        self.tmp.cleanup()

    def _generate(self, ks=(1, 10, 100)):
        return ek.generate(data_dir=self.data, kw_dir=self.kw, langs=self.langs, seeds=(11, 29), ks=ks)

    def test_files_valid_nested_and_present_in_text(self):
        self._generate()
        for lang, fname in self.langs.items():
            text = open(os.path.join(self.data, fname), "rb").read()
            for seed in (11, 29):
                sets = {}
                for k in (1, 10, 100):
                    path = f"keywords/kw_{lang}_seed{seed}_k{k}.txt"
                    pats = common.make_patterns({"kind": "file", "path": path}, self.data)
                    common.check_patterns(pats)                         # đúng ràng buộc của runner
                    self.assertEqual(len(pats), k)
                    for p in pats:
                        self.assertIn(p, text, f"từ khóa {p!r} không có trong corpus")
                        self.assertGreaterEqual(len(p), ek.MIN_BYTES)
                        self.assertLessEqual(len(p), ek.MAX_BYTES)
                    sets[k] = pats
                self.assertEqual(sets[10][:1], sets[1])
                self.assertEqual(sets[100][:10], sets[10])

    def test_contains_phrases_and_unicode(self):
        self._generate()
        pats = common.make_patterns({"kind": "file", "path": "keywords/kw_vi_seed11_k100.txt"}, self.data)
        self.assertTrue(any(b" " in p for p in pats), "phải có cụm nhiều từ")
        self.assertTrue(any(any(c > 0x7F for c in p) for p in pats), "phải có ký tự tiếng Việt đa byte")
        self.assertFalse(any(p.decode().isdigit() for p in pats))

    def test_deterministic_and_seed_dependent(self):
        self._generate()
        a = open(os.path.join(self.kw, "kw_vi_seed11_k100.txt"), "rb").read()
        b = open(os.path.join(self.kw, "kw_vi_seed29_k100.txt"), "rb").read()
        self._generate()
        self.assertEqual(a, open(os.path.join(self.kw, "kw_vi_seed11_k100.txt"), "rb").read())
        self.assertNotEqual(a, b)

    def test_manifest_and_stub_removed(self):
        self._generate()
        self.assertFalse(os.path.exists(os.path.join(self.kw, "STUB_NOTICE.txt")))
        m = json.load(open(os.path.join(self.kw, "keywords_manifest.json"), encoding="utf-8"))
        self.assertEqual(len(m["files"]), 2 * 2 * 3)
        self.assertTrue(ek.check(self.kw))
        # sửa một tệp -> check phải báo sai
        with open(os.path.join(self.kw, "kw_en_seed11_k10.txt"), "ab") as f:
            f.write(b"\nxyz")
        self.assertFalse(ek.check(self.kw))

    def test_too_few_candidates_raises(self):
        with self.assertRaises(ValueError):
            ek.select_keywords("một hai ba\n", seed=1, kmax=10)

    def test_phrase_across_punctuation_not_selected(self):
        # "alpha, beta" -> n-gram "alpha beta" không có nguyên văn, không được chọn
        text = ("alpha, beta\n" * 50) + ("gamma delta\n" * 50)
        pats = ek.select_keywords(text, seed=3, kmax=4, min_freq=2)
        self.assertNotIn(b"alpha beta", pats)
        self.assertEqual(len(pats), 4)
        for p in pats:
            self.assertIn(p.decode(), text)


if __name__ == "__main__":
    unittest.main()
