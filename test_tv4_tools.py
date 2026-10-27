"""Observable TV4 analysis and diagnostic behavior with hand-checked fixtures."""
import importlib.util
import unittest


class KeywordAnalysis(unittest.TestCase):
    def test_profile_occurrences_prefixes_and_dedup(self):
        self.assertIsNotNone(importlib.util.find_spec('tv4.keyword_analysis'),'keyword analysis is missing')
        from tv4.keyword_analysis import profile_keywords
        from tv4.preprocessing import prepare_keywords
        profile=profile_keywords(prepare_keywords(['a','ab','b','a']),b'ababa')
        self.assertEqual(profile['summary']['k'],3)
        self.assertEqual(profile['summary']['L_bytes'],4)
        self.assertEqual(profile['summary']['trie_states'],4)
        self.assertEqual(profile['summary']['shared_prefix_nodes'],1)
        self.assertEqual(profile['summary']['max_shared_prefix_bytes'],1)
        self.assertEqual(profile['summary']['duplicates_removed'],1)
        self.assertEqual([r['occurrences'] for r in profile['rows']],[3,2,2])

    def test_profile_absent_corpus_is_not_zero_frequency(self):
        from tv4.keyword_analysis import profile_keywords
        from tv4.preprocessing import prepare_keywords
        profile=profile_keywords(prepare_keywords(['aaa','aa','a']))
        self.assertEqual([r['longest_border_bytes'] for r in profile['rows']],[2,1,0])
        self.assertTrue(all(r['occurrences'] is None for r in profile['rows']))
        self.assertEqual(profile['summary']['trie_states'],4)


class ValidatorContract(unittest.TestCase):
    def test_canonical_ushers_all_actual_algorithms(self):
        from tv4.validate import validate_case
        self.assertEqual(validate_case(b'ushers',[b'he',b'she',b'his',b'hers']),[])

    def test_raw_duplicate_issue_is_visible(self):
        from tv4.validate import validate_case
        issues=validate_case(b'ab',[b'ab',b'ab',b'b'])
        self.assertEqual(len(issues),1)
        self.assertEqual(issues[0]['algorithm'],'ac_fail')
        self.assertEqual(issues[0]['kind'],'algorithm_failure')
        self.assertEqual(issues[0]['expected'],[(0,0),(0,1),(1,2)])

    def test_known_contract_issues_do_not_become_clean_pass(self):
        from tv4.validate import diagnose_contracts, validation_status
        issues=diagnose_contracts()
        self.assertTrue(any(i['id']=='BF_EMPTY_COUNT' for i in issues))
        self.assertTrue(any(i['id']=='AC_DUPLICATE_PID' for i in issues))
        self.assertEqual(validation_status([],issues),'canonical_pass_contract_issues_open')
        self.assertEqual(validation_status([{'kind':'algorithm_failure'}],issues),'algorithm_failures')

    def test_repeated_build_and_scan_does_not_retain_state(self):
        from tv4.adapters import scan_algorithm
        for name in ('bf','kmp','kmp_k','ac_fail'):
            self.assertEqual(scan_algorithm(name,b'ababa',[b'aba']),[(0,0),(2,0)])
            self.assertEqual(scan_algorithm(name,b'xx',[b'aba']),[])
            self.assertEqual(scan_algorithm(name,b'ababa',[b'aba']),[(0,0),(2,0)])

    def test_shrinker_keeps_reproducible_failure(self):
        from tv4.validate import minimize_case,validate_case
        text,pats=minimize_case(b'zzabzz',[b'ab',b'ab',b'b'],'ac_fail')
        self.assertLessEqual(len(text),6)
        self.assertTrue(validate_case(text,pats,algorithms=('ac_fail',)))
        self.assertTrue(all(pats))

    def test_line_fixture_has_independent_expected_lines(self):
        from tv4.validate import line_fixture_report
        report=line_fixture_report()
        self.assertEqual(report['expected_flagged_line_ids'],[0,2,4,6])
        for result in report['algorithms'].values():
            self.assertEqual(result['actual_flagged_line_ids'],[0,2,4,6])
            self.assertEqual(result['summary']['count'],5)
            self.assertEqual(result['summary']['lines_total'],7)
            self.assertTrue(result['oracle_ok'])


if __name__=='__main__':
    unittest.main(verbosity=2)
