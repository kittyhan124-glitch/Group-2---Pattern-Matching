"""Independent stdlib audit of TV2 oracle and numerical CSV exports.

No timing is rerun here. Pilot/stand-in files remain pilot evidence only.
Integer checksums are never converted through float.
"""
import argparse
from collections import defaultdict
import csv
from decimal import Decimal,InvalidOperation
import importlib.util
import json
import math
from pathlib import Path
import random
import statistics

from oracle import oracle_find,summarize_matches

CFG=('rq','corpus_id','S_MiB','k','m_bytes')
STATUS_PRIORITY=('wrong','oom','crash','timeout')


def _aggregate_status(statuses):
    statuses=set(statuses)
    for status in STATUS_PRIORITY:
        if status in statuses:return status
    return 'ok' if statuses=={'ok'} else 'crash'


def _seed(value):
    return 'na' if value in ('',None) else str(value)


def _integer(value):
    number=Decimal(str(value))
    if not number.is_finite() or number!=number.to_integral_value():raise ValueError('integer required')
    return int(number)


def _number(value):
    result=float(value)
    if not math.isfinite(result):raise ValueError('finite number required')
    return result


def _key(row,extra=()):
    out=[]
    for col in CFG+extra:
        value=str(row.get(col,''))
        if col=='seed':value=_seed(row.get(col))
        if col in ('S_MiB','k','m_bytes') and value:
            try:value=str(Decimal(value).normalize())
            except InvalidOperation:pass
        out.append(value)
    return tuple(out)


def _near(value,expected):
    return math.isclose(_number(value),expected,rel_tol=1e-5,abs_tol=1e-6)


def audit_raw_rows(rows):
    issues=[];groups=defaultdict(list)
    for i,row in enumerate(rows,2):
        if row.get('mode') not in ('timing','count'):continue
        if row.get('status')!='ok':
            if row.get('status')=='timeout' and row.get('elapsed_ms') not in ('',None):
                issues.append({'id':'TIMEOUT_VALUE','row':i,'note':'timeout has a measured scan value'})
            continue
        try:
            count,check,N=(_integer(row[k]) for k in ('count','check','N_bytes'))
            if count<0 or not 0<=check<2**64 or N<0:raise ValueError('out of range')
            if str(row.get('oracle_ok'))!='1':
                issues.append({'id':'ORACLE_FLAG','row':i})
            if row['mode']=='timing':
                elapsed=_number(row['elapsed_ms'])
                if elapsed<=0:raise ValueError('positive scan time required')
                throughput=(N/2**20)/(elapsed/1000)
                if not _near(row['throughput_MiB_s'],throughput):
                    issues.append({'id':'THROUGHPUT','row':i,'expected':throughput,
                                   'actual':row.get('throughput_MiB_s')})
            groups[_key(row,('seed',))].append((row,count,check))
        except (KeyError,ValueError,InvalidOperation,TypeError) as exc:
            issues.append({'id':'INVALID_RAW','row':i,'error':str(exc)})
    for key,values in groups.items():
        if len({(v[1],v[2]) for v in values})>1:
            issues.append({'id':'RESULT_CONSISTENCY','config':key,'note':'count/check differ across algorithms or repeats'})
        identities={(v[0].get('corpus_hash'),v[0].get('keyword_hash')) for v in values}
        if len(identities)>1:
            issues.append({'id':'INPUT_IDENTITY','config':key,'note':'same configuration has different input hashes'})
    return issues


def recompute_per_cell(rows):
    groups=defaultdict(list)
    for row in rows:
        if row.get('mode')=='timing':groups[row['cell_id']].append(row)
    timed_cells=set(groups)
    for row in rows:
        if row.get('mode')=='warmup' and row.get('status')!='ok' and row.get('cell_id') not in timed_cells:
            groups[row['cell_id']].append(row)
    out={}
    for cid,values in groups.items():
        valid=[];invalid=[]
        for r in values:
            if r.get('status')!='ok':continue
            try:
                elapsed,build=_number(r['elapsed_ms']),_number(r['build_ms'])
                N,count,check=(_integer(r[k]) for k in ('N_bytes','count','check'))
                if elapsed<=0 or build<0 or N<0 or count<0 or not 0<=check<2**64:
                    raise ValueError('measurement out of range')
                valid.append((r,elapsed,build,N,count,check))
            except (KeyError,ValueError,InvalidOperation,TypeError) as exc:
                invalid.append(str(exc))
        first=values[0]
        result={k:first.get(k,'') for k in CFG+('algo','seed','cell_id')}
        if invalid:result['invalid_raw']=invalid
        status=_aggregate_status(r.get('status','crash') for r in values)
        if valid and status=='ok':
            times=[v[1] for v in valid]
            builds=[v[2] for v in valid]
            med=statistics.median(times)
            result.update(status='ok',n_reps=len(times),elapsed_med=med,
                          elapsed_min=min(times),elapsed_max=max(times),
                          build_med=statistics.median(builds),
                          rep_range_pct=(max(times)-min(times))/med*100,
                          N_bytes=valid[0][3],count=valid[0][4],check=valid[0][5])
        else:result.update(status='invalid_raw' if invalid else status,n_reps=len(valid))
        out[cid]=result
    return out


