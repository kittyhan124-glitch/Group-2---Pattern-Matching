#!/usr/bin/env python3
"""Vẽ biểu đồ từ summary.csv / total_cost.csv (TV2). Ca timeout/lỗi hiện bằng dấu X, không thay bằng 0."""
import argparse, os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

COL = {"bf": "#c0392b", "kmp": "#2471a3", "kmp-k": "#7d3c98", "ac": "#1e8449", "lib-find": "#7f8c8d"}
MK = {"bf": "o", "kmp": "s", "kmp-k": "^", "ac": "D", "lib-find": "v"}
NOTE = "Điểm = median của 3 median theo seed (mỗi median từ 3 lượt đo); dải = min–max giữa các seed."


def _line(ax, df, x, y, lo, hi, algo, label=None):
    df = df.sort_values(x)
    ax.plot(df[x], df[y], marker=MK[algo], color=COL[algo], label=label or algo, lw=1.6, ms=5)
    if lo in df and hi in df and df[lo].notna().any():
        ax.fill_between(df[x], df[lo], df[hi], color=COL[algo], alpha=0.15, lw=0)


def _plain_ticks(ax, vals):
    vals = sorted(set(int(v) for v in vals))
    ax.set_xticks(vals); ax.set_xticklabels([str(v) for v in vals]); ax.minorticks_off()


def _tmo(ax, df, x, algo):
    t = df[df["status"] != "ok"]
    if len(t):
        ymax = ax.get_ylim()[1]
        ax.scatter(t[x], [ymax * 0.85] * len(t), marker="X", s=70, color=COL[algo], zorder=5, label=f"{algo}: status != ok (vị trí dọc không có nghĩa)")


def fig_rq1(s, out):
    d = s[s["rq"] == "RQ1"]
    if d.empty: return
    corp = sorted(d["corpus_id"].unique())
    f, ax = plt.subplots(2, len(corp), figsize=(5.4 * len(corp), 7), squeeze=False, sharex=True)
    for j, c in enumerate(corp):
        for a in ("bf", "kmp"):
            g = d[(d.corpus_id == c) & (d.algo == a) & (d.status == "ok")]
            if g.empty: continue
            g = g.assign(tp_lo=(g.N_bytes / 2**20) / (g.elapsed_ms_seed_max / 1000),
                         tp_hi=(g.N_bytes / 2**20) / (g.elapsed_ms_seed_min / 1000))
            _line(ax[0, j], g, "S_MiB", "throughput_MiB_s", "tp_lo", "tp_hi", a)
            _line(ax[1, j], g, "S_MiB", "comparisons_per_N", "comparisons_per_N", "comparisons_per_N", a)
        ax[0, j].set(title=f"RQ1 – {c}", ylabel="Thông lượng (MiB/s)"); ax[0, j].set_ylim(bottom=0)
        ax[1, j].set(xlabel="Kích thước dữ liệu S (MiB)", ylabel="Số phép so sánh / N (byte)")
        cm = d[(d.corpus_id == c)].comparisons_per_N.dropna()
        if len(cm):
            pad = max((cm.max() - cm.min()) * 0.5, 0.01)
            ax[1, j].set_ylim(cm.min() - pad, cm.max() + pad)
        ax[1, j].axhline(1.0, color="k", lw=0.8, ls=":")
        for r in (0, 1):
            ax[r, j].set_xscale("log", base=2); ax[r, j].set_xticks(sorted(d.S_MiB.unique()))
            ax[r, j].set_xticklabels([str(int(v)) for v in sorted(d.S_MiB.unique())]); ax[r, j].grid(alpha=.3); ax[r, j].legend()
    f.suptitle("RQ1 – BF vs KMP, m = 16 byte", y=0.995); f.text(0.5, 0.005, NOTE, ha="center", fontsize=8)
    f.tight_layout(rect=(0, 0.02, 1, 0.98)); f.savefig(out, dpi=150); plt.close(f)


