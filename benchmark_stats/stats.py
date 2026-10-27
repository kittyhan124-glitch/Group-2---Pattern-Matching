#!/usr/bin/env python3
"""Tổng hợp thống kê từ raw_results.csv (TV2). Công thức khớp mục 10 của bản phân công.

Đầu ra (thư mục --outdir):
  summary.csv      mỗi (RQ, corpus, S, k, m, thuật toán): median/min/max theo seed, dao động, thông lượng, count, bộ nhớ
  speedup.csv      speedup ghép cặp cùng seed: t_baseline / t_candidate (>1: candidate nhanh hơn baseline)
  total_cost.csv   build + r * scan cho r = 1, 5, 20 và ngưỡng hòa vốn (chỉ khi điều kiện cho phép)
  consistency.csv  mọi thuật toán trong cùng cấu hình có cùng count/check và oracle_ok hay không

Nguyên tắc: bỏ lượt warm-up; KHÔNG coi chín lượt (3 seed x 3 lần) là chín mẫu độc lập; ca timeout/lỗi giữ nguyên
trạng thái, không thay bằng 0; không tính khoảng tin cậy (chỉ 3 seed -> mô tả).
"""
import argparse, os
import numpy as np
import pandas as pd

PAIRS = {  # (baseline, candidate) cho từng RQ
    "RQ1": [("bf", "kmp")], "RQ2A": [("bf", "kmp")], "RQ2B": [("bf", "kmp")],
    "RQ3": [("kmp-k", "ac"), ("lib-find", "ac"), ("kmp-k", "lib-find")],
}
CFG = ["rq", "corpus_id", "S_MiB", "k", "m_bytes"]
RS = (1, 5, 20)


def load(path):
    d = pd.read_csv(path, keep_default_na=True, dtype={"seed": "string"})
    for c in ["S_MiB", "k", "m_bytes", "N_bytes", "build_ms", "elapsed_ms", "throughput_MiB_s", "mem_peak_bytes",
              "states", "transitions", "comparisons", "failure_steps", "count", "lines_flagged", "lines_total", "cpu_wall_ratio"]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d["seed"] = d["seed"].fillna("na")
    return d


def per_cell(d):
    """Một dòng cho mỗi (cell_id): thống kê 3 lượt đo trong cùng seed (dao động do đo lặp)."""
    t = d[d["mode"] == "timing"]
    rows = []
    for cid, g in t.groupby("cell_id", sort=False):
        ok = g[g["status"] == "ok"]
        first = g.iloc[0]
        r = {c: first[c] for c in CFG + ["cell_id", "algo", "variant", "seed", "sigma", "N_bytes"]}
        if len(ok) == 0:
            r.update(status=g["status"].iloc[0], n_reps=0)
        else:
            e, b = ok["elapsed_ms"], ok["build_ms"]
            r.update(status="ok", n_reps=len(ok), elapsed_med=e.median(), elapsed_min=e.min(), elapsed_max=e.max(),
                     build_med=b.median(), build_min=b.min(), build_max=b.max(),
                     rep_range_pct=100 * (e.max() - e.min()) / e.median() if e.median() > 0 else np.nan,
                     count=ok["count"].iloc[0], check=ok["check"].iloc[0], oracle_ok=int(ok["oracle_ok"].min()),
                     N_bytes=ok["N_bytes"].iloc[0],
                     cpu_wall_min=ok["cpu_wall_ratio"].min() if "cpu_wall_ratio" in ok else np.nan,
                     n_contended=int((ok["cpu_wall_ratio"] < 0.90).sum()) if "cpu_wall_ratio" in ok else 0)
        rows.append(r)
    out = pd.DataFrame(rows)
    # gắn thông tin từ lượt count và mem
    cnt = d[(d["mode"] == "count") & (d["status"] == "ok")].set_index("cell_id")
    mem = d[(d["mode"] == "mem") & (d["status"] == "ok")].set_index("cell_id")
    for col, src in (("comparisons", cnt), ("failure_steps", cnt), ("lines_flagged", cnt), ("lines_total", cnt),
                     ("mem_peak_bytes", mem), ("states", mem), ("transitions", mem), ("L_bytes", mem)):
        out[col] = out["cell_id"].map(src[col])
    for src in (cnt, mem):
        out["N_bytes"] = out["N_bytes"].fillna(out["cell_id"].map(src["N_bytes"]))
    return out