def audit_derived_rows(raw,per_cell_rows=(),summary_rows=(),speedup_rows=(),total_rows=()):
    pc=recompute_per_cell(raw);issues=[]
    for cid,cell in pc.items():
        if cell.get('invalid_raw'):issues.append({'id':'INVALID_RAW','cell_id':cid,'errors':cell['invalid_raw']})
    def compare(identifier,row,field,expected):
        if field not in row:return  # Partial tables supported by the Python API.
        if row[field] in ('',None):
            issues.append({'id':'MISSING_VALUE','field':field,'cell_id':row.get('cell_id'),'config':_key(row)})
            return
        try:correct=_near(row[field],expected)
        except (ValueError,TypeError):correct=False
        if not correct:issues.append({'id':identifier,'field':field,'expected':expected,
                                      'actual':row.get(field),'cell_id':row.get('cell_id'),
                                      'config':_key(row)})
    def status_and_evidence(row,status,measured_fields,has_evidence):
        if row.get('status') and row['status']!=status:
            issues.append({'id':'STATUS_MISMATCH','cell_id':row.get('cell_id'),
                           'config':_key(row),'expected':status,'actual':row['status']})
        if not has_evidence:
            for field in measured_fields:
                if row.get(field) not in ('',None):
                    issues.append({'id':'UNMEASURED_VALUE','cell_id':row.get('cell_id'),
                                   'config':_key(row),'field':field,'actual':row[field]})
    for row in per_cell_rows:
        real=pc.get(row.get('cell_id'))
        if real is None:
            issues.append({'id':'UNKNOWN_CELL','cell_id':row.get('cell_id')});continue
        status_and_evidence(row,real['status'],('elapsed_med','elapsed_min','elapsed_max','build_med','check','count'),
                            real['status']=='ok')
        for field in ('elapsed_med','elapsed_min','elapsed_max','build_med','rep_range_pct','n_reps'):
            if field in real:compare('PER_CELL',row,field,real[field])
        for field in ('check','N_bytes','count'):
            if row.get(field) and field in real:
                try:equal=_integer(row[field])==real[field]
                except (ValueError,InvalidOperation):equal=False
                if not equal:issues.append({'id':'CHECKSUM_PRECISION' if field=='check' else 'INTEGER_PRECISION',
                                           'cell_id':row.get('cell_id'),'field':field,
                                           'expected':real[field],'actual':row[field]})
    aggregate=defaultdict(list)
    by_seed={}
    for real in pc.values():
        aggregate[_key(real,('algo',))].append(real)
        by_seed[(_key(real),real['algo'],_seed(real['seed']))]=real
    ag={}
    for key,cells in aggregate.items():
        valid=[c for c in cells if c['status']=='ok']
        if not valid:continue
        values=[c['elapsed_med'] for c in valid]
        median=statistics.median(values)
        ag[key]={'elapsed_ms_median':median,'elapsed_ms_seed_min':min(values),
                 'elapsed_ms_seed_max':max(values),'build_ms_median':statistics.median(c['build_med'] for c in valid),
                 'within_seed_range_pct_median':statistics.median(c['rep_range_pct'] for c in valid),
                 'between_seed_range_pct':(max(values)-min(values))/median*100,
                 'throughput_MiB_s':(valid[0]['N_bytes']/2**20)/(median/1000),
                 'all_seeds_ok':len(valid)==len(cells)}
    for row in summary_rows:
        key=_key(row,('algo',));values=ag.get(key);cells=aggregate.get(key)
        if cells is None:
            issues.append({'id':'UNKNOWN_SUMMARY','config':key});continue
        statuses=[c['status'] for c in cells]
        status=_aggregate_status(statuses)
        status_and_evidence(row,status,('elapsed_ms_median','elapsed_ms_seed_min','elapsed_ms_seed_max',
                                        'build_ms_median','throughput_MiB_s'),values is not None)
        compare('SUMMARY',row,'n_seeds_planned',len(cells))
        compare('SUMMARY',row,'n_seeds_ok',sum(s=='ok' for s in statuses))
        if values is None:continue
        for field,expected in values.items():
            if field!='all_seeds_ok':compare('SUMMARY',row,field,expected)
    for row in speedup_rows:
        key=_key(row);base=row['baseline'];cand=row['candidate'];seed=_seed(row['seed'])
        if seed in ('median','min','max'):
            ratios=[]
            for (cfg,algo,sd),b in by_seed.items():
                c=by_seed.get((cfg,cand,sd))
                if cfg==key and algo==base and c and b['status']==c['status']=='ok':
                    ratios.append(b['elapsed_med']/c['elapsed_med'])
            if ratios:
                fn={'median':statistics.median,'min':min,'max':max}[seed]
                compare('SPEEDUP',row,'speedup',fn(ratios))
        else:
            b=by_seed.get((key,base,seed));c=by_seed.get((key,cand,seed))
            if b and c and b['status']==c['status']=='ok':
                compare('SPEEDUP',row,'speedup',b['elapsed_med']/c['elapsed_med'])
            elif row.get('speedup') not in ('',None):
                issues.append({'id':'UNMEASURED_VALUE','field':'speedup','config':key,'seed':seed})
    for row in total_rows:
        algo=row['algo']
        if algo.startswith('BREAKEVEN '):
            base,cand=algo[len('BREAKEVEN '):].split('->')
            b=ag.get(_key(row)+(base,));c=ag.get(_key(row)+(cand,))
            if b and c and b['all_seeds_ok'] and c['all_seeds_ok']:
                bb,sb=b['build_ms_median'],b['elapsed_ms_median']
                bc,sc=c['build_ms_median'],c['elapsed_ms_median']
                if sc<sb:
                    compare('BREAKEVEN',row,'breakeven_r',0 if bc<=bb else (bc-bb)/(sb-sc))
            continue
        value=ag.get(_key(row,('algo',)))
        if value and value['all_seeds_ok']:
            for r in (1,5,20):
                compare('TOTAL_COST',row,f'total_r{r}_ms',value['build_ms_median']+r*value['elapsed_ms_median'])
        elif any(row.get(f'total_r{r}_ms') not in ('',None) for r in (1,5,20)):
            issues.append({'id':'UNMEASURED_VALUE','field':'total_cost','config':_key(row,('algo',))})
    return issues