def fig_rq2(s, out):
    a_, b_ = s[s["rq"] == "RQ2A"], s[s["rq"] == "RQ2B"]
    if a_.empty and b_.empty: return
    f, ax = plt.subplots(2, 2, figsize=(11, 7.5))
    for col, (d, x, title, xl) in enumerate(((a_, "sigma", "RQ2 A – T3 4 MiB, m = 64", "σ (số ký hiệu)"),
                                              (b_, "m_bytes", "RQ2 B – T4 4 MiB, mẫu a^(m−1)b", "m (byte)"))):
        if d.empty: continue
        for a in ("bf", "kmp"):
            g = d[d.algo == a]
            gk = g[g.status == "ok"]
            if gk.empty:
                continue
            _line(ax[0, col], gk, x, "elapsed_ms_median", "elapsed_ms_seed_min", "elapsed_ms_seed_max", a)
            _line(ax[1, col], gk, x, "comparisons_per_N", "comparisons_per_N", "comparisons_per_N", a)
        ax[0, col].set_yscale("log"); ax[0, col].set(title=title, ylabel="Thời gian quét (ms, log)")
        for a in ("bf", "kmp"):
            _tmo(ax[0, col], d[d.algo == a], x, a)
        for a in ("bf", "kmp"):
            gt = d[(d.algo == a) & (d.comparisons_per_N.isna())]
            if len(gt):
                ax[1, col].scatter(gt[x], [ax[1, col].get_ylim()[1] * 0.85] * len(gt), marker="X", s=70,
                                   color=COL[a], label=f"{a}: chưa đo (status != ok)")
        ax[1, col].set(xlabel=xl, ylabel="Số phép so sánh / N")
        for r in (0, 1):
            ax[r, col].set_xscale("log", base=2) if col == 1 else ax[r, col].set_xscale("log", base=2)
            ax[r, col].set_xticks(sorted(d[x].dropna().unique())); ax[r, col].set_xticklabels([str(int(v)) for v in sorted(d[x].dropna().unique())])
            ax[r, col].grid(alpha=.3, which="both"); ax[r, col].legend(fontsize=8)
        if col == 1: ax[1, col].set_yscale("log")
    f.text(0.5, 0.005, NOTE + " T4 xác định nên không có seed thật.", ha="center", fontsize=8)
    f.tight_layout(rect=(0, 0.02, 1, 1)); f.savefig(out, dpi=150); plt.close(f)


