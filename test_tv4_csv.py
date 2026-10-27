"""CSV checks use exact integer checksums and independently derived numbers."""
import importlib.util
import unittest


def row(algo='bf',elapsed='1000',check='9007199254740993',mode='timing',status='ok'):
    return {'rq':'RQ1','corpus_id':'T','S_MiB':'1','k':'1','m_bytes':'1',
            'algo':algo,'seed':'11','cell_id':'T|'+algo,'mode':mode,'status':status,
            'N_bytes':'1048576','build_ms':'2','elapsed_ms':elapsed,
            'throughput_MiB_s':str(1000/float(elapsed)), 'count':'1','check':check,
            'oracle_ok':'1','corpus_hash':'corpus','keyword_hash':'keywords'}


class CSVVerification(unittest.TestCase):
    def test_wrong_throughput_detected(self):
        self.assertIsNotNone(importlib.util.find_spec('tv4.review_tv2'),'CSV auditor is missing')
        from tv4.review_tv2 import audit_raw_rows
        bad=row();bad['throughput_MiB_s']='99'
        self.assertTrue(any(i['id']=='THROUGHPUT' for i in audit_raw_rows([bad])))

    def test_large_integer_checksum_difference_is_not_rounded_away(self):
        from tv4.review_tv2 import audit_raw_rows
        issues=audit_raw_rows([row(),row('kmp',check='9007199254740992')])
        self.assertTrue(any(i['id']=='RESULT_CONSISTENCY' for i in issues))

    def test_valid_raw_and_timeout_not_converted_to_zero(self):
        from tv4.review_tv2 import audit_raw_rows,recompute_per_cell
        timeout=row('kmp',status='timeout');timeout['elapsed_ms']='';timeout['throughput_MiB_s']=''
        self.assertEqual(audit_raw_rows([row(),timeout]),[])
        self.assertEqual(recompute_per_cell([timeout])['T|kmp']['status'],'timeout')
        self.assertNotIn('elapsed_med',recompute_per_cell([timeout])['T|kmp'])

    def test_warmup_excluded_from_median(self):
        from tv4.review_tv2 import recompute_per_cell
        rows=[row(elapsed='100'),row(elapsed='300'),row(elapsed='200'),row(elapsed='9999',mode='warmup')]
        cell=recompute_per_cell(rows)['T|bf']
        self.assertEqual(cell['elapsed_med'],200)
        self.assertEqual(cell['rep_range_pct'],100)
        self.assertEqual(cell['n_reps'],3)

    def test_export_rounding_of_checksum_is_reported(self):
        from tv4.review_tv2 import audit_derived_rows
        pc={'cell_id':'T|bf','elapsed_med':'1000','check':'9.0072e15'}
        issues=audit_derived_rows([row()],per_cell_rows=[pc])
        self.assertTrue(any(i['id']=='CHECKSUM_PRECISION' for i in issues))

    def test_speedup_and_total_cost_formulas(self):
        from tv4.review_tv2 import audit_derived_rows
        rows=[row(elapsed='1000'),row('kmp',elapsed='500')]
        speed={'rq':'RQ1','corpus_id':'T','S_MiB':'1','k':'1','m_bytes':'1',
               'baseline':'bf','candidate':'kmp','seed':'11','speedup':'3'}
        self.assertTrue(any(i['id']=='SPEEDUP' for i in audit_derived_rows(rows,speedup_rows=[speed])))
        costs={'rq':'RQ1','corpus_id':'T','S_MiB':'1','k':'1','m_bytes':'1',
               'algo':'bf','total_r5_ms':'5002','total_r20_ms':'20002'}
        self.assertEqual(audit_derived_rows(rows,total_rows=[costs]),[])


if __name__=='__main__':unittest.main(verbosity=2)
