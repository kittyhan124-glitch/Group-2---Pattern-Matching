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
        import ac_fail
        # Remain valid after the owner resolves the raw-contract disagreement.
        actual=sorted(ac_fail.scan(b'ab',ac_fail.build([b'ab',b'ab',b'b'])))
        issues=validate_case(b'ab',[b'ab',b'ab',b'b'])
        if actual==[(0,0),(0,1),(1,2)]:
            self.assertEqual(issues,[])
            return
        self.assertEqual(len(issues),1)
        self.assertEqual(issues[0]['algorithm'],'ac_fail')
        self.assertEqual(issues[0]['kind'],'algorithm_failure')
        self.assertEqual(issues[0]['expected'],[(0,0),(0,1),(1,2)])

    def test_known_contract_issues_do_not_become_clean_pass(self):
        from tv4.validate import validation_status
        issues=[{'kind':'contract_issue','id':'some_observed_contract_failure'}]
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
        if not validate_case(b'zzabzz',[b'ab',b'ab',b'b'],algorithms=('ac_fail',)):
            self.skipTest('Owner resolved the duplicate-PID issue used by this shrink fixture')
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

    def test_profile_hash_matches_tv2_length_prefixed_format(self):
        import hashlib
        from tv4.keyword_analysis import profile_keywords
        from tv4.preprocessing import prepare_keywords
        # Manual serialization of [a,ab,b], with 4-byte big-endian lengths.
        expected=hashlib.sha256(b'\x00\x00\x00\x01a\x00\x00\x00\x02ab\x00\x00\x00\x01b').hexdigest()
        actual=profile_keywords(prepare_keywords(['a','ab','b']))['summary']['keyword_sha256']
        self.assertEqual(actual,expected)

    def test_validator_cli_still_writes_report_when_ac_module_missing(self):
        import json,shutil,subprocess,sys,tempfile
        from pathlib import Path
        source=Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            shutil.copytree(source/'tv4',root/'tv4',ignore=shutil.ignore_patterns('__pycache__'))
            for name in ('bf.py','kmp.py','kmp_k.py','oracle.py'):
                shutil.copy2(source/name,root/name)
            completed=subprocess.run([sys.executable,'-B','-m','tv4.validate','--fuzz-cases','0','--out','report'],
                                      cwd=root,capture_output=True,text=True,timeout=20)
            self.assertEqual(completed.returncode,1)
            out=root/'report/verification.json'
            self.assertTrue(out.is_file(),completed.stderr)
            report=json.loads(out.read_text(encoding='utf-8'))
            self.assertEqual(report['status'],'pending_dependency')
            self.assertEqual(report['line_fixture']['algorithms']['ac_fail']['status'],'pending_dependency')

    def test_invalid_line_hit_is_reported_as_failure_instead_of_throwing(self):
        from unittest.mock import patch
        import tv4.validate as validator
        real=validator.scan_algorithm
        # Only corrupt the algorithm result at the boundary being validated.
        def invalid(name,text,pats,counted=False):
            return [(999999,0)] if name=='bf' else real(name,text,pats,counted)
        with patch.object(validator,'scan_algorithm',side_effect=invalid):
            report=validator.line_fixture_report()
        self.assertEqual(report['algorithms']['bf']['status'],'algorithm_failure')

    def test_counted_failure_mode_is_preserved_for_replay(self):
        from unittest.mock import patch
        import tv4.validate as validator
        real=validator.scan_algorithm
        def counted_bug(name,text,pats,counted=False):
            return [] if name=='bf' and counted else real(name,text,pats,counted)
        with patch.object(validator,'scan_algorithm',side_effect=counted_bug):
            issues=validator.validate_case(b'a',[b'a'],algorithms=('bf',),counted=True)
            self.assertEqual(issues[0]['mode'],'counted')
            text,pats=validator.minimize_case(b'za',[b'a'],'bf',counted=True)
            self.assertTrue(validator.validate_case(text,pats,algorithms=('bf',),counted=True))
            self.assertEqual(validator.validate_case(text,pats,algorithms=('bf',)),[])


if __name__=='__main__':
    unittest.main(verbosity=2)