def audit_common_oracle(common_path,cases=1000,seed=47):
    spec=importlib.util.spec_from_file_location('tv2_common_audited',common_path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    rng=random.Random(seed);failures=[]
    for index in range(cases):
        text=bytes(rng.choice(b'ab\n\r') for _ in range(rng.randrange(80)))
        pats=list(dict.fromkeys(bytes(rng.choice(b'ab') for _ in range(rng.randint(1,5)))
                               for _ in range(rng.randint(1,6))))
        hits=oracle_find(text,pats);expected=summarize_matches(text,pats,hits)
        wanted=tuple(expected[k] for k in ('count','check','lines_flagged','lines_total'))
        actual=mod.oracle(text,pats)
        collector=mod.LineCollector(text)
        for pos,pid in hits:collector.hit(pos,pid)
        collected=(collector.count,collector.check,len(collector.lines),len(collector.nl)+1)
        if actual!=wanted or collected!=wanted:
            failures.append({'case':index,'expected':wanted,'oracle':actual,'collector':collected})
    return {'cases':cases,'seed':seed,'failures':failures,'status':'passed' if not failures else 'failed'}


def _read(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--tv2-dir',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();report={'source_status':'TV2 pilot stand-in, not official experiment','issues':[]}
    common=a.tv2_dir/'bench'/'common.py';pilot=a.tv2_dir/'results'/'pilot_standin'
    if common.is_file():report['oracle_comparison']=audit_common_oracle(common)
    else:report['issues'].append({'id':'DEPENDENCY_MISSING','path':str(common)})
    raw_path=pilot/'pilot_raw_results.csv'
    if raw_path.is_file():
        raw=_read(raw_path);report['raw_rows']=len(raw)
        report['issues']+=audit_raw_rows(raw)
        names={'per_cell_rows':'per_cell.csv','summary_rows':'summary.csv',
               'speedup_rows':'speedup.csv','total_rows':'total_cost.csv'}
        tables={}
        for key,name in names.items():
            path=pilot/name
            if path.is_file():tables[key]=_read(path)
            else:report['issues'].append({'id':'DEPENDENCY_MISSING','path':str(path)})
        report['issues']+=audit_derived_rows(raw,**tables)
        report['derived_rows_checked']={k:len(v) for k,v in tables.items()}
    else:report['issues'].append({'id':'DEPENDENCY_MISSING','path':str(raw_path)})
    report['status']='passed' if not report['issues'] and report.get('oracle_comparison',{}).get('status')=='passed' else 'issues_open'
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':report['status'],'issues':len(report['issues']),
                      'oracle_comparison':report.get('oracle_comparison',{}).get('status'),'out':str(a.out)}))
    return 0 if report['status']=='passed' else 1


if __name__=='__main__':raise SystemExit(main())
