"""TV4 verification CLI. Canonical matches and open contracts are reported apart."""
import argparse
from collections import Counter
from datetime import datetime,timezone
import hashlib
import importlib
import json
from pathlib import Path
import platform
import random
import subprocess
import sys
import unicodedata

from oracle import oracle_find,checksum,summarize_matches
from .adapters import ALGORITHMS,scan_algorithm
from .preprocessing import prepare_keywords,normalize_text


def validate_case(text,patterns,algorithms=ALGORITHMS,counted=False):
    expected=oracle_find(text,patterns)
    issues=[]
    for name in algorithms:
        try:
            actual=scan_algorithm(name,text,patterns,counted)
            if actual!=expected:
                issues.append({'kind':'algorithm_failure','algorithm':name,
                               'expected':expected,'actual':actual})
        except (ModuleNotFoundError,NotImplementedError) as exc:
            issues.append({'kind':'pending_dependency','algorithm':name,'error':str(exc)})
        except Exception as exc:
            issues.append({'kind':'algorithm_failure','algorithm':name,
                           'error':type(exc).__name__+': '+str(exc)})
    for issue in issues:issue['mode']='counted' if counted else 'normal'
    return issues


def validation_status(failures,contracts):
    if any(i['kind']=='algorithm_failure' for i in failures):return 'algorithm_failures'
    if any(i['kind']=='pending_dependency' for i in failures):return 'pending_dependency'
    if contracts:return 'canonical_pass_contract_issues_open'
    return 'passed'


def diagnose_contracts():
    issues=[]
    try:
        mod=importlib.import_module('bf')
        try:
            actual=mod.scan_with_comparisons(b'abc',b'')
        except ValueError:
            actual=None
        if actual is not None:
            issues.append({'id':'BF_EMPTY_COUNT','kind':'contract_issue','owner':'TV1',
                           'algorithm':'bf','input':{'text_hex':'616263','patterns_hex':['']},
                           'expected':'ValueError','actual':actual,
                           'note':'build rejects empty; direct public counted entrypoint does not'})
    except ModuleNotFoundError as exc:
        issues.append({'id':'BF_MISSING','kind':'pending_dependency','owner':'TV1','error':str(exc)})
    text,pats=b'ab',[b'ab',b'ab',b'b']
    for issue in validate_case(text,pats,algorithms=('ac_fail',)):
        pending=issue['kind']=='pending_dependency'
        issues.append({**issue,'id':'AC_MISSING' if pending else 'AC_DUPLICATE_PID',
                       'kind':'pending_dependency' if pending else 'contract_issue','owner':'TV5',
                       'input':{'text_hex':text.hex(),'patterns_hex':[p.hex() for p in pats]},
                       'note':'raw contract differs; canonical deduplicated inputs are checked separately'})
    try:
        mod=importlib.import_module('ac_fail')
        if not any(hasattr(mod,n) for n in ('scan_counted','scan_stats')):
            issues.append({'id':'AC_COUNT_PENDING','kind':'pending_dependency','owner':'TV5',
                           'note':'counted scan instrumentation not present; not an observed wrong-search result'})
    except ModuleNotFoundError:
        pass
    return issues


