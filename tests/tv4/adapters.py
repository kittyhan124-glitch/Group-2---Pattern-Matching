"""Read-only test adapters for actual member modules, not benchmark stand-ins.

BF/KMP are called per pattern only to compare results with a multipattern
oracle. This wrapper is NOT the k-KMP implementation or a timing adapter.
"""
import importlib

ALGORITHMS=('bf','kmp','kmp_k','ac_fail')


def scan_algorithm(name,text,patterns,counted=False):
    if name not in ALGORITHMS: raise ValueError('unknown student algorithm: '+name)
    mod=importlib.import_module(name)
    if name in ('bf','kmp'):
        out=[]
        for pid,p in enumerate(patterns):
            structure=mod.build(p)
            if counted:
                hits=(mod.scan_with_comparisons(text,structure)[0] if name=='bf'
                      else mod.scan_stats(text,structure)[0])
            else:
                hits=mod.scan(text,structure)
            out.extend((pos,pid) for pos,_ in hits)
        return sorted(out)
    structure=mod.build(list(patterns))
    if counted and name=='kmp_k':
        return sorted(mod.scan_stats(text,structure)[0])
    if counted:
        return sorted(mod.scan_counted(text,structure)[0])
    return sorted(mod.scan(text,structure))