def fig_rq3(s, out_scan, out_mem):
    d = s[s["rq"] == "RQ3"]
    if d.empty: return
    combos = sorted(d[["corpus_id", "S_MiB"]].drop_duplicates().itertuples(index=False))
    n = len(combos)
    f, ax = plt.subplots(2, n, figsize=(4.6 * n, 7.5), squeeze=False)
    for j, (c, S) in enumerate(combos):
        for a in ("kmp-k", "ac", "lib-find"):
            g = d[(d.corpus_id == c) & (d.S_MiB == S) & (d.algo == a)]
            gk = g[g.status == "ok"]
            if gk.empty: continue
            _line(ax[0, j], gk, "k", "elapsed_ms_median", "elapsed_ms_seed_min", "elapsed_ms_seed_max", a)
            _line(ax[1, j], gk, "k", "build_ms_median", "build_ms_median", "build_ms_median", a)
        for r, yl in ((0, "Thời gian quét (ms)"), (1, "Thời gian build (ms)")):
            ax[r, j].set_xscale("log"); ax[r, j].set_yscale("log"); ax[r, j].set(ylabel=yl, xlabel="k (số từ khóa)")
            ax[r, j].grid(alpha=.3, which="both"); _plain_ticks(ax[r, j], d.k.unique())
        ax[0, j].set_title(f"RQ3 – {c}, {int(S)} MiB")
        for a in ("kmp-k", "ac", "lib-find"):
            _tmo(ax[0, j], d[(d.corpus_id == c) & (d.S_MiB == S) & (d.algo == a)], "k", a)
        ax[0, j].legend(fontsize=7)
    f.text(0.5, 0.005, NOTE, ha="center", fontsize=8); f.tight_layout(rect=(0, 0.02, 1, 1))
    f.savefig(out_scan, dpi=150); plt.close(f)

    m = d[d.mem_peak_bytes.notna() & d.states.notna()]
    if m.empty: return
    f, ax = plt.subplots(1, 2, figsize=(10, 4.2))
    for a in ("kmp-k", "ac"):
        g = m[m.algo == a]
        ax[0].scatter(g["states"], g["mem_peak_bytes"] / 2**20, color=COL[a], marker=MK[a], label=a)
        ax[1].scatter(g["k"], g["mem_peak_bytes"] / 2**20, color=COL[a], marker=MK[a], label=a)
    ax[0].set(xlabel="Số trạng thái Q", ylabel="Đỉnh bộ nhớ vùng build (MiB, tracemalloc)")
    ax[1].set(xlabel="k (số từ khóa)", ylabel="Đỉnh bộ nhớ vùng build (MiB, tracemalloc)")
    for x in ax:
        x.set_xscale("log"); x.set_yscale("log"); x.grid(alpha=.3, which="both"); x.legend()
    f.text(0.5, 0.005, "tracemalloc chỉ theo dõi khối nhớ Python, không phải RSS của tiến trình.", ha="center", fontsize=8)
    f.tight_layout(rect=(0, 0.03, 1, 1)); f.savefig(out_mem, dpi=150); plt.close(f)


def fig_breakeven(s, out, maxr=30):
    d = s[(s.rq == "RQ3") & (s.status == "ok")]
    if d.empty: return
    ks = sorted(d.k.unique())[-2:]
    cs = sorted(d[["corpus_id", "S_MiB"]].drop_duplicates().itertuples(index=False))[:1]
    if not cs: return
    c, S = cs[0]
    f, ax = plt.subplots(1, len(ks), figsize=(5.2 * len(ks), 4.2), squeeze=False)
    r = np.arange(1, maxr + 1)
    for j, k in enumerate(ks):
        for a in ("kmp-k", "ac", "lib-find"):
            g = d[(d.corpus_id == c) & (d.S_MiB == S) & (d.k == k) & (d.algo == a)]
            if g.empty: continue
            b, sc = g.build_ms_median.iloc[0], g.elapsed_ms_median.iloc[0]
            ax[0, j].plot(r, (b + r * sc) / 1000, color=COL[a], label=a)
        ax[0, j].set_yscale("log")
        ax[0, j].set(title=f"{c}, {int(S)} MiB, k = {int(k)}", xlabel="r (số lần quét dùng lại bộ từ khóa)",
                     ylabel="Tổng chi phí build + r×scan (s, log)"); ax[0, j].grid(alpha=.3, which="both"); ax[0, j].legend()
    f.tight_layout(); f.savefig(out, dpi=150); plt.close(f)


def main(summary, outdir):
    os.makedirs(outdir, exist_ok=True)
    s = pd.read_csv(summary)
    fig_rq1(s, os.path.join(outdir, "fig_rq1_throughput.png"))
    fig_rq2(s, os.path.join(outdir, "fig_rq2_sigma_m.png"))
    fig_rq3(s, os.path.join(outdir, "fig_rq3_scan_build_vs_k.png"), os.path.join(outdir, "fig_rq3_memory.png"))
    fig_breakeven(s, os.path.join(outdir, "fig_rq3_total_cost.png"))
    print(sorted(os.listdir(outdir)))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--summary", default="summary.csv"); ap.add_argument("--outdir", default="figs")
    a = ap.parse_args(); main(a.summary, a.outdir)
