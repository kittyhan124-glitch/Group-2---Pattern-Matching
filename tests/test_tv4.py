"""TV4 contracts: literal expectations independent of implementations."""
import importlib.util
import unittest
import unicodedata


class OracleContract(unittest.TestCase):
    def test_overlap_and_pid_contract(self):
        self.assertIsNotNone(importlib.util.find_spec('oracle'), 'TV4 oracle module is missing')
        from oracle import oracle_find
        self.assertEqual(oracle_find(b'aaaaa', [b'aaa']), [(0,0),(1,0),(2,0)])
        self.assertEqual(oracle_find(b'ushers', [b'he',b'she',b'his',b'hers']), [(1,1),(2,0),(2,3)])

    def test_duplicate_ids_are_not_discarded(self):
        from oracle import oracle_find, checksum
        hits=oracle_find(b'ab', [b'ab',b'ab',b'b'])
        self.assertEqual(hits,[(0,0),(0,1),(1,2)])
        self.assertEqual(checksum(hits),{'count':3,'check':4000015})

    def test_overlap_checksum_and_order_independence(self):
        from oracle import checksum
        self.assertEqual(checksum([(0,0),(1,0),(2,0)]),{'count':3,'check':6000018})
        self.assertEqual(checksum([(2,0),(0,0),(1,0)]),{'count':3,'check':6000018})

    def test_empty_text_binary_and_long_pattern(self):
        from oracle import oracle_find
        self.assertEqual(oracle_find(b'', [b'a']),[])
        self.assertEqual(oracle_find(b'ab', [b'abc']),[])
        self.assertEqual(oracle_find(b'\x00\xff\x00', [b'\x00',b'\xff']),[(0,0),(1,1),(2,0)])

    def test_reject_empty_and_wrong_types(self):
        from oracle import oracle_find
        for pats in ([],[b''],[b'a',b'']):
            with self.assertRaises(ValueError): oracle_find(b'a',pats)
        for pats in (b'a','a',['a']):
            with self.assertRaises(TypeError): oracle_find(b'a',pats)
        with self.assertRaises(TypeError): oracle_find('a',[b'a'])

    def test_line_metrics_and_bounds(self):
        from oracle import summarize_matches
        self.assertEqual(summarize_matches(b'a\n\nb\n',[b'a',b'b'],[(0,0),(3,1)]),
                         {'count':2,'check':5000016,'lines_flagged':2,'lines_total':4})
        self.assertEqual(summarize_matches(b'',[b'a'],[]),
                         {'count':0,'check':0,'lines_flagged':0,'lines_total':1})
        with self.assertRaises(ValueError): summarize_matches(b'a\nb',[b'a\nb'],[])
        with self.assertRaises(ValueError): summarize_matches(b'a',[b'a'],[(4,0)])


class PreprocessingContract(unittest.TestCase):
    def test_nfc_dedup_mapping_and_byte_offsets(self):
        from tv4.preprocessing import prepare_keywords, normalize_text
        from oracle import oracle_find
        prepared=prepare_keywords(['á',unicodedata.normalize('NFD','á'),'a'])
        self.assertEqual(prepared.patterns,('á'.encode(),b'a'))
        self.assertEqual(prepared.source_to_pid,(0,0,1))
        self.assertEqual(prepared.duplicates_removed,1)
        self.assertEqual(oracle_find(normalize_text('áa'),prepared.patterns),[(0,0),(2,1)])

    def test_no_case_folding_or_strip(self):
        from tv4.preprocessing import prepare_keywords
        self.assertEqual(prepare_keywords(['A','a',' a ']).patterns,(b'A',b'a',b' a '))

    def test_keyword_line_contract(self):
        from tv4.preprocessing import prepare_keywords
        for values in ([],[''],['a\nb']):
            with self.assertRaises(ValueError): prepare_keywords(values)
        with self.assertRaises(TypeError): prepare_keywords('a')


if __name__=='__main__':
    unittest.main(verbosity=2)
