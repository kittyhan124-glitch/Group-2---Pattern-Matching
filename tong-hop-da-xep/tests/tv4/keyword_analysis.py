"""Reproducible keyword profiles; no corpus means unknown frequency, not zero."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import statistics

from oracle import iter_matches
from .preprocessing import prepare_keywords,normalize_text


def _longest_border(p):
    # Direct definition, intentionally independent of the student's prefix code.
    return next((n for n in range(len(p)-1,0,-1) if p[:n]==p[-n:]),0)


def profile_keywords(prepared,text=None):
    pats=prepared.patterns
    children=[{}]
    visits=[0]
    depths=[0]
    for p in pats:
        node=0
        for byte in p:
            if byte not in children[node]:
                children[node][byte]=len(children)
                children.append({});visits.append(0);depths.append(depths[node]+1)
            node=children[node][byte]
            visits[node]+=1
    counts=None
    if text is not None:
        counts=[0]*len(pats)
        for _,pid in iter_matches(text,pats): counts[pid]+=1
    rows=[]
    for pid,p in enumerate(pats):
        rows.append({'pid':pid,'keyword_nfc':prepared.normalized_keywords[pid],
                     'pattern_hex':p.hex(),'m_bytes':len(p),
                     'characters':len(prepared.normalized_keywords[pid]),
                     'longest_border_bytes':_longest_border(p),
                     'occurrences':None if counts is None else counts[pid],
                     'hits_per_MiB':None if text is None or not len(text) else counts[pid]/(len(text)/2**20)})
    digest=hashlib.sha256()
    for p in pats: digest.update(len(p).to_bytes(4,'big')+p)
    shared=[depths[i] for i,n in enumerate(visits) if n>=2]
    return {'rows':rows,'summary':{'raw_count':len(prepared.raw_keywords),'k':len(pats),
            'duplicates_removed':prepared.duplicates_removed,'L_bytes':sum(map(len,pats)),
            'm_min':min(map(len,pats)),'m_median':statistics.median(map(len,pats)),
            'm_max':max(map(len,pats)),'trie_states':len(children),
            'shared_prefix_nodes':len(shared),'max_shared_prefix_bytes':max(shared,default=0),
            'keyword_sha256':digest.hexdigest(),'source_to_pid':list(prepared.source_to_pid),
            'corpus_sha256':None if text is None else hashlib.sha256(text).hexdigest(),
            'N_bytes':None if text is None else len(text)}}


def write_profile(profile,outdir,label='provisional'):
    outdir=Path(outdir);outdir.mkdir(parents=True,exist_ok=True)
    with (outdir/'keyword_profile.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(profile['rows'][0]));w.writeheader();w.writerows(profile['rows'])
    summary={**profile['summary'],'source_status':label}
    (outdir/'keyword_profile_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--keywords',type=Path,required=True)
    p.add_argument('--text',type=Path)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--source-status',default='provisional')
    a=p.parse_args()
    prepared=prepare_keywords(a.keywords.read_text(encoding='utf-8-sig').splitlines())
    text=None if a.text is None else normalize_text(a.text.read_bytes().decode('utf-8-sig'))
    write_profile(profile_keywords(prepared,text),a.out,a.source_status)
    print(json.dumps({'k':len(prepared.patterns),'out':str(a.out)},ensure_ascii=False))


if __name__=='__main__':main()
