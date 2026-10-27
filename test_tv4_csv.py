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

    def test_derived_timeout_cannot_be_fabricated_as_successful_zero(self):
        from tv4.review_tv2 import audit_derived_rows
        raw=row(status='timeout');raw['elapsed_ms']='';raw['throughput_MiB_s']=''
        per_cell={'cell_id':'T|bf','status':'ok','elapsed_med':'0','check':'0'}
        summary={**row(),'status':'ok','elapsed_ms_median':'0'}
        issues=audit_derived_rows([raw],per_cell_rows=[per_cell],summary_rows=[summary])
        self.assertTrue(any(i['id']=='STATUS_MISMATCH' for i in issues))
        self.assertTrue(any(i['id']=='UNMEASURED_VALUE' for i in issues))

    def test_invalid_raw_is_reported_without_crashing_derived_audit(self):
        from tv4.review_tv2 import audit_derived_rows
        bad=row();bad['elapsed_ms']='bad'
        issues=audit_derived_rows([bad],per_cell_rows=[{'cell_id':'T|bf','status':'ok','elapsed_med':'0'}])
        self.assertTrue(any(i['id']=='INVALID_RAW' for i in issues))

    def test_successful_export_cannot_omit_a_present_measurement_column(self):
        from tv4.review_tv2 import audit_derived_rows
        issues=audit_derived_rows([row()],per_cell_rows=[{'cell_id':'T|bf','status':'ok','elapsed_med':''}])
        self.assertTrue(any(i['id']=='MISSING_VALUE' for i in issues))

    def test_empty_t4_seed_matches_tv2_na_label(self):
        from tv4.review_tv2 import audit_derived_rows
        a=row(elapsed='1000');b=row('kmp',elapsed='500')
        a['seed']=b['seed']=''
        speed={**a,'baseline':'bf','candidate':'kmp','seed':'na','speedup':'2'}
        self.assertEqual(audit_derived_rows([a,b],speedup_rows=[speed]),[])

    def test_csv_cli_preserves_report_on_invalid_raw_file(self):
        import csv,json,subprocess,sys,tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);pilot=root/'pilot_standin';pilot.mkdir()
            bad=row();bad['elapsed_ms']='bad'
            with (pilot/'pilot_raw_results.csv').open('w',newline='',encoding='utf-8') as f:
                w=csv.DictWriter(f,fieldnames=list(bad));w.writeheader();w.writerow(bad)
            out=root/'report.json'
            completed=subprocess.run([sys.executable,'-B','-m','tv4.review_tv2','--tv2-dir',str(root),
                                      '--out',str(out)],capture_output=True,text=True,timeout=20)
            self.assertEqual(completed.returncode,1)
            self.assertTrue(out.is_file(),completed.stderr)
            report=json.loads(out.read_text(encoding='utf-8'))
            self.assertTrue(any(i['id']=='INVALID_RAW' for i in report['issues']))


if __name__=='__main__':unittest.main(verbosity=2)