def build_summary(pc):
    rows = []
    for key, g in pc.groupby(CFG + ["algo"], dropna=False, sort=False):
        ok = g[g["status"] == "ok"]
        base = dict(zip(CFG + ["algo"], key))
        base["variant"] = g["variant"].iloc[0] if isinstance(g["variant"].iloc[0], str) else ""
        base["sigma"] = g["sigma"].iloc[0]
        base["n_seeds_planned"] = len(g)
        base["n_seeds_ok"] = len(ok)
        base["status"] = "ok" if len(ok) == len(g) else ("timeout" if (g["status"] == "timeout").any() else
                                                         "partial/error")
        if len(ok):
            sm = ok["elapsed_med"]
            N = ok["N_bytes"].iloc[0]
            base.update(
                N_bytes=int(N), elapsed_ms_median=sm.median(), elapsed_ms_seed_min=sm.min(), elapsed_ms_seed_max=sm.max(),
                within_seed_range_pct_median=ok["rep_range_pct"].median(),     # dao động do đo lặp
                between_seed_range_pct=100 * (sm.max() - sm.min()) / sm.median() if sm.median() > 0 else np.nan,
                build_ms_median=ok["build_med"].median(),
                n_contended_cells=int((ok["n_contended"] > 0).sum()), cpu_wall_min=ok["cpu_wall_min"].min(),
                throughput_MiB_s=(N / 2 ** 20) / (sm.median() / 1000) if sm.median() > 0 else np.nan,
                count_median=ok["count"].median(), count_same_across_seeds=int(ok["count"].nunique() == 1),
                oracle_ok_all=int(ok["oracle_ok"].min()),
                lines_flagged_over_total=(ok["lines_flagged"] / ok["lines_total"]).median())
        # lượt count/mem là tiến trình riêng: lấy theo từng lượt, kể cả khi lượt timing của ô bị timeout
        base.update(
            comparisons_per_N=(g["comparisons"] / g["N_bytes"]).median(),
            failure_steps_per_N=(g["failure_steps"] / g["N_bytes"]).median(),
            mem_peak_bytes=g["mem_peak_bytes"].median(), states=g["states"].median(),
            transitions=g["transitions"].median())
        rows.append(base)
    s = pd.DataFrame(rows)
    return s.sort_values(["rq", "corpus_id", "S_MiB", "k", "m_bytes", "algo"]).reset_index(drop=True)


def build_speedup(pc):
    ok = pc[pc["status"] == "ok"]
    rows = []
    for rq, pairs in PAIRS.items():
        sub = pc[pc["rq"] == rq]
        for key, g in sub.groupby(CFG, dropna=False, sort=False):
            gi = g.set_index(["algo", "seed"])
            for b, c in pairs:
                seeds = sorted(set(g[g["algo"] == b]["seed"]) & set(g[g["algo"] == c]["seed"]))
                vals = []
                for sd in seeds:
                    rb, rc = gi.loc[(b, sd)], gi.loc[(c, sd)]
                    row = dict(zip(CFG, key), baseline=b, candidate=c, seed=sd, baseline_status=rb["status"],
                               candidate_status=rc["status"])
                    if rb["status"] == "ok" and rc["status"] == "ok":
                        row.update(t_baseline_ms=rb["elapsed_med"], t_candidate_ms=rc["elapsed_med"],
                                   speedup=rb["elapsed_med"] / rc["elapsed_med"])
                        vals.append(row["speedup"])
                    rows.append(row)
                if vals:
                    for lab, f in (("median", np.median), ("min", np.min), ("max", np.max)):
                        rows.append(dict(zip(CFG, key), baseline=b, candidate=c, seed=lab, speedup=f(vals),
                                         baseline_status="ok", candidate_status="ok"))
    return pd.DataFrame(rows)


def build_total_cost(pc):
    rows = []
    for key, g in pc[pc["rq"] == "RQ3"].groupby(CFG, dropna=False, sort=False):
        agg = {}
        for a, ga in g.groupby("algo"):
            ok = ga[ga["status"] == "ok"]
            agg[a] = (ok["build_med"].median(), ok["elapsed_med"].median(), len(ok) == len(ga)) if len(ok) else None
        for a, v in agg.items():
            if v is None or not v[2]:
                continue
            b, s, _ = v
            row = dict(zip(CFG, key), algo=a, build_ms=b, scan_ms=s)
            for r in RS:
                row[f"total_r{r}_ms"] = b + r * s
            rows.append(row)
        for base, cand in PAIRS["RQ3"]:
            if agg.get(base) and agg.get(cand) and agg[base][2] and agg[cand][2]:
                (bb, sb, _), (bc, sc, _) = agg[base], agg[cand]
                if sc >= sb:
                    note, be = "candidate scan không nhanh hơn baseline: không có hòa vốn", np.nan
                elif bc <= bb:
                    note, be = "candidate không tốn build hơn: lợi ngay từ r=1", 0.0
                else:
                    be, note = (bc - bb) / (sb - sc), "r* = (build_c - build_b)/(scan_b - scan_c); r nguyên >= ceil(r*)"
                rows.append(dict(zip(CFG, key), algo=f"BREAKEVEN {base}->{cand}", build_ms=bc - bb, scan_ms=sb - sc,
                                 breakeven_r=be, note=note))
    return pd.DataFrame(rows)


def build_consistency(pc):
    rows = []
    for key, g in pc.groupby(CFG, dropna=False, sort=False):
        for sd, gs in g.groupby("seed"):
            ok = gs[gs["status"] == "ok"]
            if len(ok):
                rows.append(dict(zip(CFG, key), seed=sd, algos=",".join(ok["algo"]), n_algos=len(ok),
                                 same_count=int(ok["count"].nunique() == 1), same_check=int(ok["check"].nunique() == 1),
                                 all_oracle_ok=int(ok["oracle_ok"].min())))
    return pd.DataFrame(rows)


def main(raw, outdir):
    os.makedirs(outdir, exist_ok=True)
    d = load(raw)
    pc = per_cell(d)
    outs = {"summary.csv": build_summary(pc), "speedup.csv": build_speedup(pc), "total_cost.csv": build_total_cost(pc),
            "consistency.csv": build_consistency(pc)}
    for name, df in outs.items():
        df.to_csv(os.path.join(outdir, name), index=False, float_format="%.6g")
        print(f"{name}: {len(df)} dòng")
    pc.to_csv(os.path.join(outdir, "per_cell.csv"), index=False, float_format="%.6g")
    return outs


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="raw_results.csv"); ap.add_argument("--outdir", default=".")
    a = ap.parse_args()
    main(a.raw, a.outdir)
