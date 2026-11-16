"""Tính lại các bảng trong results/<session>/analysis/ từ CSV thô của một phiên đo.

Dùng:
    python bench/analyze_results.py results/recorded_20261103_234305
    python bench/analyze_results.py results/supplement_20261104_025037

Đầu vào trong thư mục phiên:
    experiment_plan.csv   danh sách cell (thứ tự xuất bảng)
    raw_results.csv       các lượt warmup / timing / count / mem (dòng "discarded" bị bỏ)
    build_only.csv        (tùy chọn) thời gian dựng riêng cho RQ3

Đầu ra trong <session>/analysis/ (hoặc --outdir):
    per_cell_exact.csv    một dòng cho mỗi cell (một seed, một thuật toán)
    summary.csv           median qua các seed cho mỗi cấu hình
    paired_speedup.csv    speedup ghép cặp theo seed: scan(baseline) / scan(candidate)
    total_cost.csv        build + r * scan với r = 1, 5, 20 và điểm hòa vốn
"""
import argparse
import csv
import math
import os
import re
import statistics
import sys

PAIRS = {
    "RQ1": [("bf", "kmp")],
    "RQ2A": [("bf", "kmp")],
    "RQ3": [("kmp-k", "ac"), ("lib-find", "ac")],
    "RQ3ABL": [("ac-noout", "ac"), ("ac-nofail", "ac")],
}
CONTENDED_CPU_WALL = 0.9  # lượt timing có cpu/wall dưới ngưỡng này được đếm là bị tranh chấp CPU
COUNT_FIELDS = ["comparisons", "failure_steps", "state_transitions", "output_steps"]


def read(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write(path, fields, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: fmt(r.get(k)) for k in fields})


def fmt(v):
    if v is None or v == "":
        return ""
    if isinstance(v, float):
        return repr(v)
    return str(v)


def num(s):
    if s is None or s == "":
        return None
    # số nguyên đọc bằng int() để giữ chính xác giá trị > 2**53 (ví dụ cột check)
    try:
        return int(s)
    except ValueError:
        return float(s)


def as_float(v):
    return None if v is None else float(v)


def med(vals):
    vals = [v for v in vals if v is not None]
    return statistics.median(vals) if vals else None


def first(rows, key):
    for r in rows:
        if r.get(key) not in (None, ""):
            return num(r[key])
    return None


def no_size(cell_id):
    return re.sub(r"\|S\d+\|", "|S*|", cell_id)


def per_cell(plan, raw, build_only):
    by_cell = {}
    for r in raw:
        if r["mode"] != "discarded":
            by_cell.setdefault(r["cell_id"], []).append(r)
    builds = {}
    for r in build_only or []:
        if r["mode"] == "build" and r["status"] == "ok":
            builds.setdefault(no_size(r["cell_id"]), []).append(float(r["build_ms"]))

    out = []
    for p in plan:
        rows = by_cell.get(p["cell_id"], [])
        timing = [r for r in rows if r["mode"] == "timing" and r["status"] == "ok"]
        count = [r for r in rows if r["mode"] == "count" and r["status"] == "ok"]
        mem = [r for r in rows if r["mode"] == "mem" and r["status"] == "ok"]
        timeout = any(r["status"] == "timeout" for r in rows)
        N = first(rows, "N_bytes") or 0

        scans = [float(r["elapsed_ms"]) for r in timing]
        scan = med(scans)
        worker_build = med([float(r["build_ms"]) for r in timing if r["build_ms"] != ""])
        cpu = [float(r["cpu_wall_ratio"]) for r in timing if r["cpu_wall_ratio"] != ""]
        cell = {
            "cell_id": p["cell_id"], "group_id": p["group_id"], "rq": p["rq"],
            "corpus_id": p["corpus_id"], "algo": p["algo"], "seed": num(p["seed"]),
            "S_MiB": num(p["S_MiB"]), "k": num(p["k"]), "N_bytes": N,
            "status": "timeout" if timeout else "ok",
            "n_timing": len(timing), "scan_ms": scan,
            "scan_min_ms": min(scans) if scans else None,
            "scan_max_ms": max(scans) if scans else None,
            "cpu_wall_min": min(cpu) if cpu else None,
            "contended_timing": sum(1 for c in cpu if c < CONTENDED_CPU_WALL),
            "count": first(timing or count, "count"), "check": first(timing or count, "check"),
            "keyword_hash": next((r["keyword_hash"] for r in rows if r["keyword_hash"]), ""),
            # raw ghi m_median lúc "16", lúc "16.0"; bảng analysis luôn để dạng số thực
            "m_min": first(rows, "m_min"), "m_median": as_float(first(rows, "m_median")),
            "m_max": first(rows, "m_max"), "L_bytes": first(rows, "L_bytes"),
            "mem_peak_bytes": first(mem, "mem_peak_bytes"),
            "mem_current_bytes": first(mem, "mem_current_bytes"),
            "states": first(mem + count, "states"),
            "transitions": first(count, "transitions"),
            "lines_flagged": first(count, "lines_flagged"),
            "lines_total": first(count, "lines_total"),
            "count_status": "ok" if count else ("skipped_after_timing_failure" if timeout else ""),
            "memory_status": "ok" if mem else "",
            "throughput_MiB_s": (N / 2**20) / (scan / 1000) if scan else None,
        }
        for f in COUNT_FIELDS:
            cell[f] = first(count, f)
        if no_size(p["cell_id"]) in builds:
            # build-only chỉ đo ở 4 MiB; thời gian dựng không phụ thuộc N nên cell 16 MiB dùng lại
            cell["build_ms"] = med(builds[no_size(p["cell_id"])])
            cell["build_source"] = "separate build-only workers"
            cell["build_timing_worker_ms"] = worker_build
        else:
            cell["build_ms"] = worker_build
            cell["build_source"] = "timing worker"
            cell["build_timing_worker_ms"] = None
        out.append(cell)
    return out