def minimize_case(text,patterns,algorithm,budget=64,counted=False):
    """Bounded deletion shrinker; every returned candidate still reproduces."""
    pats=list(patterns)
    def fails(t,ps):
        return any(i['kind']=='algorithm_failure' for i in validate_case(t,ps,algorithms=(algorithm,),counted=counted))
    if not fails(text,pats):return text,pats
    attempts=0;chunk=max(1,len(text)//2)
    while chunk and attempts<budget:
        changed=False
        for start in range(0,len(text),chunk):
            candidate=text[:start]+text[start+chunk:]
            attempts+=1
            if fails(candidate,pats):
                text=candidate;changed=True;break
            if attempts>=budget:break
        if not changed:chunk//=2
    i=0
    while len(pats)>1 and i<len(pats) and attempts<budget:
        candidate=pats[:i]+pats[i+1:];attempts+=1
        if fails(text,candidate):pats=candidate
        else:i+=1
    return text,pats


def line_fixture_report():
    fixture=json.loads((Path(__file__).parent/'fixtures/lines_vi.json').read_text(encoding='utf-8'))
    text=normalize_text(fixture['text']);pats=prepare_keywords(fixture['keywords']).patterns
    expected=fixture['expected_flagged_line_ids'];results={}
    for name in ALGORITHMS:
        hits=None
        try:
            hits=scan_algorithm(name,text,pats)
            summary=summarize_matches(text,pats,hits)
            actual=sorted({text[:pos].count(b'\n') for pos,_ in hits})
            ok=hits==oracle_find(text,pats) and actual==expected
            results[name]={'actual_flagged_line_ids':actual,'summary':summary,
                           'oracle_ok':ok,'status':'passed' if ok else 'algorithm_failure'}
        except (ModuleNotFoundError,NotImplementedError) as exc:
            results[name]={'status':'pending_dependency','oracle_ok':False,'error':str(exc)}
        except Exception as exc:
            results[name]={'status':'algorithm_failure','oracle_ok':False,
                           'error':type(exc).__name__+': '+str(exc),'actual_hits':hits}
    return {'label_kind':fixture['label_kind'],'expected_flagged_line_ids':expected,'algorithms':results}


def fixed_cases():
    vietnamese=unicodedata.normalize('NFD','đầu Việt Việt')
    return [('overlap_a',b'aaaaa',[b'aaa']),('overlap_ab',b'abababab',[b'abab']),
            ('ushers',b'ushers',[b'he',b'she',b'his',b'hers']),
            ('suffix_chain',b'aaaa',[b'a',b'aa',b'aaa']),
            ('empty_text',b'',[b'a']),('long_pattern',b'ab',[b'abc']),
            ('binary',b'\x00\xff\x00\xff',[b'\x00\xff',b'\xff']),
            ('unicode_nfd',normalize_text(vietnamese),prepare_keywords(['Việt']).patterns),
            ('crlf',b'a\r\nb\r\na',[b'a',b'b']),
            ('T4_m1024',b'a'*2048,[b'a'*1023+b'b'])]


def fuzz_case(rng,index):
    category=index%4
    if category==2:
        alphabet=['a','b',' ','\n','ệ','ấ','đ','Việt','漢','🙂']
        value=''.join(rng.choice(alphabet) for _ in range(rng.randrange(35)))
        value=unicodedata.normalize(rng.choice(('NFC','NFD')),value)
        text=normalize_text(value)
        words=[''.join(rng.choice(alphabet[:-1]) for _ in range(rng.randint(1,4))).replace('\n','x')
               for _ in range(rng.randint(1,5))]
        # Include a guaranteed normalized, non-LF substring on some cases.
        if value and rng.random()<0.7:
            words.append(rng.choice(value).replace('\n','x'))
        pats=list(prepare_keywords(words).patterns)
    elif category==3:
        core=bytes(rng.choice(b'ab') for _ in range(rng.randint(1,5)))
        text=core*rng.randint(0,15)+b'c'+core
        pats=list(dict.fromkeys([core,core[:1],core[-1:],core+core,core+b'c']))
    else:
        sigma=rng.choice((2,4,26)) if category==0 else 256
        text=bytes(rng.randrange(sigma) for _ in range(rng.randrange(90)))
        pats=[]
        for _ in range(rng.randint(1,6)):
            if text and rng.random()<0.65:
                left=rng.randrange(len(text));p=text[left:left+rng.randint(1,12)]
            else:p=bytes(rng.randrange(sigma) for _ in range(rng.randint(1,12)))
            if p not in pats:pats.append(p)
    return ('binary_small','binary_256','unicode_nfc_nfd','prefix_suffix_overlap')[category],text,pats


def source_hashes():
    root=Path(__file__).resolve().parents[1]
    paths=[root/(name+'.py') for name in ALGORITHMS]+[root/'oracle.py']+list((root/'tv4').rglob('*.py'))
    return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()}


def run_validation(seed=11,fuzz_cases=10000):
    failures=[];categories=Counter();comparisons=Counter();recorded=[]
    for label,text,pats in fixed_cases():
        for issue in validate_case(text,pats):
            failures.append({**issue,'case':label})
    rng=random.Random(seed)
    for index in range(fuzz_cases):
        label,text,pats=fuzz_case(rng,index);categories[label]+=1
        checks=validate_case(text,pats)
        for name in ALGORITHMS:comparisons[name]+=1
        if index%10==0:
            checks+=validate_case(text,pats,algorithms=('bf','kmp','kmp_k'),counted=True)
        for issue in checks:
            failures.append({'kind':issue['kind'],'algorithm':issue['algorithm'],'case_index':index,'mode':issue['mode']})
            if len(recorded)<10:
                small_t,small_p=minimize_case(text,pats,issue['algorithm'],counted=issue['mode']=='counted') if issue['kind']=='algorithm_failure' else (text,pats)
                recorded.append({**issue,'case_index':index,'category':label,'seed':seed,
                                 'text_hex':text.hex(),'patterns_hex':[p.hex() for p in pats],
                                 'minimized_text_hex':small_t.hex(),'minimized_patterns_hex':[p.hex() for p in small_p]})
    lines=line_fixture_report()
    for name,result in lines['algorithms'].items():
        if not result['oracle_ok']:failures.append({'kind':result['status'],'algorithm':name,'case':'line_fixture'})
    contracts=diagnose_contracts()
    return {'seed':seed,'fuzz_cases':fuzz_cases,'categories':dict(categories),'comparisons_by_algorithm':dict(comparisons),
            'fixed_cases':len(fixed_cases()),'failures':failures,'recorded_failures':recorded,
            'contract_issues':contracts,'line_fixture':lines,'status':validation_status(failures,contracts),
            'source_sha256':source_hashes(),'python':sys.version,'platform':platform.platform(),
            'timestamp_utc':datetime.now(timezone.utc).isoformat(),
            'scope':'actual member code; canonical nonempty unique bytes; BF/KMP adapted per pattern only for validation'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--seed',type=int,default=11);p.add_argument('--fuzz-cases',type=int,default=10000)
    p.add_argument('--out',type=Path,default=Path('docs/tv4/reports/seed11'))
    a=p.parse_args()
    if a.fuzz_cases<0:p.error('--fuzz-cases must be nonnegative')
    report=run_validation(a.seed,a.fuzz_cases)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    (a.out/'error_cases.json').write_text(json.dumps(report['recorded_failures']+report['contract_issues'],ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':report['status'],'seed':a.seed,'fuzz_cases':a.fuzz_cases,
                      'search_failures':len(report['failures']),'open_contract_or_dependency_issues':len(report['contract_issues']),
                      'report':str(a.out/'verification.json')},ensure_ascii=False))
    return 0 if report['status']=='passed' else 1


if __name__=='__main__':sys.exit(main())