def summarize(cells):
    groups = {}
    for c in cells:
        key = (c["rq"], c["corpus_id"], c["S_MiB"], c["k"], c["algo"])
        groups.setdefault(key, []).append(c)
    out = []
    for (rq, corpus, S, k, algo), cs in groups.items():
        ok = [c for c in cs if c["status"] == "ok"]
        n_to = sum(1 for c in cs if c["status"] == "timeout")
        scan = med([c["scan_ms"] for c in ok])
        N = cs[0]["N_bytes"]
        row = {
            "rq": rq, "corpus_id": corpus, "S_MiB": S, "k": k, "algo": algo,
            "seeds_observed": len(cs), "seeds_ok": len(ok), "seeds_timeout": n_to,
            "status": "ok" if len(ok) == len(cs) else ("timeout" if not ok else "partial"),
            "scan_ms": scan,
            "throughput_MiB_s": (N / 2**20) / (scan / 1000) if scan else None,
            "build_ms": med([c["build_ms"] for c in cs]),
            "build_source": cs[0]["build_source"],
            "scan_seed_min_ms": min(c["scan_ms"] for c in ok) if ok else None,
            "scan_seed_max_ms": max(c["scan_ms"] for c in ok) if ok else None,
            "within_seed_range_pct_median": med(
                [100 * (c["scan_max_ms"] - c["scan_min_ms"]) / c["scan_ms"] for c in ok]),
            "m_min_over_seeds": min(c["m_min"] for c in cs),
            "m_max_over_seeds": max(c["m_max"] for c in cs),
            "n_contended_final_timings": sum(c["contended_timing"] for c in cs),
        }
        for f in ["mem_peak_bytes", "mem_current_bytes", "states", "transitions",
                  "L_bytes", "lines_flagged", "lines_total"]:
            row[f] = med([c[f] for c in cs])
        for f in COUNT_FIELDS:
            row[f + "_per_N"] = med([c[f] / c["N_bytes"] for c in ok if c[f] is not None])
        out.append(row)
    return out


def paired(cells, summary):
    by = {}
    for c in cells:
        by[(c["rq"], c["corpus_id"], c["S_MiB"], c["k"], c["algo"], c["seed"])] = c
    summ = {(s["rq"], s["corpus_id"], s["S_MiB"], s["k"], s["algo"]): s for s in summary}
    configs = []
    for s in summary:
        key = (s["rq"], s["corpus_id"], s["S_MiB"], s["k"])
        if key not in configs:
            configs.append(key)
    seeds = sorted({c["seed"] for c in cells})
    sp, tc = [], []
    for key in configs:
        for base, cand in PAIRS.get(key[0], []):
            if key + (base,) not in summ or key + (cand,) not in summ:
                continue
            ratios, ok_pairs = [], []
            for sd in seeds:
                b, c = by.get(key + (base, sd)), by.get(key + (cand, sd))
                if b and c and b["status"] == "ok" and c["status"] == "ok":
                    ratios.append(b["scan_ms"] / c["scan_ms"])
                    ok_pairs.append((b, c))
            row = dict(zip(["rq", "corpus_id", "S_MiB", "k"], key), baseline=base, candidate=cand,
                       n_pairs_ok=len(ratios), paired_speedup=med(ratios),
                       paired_speedup_min=min(ratios) if ratios else None,
                       paired_speedup_max=max(ratios) if ratios else None)
            sp.append(row)
            if not ratios:
                continue
            sb, sc = summ[key + (base,)], summ[key + (cand,)]
            t = dict(row, base_build_ms=sb["build_ms"], candidate_build_ms=sc["build_ms"],
                     base_scan_ms=sb["scan_ms"], candidate_scan_ms=sc["scan_ms"])
            for r in (1, 5, 20):
                # tổng chi phí tính theo từng seed (build + r*scan của chính seed đó) rồi lấy median
                t[f"base_total_r{r}_ms"] = med([b["build_ms"] + r * b["scan_ms"] for b, _ in ok_pairs])
                t[f"candidate_total_r{r}_ms"] = med([c["build_ms"] + r * c["scan_ms"] for _, c in ok_pairs])
            gain = sb["scan_ms"] - sc["scan_ms"]
            if gain > 0:
                t["break_even_integer_r"] = max(1, math.ceil((sc["build_ms"] - sb["build_ms"]) / gain))
            tc.append(t)
    return sp, tc


CELL_FIELDS = ["cell_id", "group_id", "rq", "corpus_id", "algo", "seed", "S_MiB", "k", "N_bytes",
               "status", "n_timing", "scan_ms", "build_ms", "scan_min_ms", "scan_max_ms",
               "cpu_wall_min", "contended_timing", "count", "check", "keyword_hash", "m_min",
               "m_median", "m_max", "L_bytes", "mem_peak_bytes", "mem_current_bytes", "states",
               "transitions", "comparisons", "failure_steps", "state_transitions", "output_steps",
               "lines_flagged", "lines_total", "count_status", "memory_status", "build_source",
               "throughput_MiB_s"]
SUMMARY_FIELDS = ["rq", "corpus_id", "S_MiB", "k", "algo", "seeds_observed", "seeds_ok",
                  "seeds_timeout", "status", "scan_ms", "throughput_MiB_s", "build_ms",
                  "build_source", "scan_seed_min_ms", "scan_seed_max_ms",
                  "within_seed_range_pct_median", "mem_peak_bytes", "mem_current_bytes",
                  "states", "transitions", "L_bytes", "lines_flagged", "lines_total",
                  "comparisons_per_N", "failure_steps_per_N", "state_transitions_per_N",
                  "output_steps_per_N", "m_min_over_seeds", "m_max_over_seeds",
                  "n_contended_final_timings"]
PAIR_FIELDS = ["rq", "corpus_id", "S_MiB", "k", "baseline", "candidate", "n_pairs_ok",
               "paired_speedup", "paired_speedup_min", "paired_speedup_max"]
COST_FIELDS = PAIR_FIELDS + ["base_build_ms", "candidate_build_ms", "base_scan_ms",
                             "candidate_scan_ms", "base_total_r1_ms", "candidate_total_r1_ms",
                             "base_total_r5_ms", "candidate_total_r5_ms", "base_total_r20_ms",
                             "candidate_total_r20_ms", "break_even_integer_r"]


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # console Windows (cp1252) không in được tiếng Việt
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("session", help="thư mục phiên đo, ví dụ results/recorded_20261103_234305")
    ap.add_argument("--outdir", help="mặc định: <session>/analysis")
    a = ap.parse_args()
    outdir = a.outdir or os.path.join(a.session, "analysis")
    os.makedirs(outdir, exist_ok=True)

    plan = read(os.path.join(a.session, "experiment_plan.csv"))
    raw = read(os.path.join(a.session, "raw_results.csv"))
    bpath = os.path.join(a.session, "build_only.csv")
    build_only = read(bpath) if os.path.exists(bpath) else None

    cells = per_cell(plan, raw, build_only)
    summary = summarize(cells)
    sp, tc = paired(cells, summary)
    cell_fields = CELL_FIELDS + (["build_timing_worker_ms"] if build_only else [])
    write(os.path.join(outdir, "per_cell_exact.csv"), cell_fields, cells)
    write(os.path.join(outdir, "summary.csv"), SUMMARY_FIELDS, summary)
    write(os.path.join(outdir, "paired_speedup.csv"), PAIR_FIELDS, sp)
    write(os.path.join(outdir, "total_cost.csv"), COST_FIELDS, tc)
    print(f"{len(cells)} cell, {len(summary)} cấu hình, {len(sp)} cặp -> {outdir}")


if __name__ == "__main__":
    main()
