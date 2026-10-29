#!/usr/bin/env python3
"""Runner benchmark của TV2 – Pattern Matching (CSD203).

Lệnh con:
  machine     ghi nhật ký máy/phiên bản (machine_log.json)
  plan        sinh plan.csv từ ma trận RQ1–RQ3 (mục 8 bản phân công)
  estimate    pilot trên tiền tố nhỏ -> workload_estimate.csv (khối lượng + dự báo timeout)
  run         chạy plan -> raw_results.csv (timing / count / mem tách tiến trình, có timeout, có resume)
  worker      (nội bộ) một phép đo trong một tiến trình mới

Nguyên tắc: mỗi phép đo chạy trong TIẾN TRÌNH RIÊNG; corpus và mẫu đã nằm trong RAM trước khi bấm giờ;
lượt timing không bật đếm phép toán hay tracemalloc; tải file/NFC/UTF-8/oracle nằm ngoài thời gian đo.
"""
import argparse, csv, hashlib, importlib.util, json, os, platform, subprocess, sys, time
from time import perf_counter_ns

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, HERE)
import common  # noqa: E402

SEEDS = [11, 29, 47]
TIMEOUT_S = 60
ALGO_FILES = {"bf": "bf.py", "kmp": "kmp.py", "kmp-k": "kmpk.py", "ac": "ac.py", "lib-find": "libfind.py",
              # ablation RQ3 (quy định chung §3): AC tắt Output Link / tắt Failure Link
              "ac-noout": "ac_noout.py", "ac-nofail": "ac_nofail.py"}
ALGO_DIR = os.path.join(HERE, "algos")   # wrapper nối mã thật của thành viên; algos_ref/ chỉ để thử runner
DEFAULT_PLAN = os.path.join(HERE, "plan.csv")
DEFAULT_RAW = os.path.join(ROOT, "results", "raw", "raw_results.csv")

PLAN_FIELDS = ["cell_id", "group_id", "rq", "corpus_id", "corpus_file", "binary", "S_MiB", "algo", "seed",
               "k", "m", "sigma", "pattern_spec", "timeout_s"]
RAW_FIELDS = ["run_id", "rq", "cell_id", "corpus_id", "corpus_hash", "keyword_hash", "seed", "rep", "mode",
              "code_version", "algo", "variant", "N_bytes", "S_MiB", "k", "m_bytes", "m_min", "m_median", "m_max",
              "L_bytes", "sigma", "build_ms", "elapsed_ms", "throughput_MiB_s", "mem_peak_bytes",
              "mem_current_bytes", "cpu_wall_ratio", "states", "transitions", "failure_steps", "comparisons", "state_transitions", "output_steps", "count", "check",
              "lines_total", "lines_flagged", "oracle_ok", "status", "timeout_s", "note"]


# ------------------------------------------------------------------ tiện ích
def load_algo(name, algo_dir):
    path = os.path.join(algo_dir, ALGO_FILES[name])
    spec = importlib.util.spec_from_file_location("algo_" + name.replace("-", "_"), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.NAME == name, f"{path}: NAME={mod.NAME!r} khác {name!r}"
    h = hashlib.sha256(open(path, "rb").read())
    src = getattr(mod, "SOURCE", None)          # file thuật toán thật mà wrapper gọi vào
    if src:
        h.update(open(os.path.join(ROOT, src), "rb").read())
    return mod, h.hexdigest()[:10]


def ensure_parent(path):
    """Tạo thư mục chứa tệp đầu ra nếu chưa có (vd. results/raw/ trên bản clone mới)."""
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    return path


def file_sha(path, _cache={}):
    if path not in _cache:
        _cache[path] = common.sha256_file(path)
    return _cache[path]


def code_version(algo_hash):
    return f"{algo_hash}+{hashlib.sha256(open(__file__, 'rb').read()).hexdigest()[:8]}"


def medians(xs):
    xs = sorted(xs)
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def classify_process_exit(returncode, stderr):
    if returncode in (-9, 137, -1073741801, 3221225495) or "MemoryError" in stderr:
        return "oom"
    return "crash"


# ------------------------------------------------------------------ WORKER (một phép đo)
def worker(cell, lane, algo_dir, prefix):
    mod, _ = load_algo(cell["algo"], algo_dir)
    text = common.load_text(os.path.join(ROOT, cell["corpus_file"]), binary=bool(int(cell["binary"])))
    if prefix:
        text = text[:prefix]
    spec = json.loads(cell["pattern_spec"])
    patterns = common.make_patterns(spec, ROOT)
    common.check_patterns(patterns)
    N = len(text)
    out = {"N_bytes": N, "keyword_hash": common.keyword_hash(patterns), "L_bytes": sum(map(len, patterns)),
           "m_min": min(map(len, patterns)), "m_median": medians([len(p) for p in patterns]),
           "m_max": max(map(len, patterns)), "k": len(patterns)}

    if lane == "oracle":
        c, ck, lf, lt = common.oracle(text, patterns)
        out.update(count=c, check=ck, lines_flagged=lf, lines_total=lt)

    elif lane == "timing":
        hc = common.Collector()
        hit = hc.hit
        c0 = time.process_time_ns()
        t0 = perf_counter_ns()
        S = mod.build(patterns)
        t1 = perf_counter_ns()
        mod.scan(text, S, hit)
        t2 = perf_counter_ns()
        c1 = time.process_time_ns()
        # Mã Python đơn luồng chạy liên tục thì CPU-time ≈ wall-time; thấp hơn nghĩa là tiến trình bị tranh CPU/bị hoãn.
        out.update(build_ms=(t1 - t0) / 1e6, elapsed_ms=(t2 - t1) / 1e6, count=hc.count, check=hc.check,
                   cpu_wall_ratio=round((c1 - c0) / max(t2 - t0, 1), 4))

    elif lane == "count":
        S = mod.build(patterns)
        lc = common.LineCollector(text)
        r = mod.scan_counted(text, S, lc.hit)
        st, tr = mod.size(S)
        out.update(comparisons=r.get("comparisons"), failure_steps=r.get("failure_steps"),
                   state_transitions=r.get("state_transitions"), output_steps=r.get("output_steps"), states=st,
                   transitions=tr, count=lc.count, check=lc.check, lines_flagged=len(lc.lines),
                   lines_total=len(lc.nl) + 1)

    elif lane == "mem":
        import tracemalloc
        tracemalloc.start()                     # ngay trước build; corpus/mẫu đã nạp xong nên không tính
        S = mod.build(patterns)
        cur, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        st, tr = mod.size(S)
        out.update(mem_peak_bytes=peak, mem_current_bytes=cur, states=st, transitions=tr)
    else:
        raise ValueError(lane)
    print("RESULT " + json.dumps(out))


# ------------------------------------------------------------------ ORCHESTRATOR
def spawn(cell, lane, timeout_s, algo_dir, prefix=0):
    timeout_s = min(float(timeout_s), TIMEOUT_S)
    cmd = [sys.executable, os.path.abspath(__file__), "worker", "--cell", json.dumps(cell), f"--{lane}",
           "--algo-dir", algo_dir, "--prefix", str(prefix)]
    # PYTHONIOENCODING: tiến trình con luôn ghi UTF-8 (Windows mặc định cp1252 không có "ễ", "ệ"...)
    env = dict(os.environ, PYTHONHASHSEED="0", PYTHONIOENCODING="utf-8")
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=timeout_s, env=env)
    except subprocess.TimeoutExpired:
        return "timeout", {}, f"quá {timeout_s}s"
    if p.returncode != 0:
        msg = (p.stderr.strip().splitlines() or ["?"])[-1][:200]
        return classify_process_exit(p.returncode, p.stderr), {}, msg
    for line in p.stdout.splitlines():
        if line.startswith("RESULT "):
            try:
                return "ok", json.loads(line[7:]), ""
            except json.JSONDecodeError as exc:
                return "crash", {}, f"RESULT không phải JSON hợp lệ: {exc}"
    return "crash", {}, "tiến trình kết thúc nhưng không có RESULT"


class Store:
    def __init__(self, path):
        ensure_parent(path)
        self.path, self.done, self.rows = path, set(), {}
        if os.path.exists(path):
            with open(path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                if reader.fieldnames != RAW_FIELDS:
                    raise ValueError(f"{path}: header khác schema hiện tại (RAW_FIELDS); "
                                     "hãy ghi ra file --out mới thay vì nối tiếp file cũ")
                self.rows = {r["run_id"]: r for r in reader}
                self.done = set(self.rows)
        else:
            with open(path, "w", newline="", encoding="utf-8") as f:
                csv.DictWriter(f, RAW_FIELDS).writeheader()

    def add(self, row):
        row = {k: ("" if row.get(k) is None else row.get(k)) for k in RAW_FIELDS}
        with open(self.path, "a", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, RAW_FIELDS).writerow(row)
        self.done.add(row["run_id"])
        self.rows[row["run_id"]] = row


def base_row(cell, mode, rep, ver, corpus_hash):
    return {"rq": cell["rq"], "cell_id": cell["cell_id"], "corpus_id": cell["corpus_id"], "corpus_hash": corpus_hash,
            "seed": cell["seed"], "rep": rep, "mode": mode, "code_version": ver, "algo": cell["algo"],
            "S_MiB": cell["S_MiB"], "sigma": cell["sigma"], "timeout_s": TIMEOUT_S}


def merge(row, res):
    for k, v in res.items():
        if k in RAW_FIELDS:
            row[k] = v
    if "m_min" in res and res["m_min"] == res["m_max"]:
        row["m_bytes"] = res["m_min"]
    return row


def run_plan(args):
    plan = list(csv.DictReader(open(args.plan, newline="", encoding="utf-8")))
    if args.cell:
        plan = [r for r in plan if r["cell_id"] == args.cell]
        if len(plan) != 1:
            raise ValueError(f"--cell phải khớp đúng một cell_id trong plan; tìm thấy {len(plan)}")
    elif args.rq:
        plan = [r for r in plan if r["rq"] in args.rq]
    if args.limit:
        gids = list(dict.fromkeys(r["group_id"] for r in plan))[:args.limit]
        plan = [r for r in plan if r["group_id"] in gids]
    if any(r["rq"] in ("RQ3", "RQ3ABL") for r in plan):
        stub_notice = os.path.join(ROOT, "data", "keywords", "STUB_NOTICE.txt")
        if os.path.exists(stub_notice):
            raise RuntimeError(f"RQ3 đang bị chặn vì bộ từ khóa là stub: {stub_notice}")
    store = Store(args.out)
    oracle_path = os.path.join(HERE, "oracle_cache.json")
    ocache = json.load(open(oracle_path, encoding="utf-8")) if os.path.exists(oracle_path) else {}
    groups = {}
    for r in plan:
        groups.setdefault(r["group_id"], []).append(r)
    t_start = time.time()
    for gi, (gid, cells) in enumerate(groups.items(), 1):
        c0 = cells[0]
        T = TIMEOUT_S
        corpus_hash = file_sha(os.path.join(ROOT, c0["corpus_file"]))
        print(f"[{gi}/{len(groups)}] {gid}  ({time.time() - t_start:.0f}s)", flush=True)
        # --- oracle độc lập (bytes.find) cho nhóm này
        okey = f"{corpus_hash}|{c0['pattern_spec']}"
        if okey not in ocache:
            st, res, note = spawn(c0 | {"algo": "lib-find"}, "oracle", T, args.algo_dir)
            if st != "ok":
                print("   !! oracle lỗi:", note); continue
            ocache[okey] = res
            json.dump(ocache, open(oracle_path, "w", encoding="utf-8"))
        orc = ocache[okey]
        algos = [c["algo"] for c in cells]
        by_algo = {c["algo"]: c for c in cells}
        ver = {a: code_version(load_algo(a, args.algo_dir)[1]) for a in algos}
        dead = set()                                       # thuật toán đã timeout ở warm-up

        def record(cell, lane, mode, rep, tmo):
            rid = f"{cell['cell_id']}|{lane}|{mode}{rep}"
            if rid in store.done:
                return None
            for attempt in range(1 + (args.retry_contended if mode == "timing" else 0)):
                st, res, note = spawn(cell, lane, tmo, args.algo_dir)
                row = base_row(cell, mode, rep, ver[cell["algo"]], corpus_hash)
                row.update(run_id=rid, status=st, note=note, variant=load_algo(cell["algo"], args.algo_dir)[0].VARIANT)
                if st == "ok":
                    merge(row, res)
                    N = res["N_bytes"]
                    if lane == "timing":
                        row["throughput_MiB_s"] = (N / 2 ** 20) / (res["elapsed_ms"] / 1000) if res["elapsed_ms"] > 0 else ""
                    if lane in ("timing", "count"):
                        row["oracle_ok"] = int(res["count"] == orc["count"] and res["check"] == orc["check"] and
                                               (lane == "timing" or res["lines_flagged"] == orc["lines_flagged"]))
                        if lane == "count":
                            row["lines_total"], row["lines_flagged"] = res["lines_total"], res["lines_flagged"]
                        if not row["oracle_ok"]:
                            row["status"] = "wrong"; row["note"] = f"lệch oracle: {res['count']}/{orc['count']}"
                else:
                    row["k"] = cell["k"]; row["m_bytes"] = cell["m"]
                contended = (lane == "timing" and mode == "timing" and row["status"] == "ok"
                             and res.get("cpu_wall_ratio", 1) < args.min_cpu_ratio)
                if contended:
                    row["note"] = f"nhiễu CPU (cpu/wall={res['cpu_wall_ratio']})"
                    if attempt < args.retry_contended:        # giữ lại bản bị loại để minh bạch, rồi đo lại
                        row["mode"], row["run_id"] = "discarded", f"{rid}|try{attempt + 1}"
                        store.add(row)
                        continue
                store.add(row)
                return row

        # warm-up (loại khỏi thống kê nhưng vẫn lưu)
        for a in algos:
            r = record(by_algo[a], "timing", "warmup", 0, T)
            if r is None:
                rid = f"{by_algo[a]['cell_id']}|timing|warmup0"
                r = store.rows.get(rid)
            if r and r["status"] != "ok":
                dead.add(a)
        # ba lượt đo, luân phiên thứ tự thuật toán
        for rep in range(1, args.reps + 1):
            order = algos[(rep - 1) % len(algos):] + algos[:(rep - 1) % len(algos)]
            for a in order:
                if a not in dead:
                    r = record(by_algo[a], "timing", "timing", rep, T)
                    if r is None:
                        rid = f"{by_algo[a]['cell_id']}|timing|timing{rep}"
                        r = store.rows.get(rid)
                    if r and r["status"] != "ok":
                        dead.add(a)
        # lượt đếm phép toán và lượt bộ nhớ (tiến trình riêng, KHÔNG dùng để lấy thời gian)
        for a in algos:
            if not args.no_count and (a not in dead or args.force_count):
                record(by_algo[a], "count", "count", 1, T)
            if not args.no_mem:
                record(by_algo[a], "mem", "mem", 1, T)
    print(f"xong, {time.time() - t_start:.0f}s -> {args.out}")


# ------------------------------------------------------------------ PLAN
def pat_cut(path, m, seed, utf8=True):
    return json.dumps({"kind": "cut", "from": path, "m": m, "seed": seed, "utf8": utf8})


def build_plan(timeout_s, seeds=SEEDS):
    rows = []

    def add(rq, corpus_id, file, binary, S, algo, seed, k, m, sigma, spec):
        gid = f"{rq}|{corpus_id}|S{S}|k{k}|m{m}|seed{seed}"
        rows.append({"cell_id": f"{gid}|{algo}", "group_id": gid, "rq": rq, "corpus_id": corpus_id,
                     "corpus_file": file, "binary": int(binary), "S_MiB": S, "algo": algo, "seed": seed, "k": k,
                     "m": m, "sigma": sigma, "pattern_spec": spec, "timeout_s": timeout_s})

    # RQ1: BF vs KMP; T1(vi) và T3(σ=26); S=1..16; m=16; 3 seed
    for seed in seeds:
        for S in (1, 2, 4, 8, 16):
            for algo in ("bf", "kmp"):
                add("RQ1", "T1_vi", f"data/T1_vi_{S}MiB.bin", 0, S, algo, seed, 1, 16, "",
                    pat_cut("data/T1_vi_1MiB.bin", 16, seed))
                add("RQ1", "T3_s26", f"data/T3_sigma26_{S}MiB_seed{seed}.bin", 0, S, algo, seed, 1, 16, 26,
                    pat_cut(f"data/T3_sigma26_1MiB_seed{seed}.bin", 16, seed, False))
    # RQ2A: T3 4 MiB, m=64, σ=2,4,26,256
    for seed in seeds:
        for sg, f, b in ((2, "data/T3_sigma2_4MiB.bin", 0), (4, "data/T3_sigma4_4MiB.bin", 0),
                         (26, f"data/T3_sigma26_4MiB_seed{seed}.bin", 0), (256, "data/T3_sigma256_4MiB.bin", 1)):
            for algo in ("bf", "kmp"):
                add("RQ2A", f"T3_s{sg}", f, b, 4, algo, seed, 1, 64, sg, pat_cut(f, 64, seed, False))
    # RQ2B: T4 (xác định, không phụ thuộc seed), m=8,64,1024
    for m in (8, 64, 1024):
        for algo in ("bf", "kmp"):
            add("RQ2B", "T4", "data/T4_worst_4MiB.bin", 0, 4, algo, "", 1, m, 1, json.dumps({"kind": "t4", "m": m}))
    # RQ3: kmp-k vs ac, lib-find làm mốc; T1/T2 4 & 16 MiB; k=1,10,100,1000 (tệp từ khóa do TV5 cấp)
    for seed in seeds:
        for lang, cid in (("vi", "T1_vi"), ("en", "T2_en")):
            for S in (4, 16):
                for k in (1, 10, 100, 1000):
                    for algo in ("kmp-k", "ac", "lib-find"):
                        add("RQ3", cid, f"data/{cid}_{S}MiB.bin", 0, S, algo, seed, k, 16, "",
                            json.dumps({"kind": "file", "path": f"data/keywords/kw_{lang}_seed{seed}_k{k}.txt"}))
    # RQ3 ABLATION (quy định chung §3): tắt lần lượt Output Link, Failure Link của AC; T1/T2 4 MiB
    for seed in seeds:
        for lang, cid in (("vi", "T1_vi"), ("en", "T2_en")):
            for k in (1, 10, 100, 1000):
                for algo in ("ac", "ac-noout", "ac-nofail"):
                    add("RQ3ABL", cid, f"data/{cid}_4MiB.bin", 0, 4, algo, seed, k, 16, "",
                        json.dumps({"kind": "file", "path": f"data/keywords/kw_{lang}_seed{seed}_k{k}.txt"}))
    return rows


def cmd_plan(a):
    rows = build_plan(a.timeout_s)
    with open(ensure_parent(a.out), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, PLAN_FIELDS)
        w.writeheader(); w.writerows(rows)
    from collections import Counter
    c = Counter(r["rq"] for r in rows)
    print(f"{len(rows)} ô cấu hình -> {a.out}:", dict(c))


# ------------------------------------------------------------------ ESTIMATE (pilot)
def cmd_estimate(a):
    plan = list(csv.DictReader(open(a.plan, newline="", encoding="utf-8")))
    classes = {}
    for r in plan:
        key = (r["rq"], r["corpus_id"].split("_s")[0] if r["rq"] == "RQ2A" else r["corpus_id"], r["algo"], r["k"],
               r["m"], r["sigma"])
        classes.setdefault(key, []).append(r)
    est = {}
    for i, (key, cells) in enumerate(classes.items(), 1):
        rep = [c for c in cells if str(c["seed"]) in ("11", "")] or cells
        c = max(rep, key=lambda c: int(c["S_MiB"]))
        st, res, note = spawn(c, "timing", a.pilot_timeout, a.algo_dir, prefix=a.prefix)
        if st == "ok":
            est[key] = (st, res["build_ms"] / 1000, res["elapsed_ms"] / 1000 / res["N_bytes"])
        else:
            est[key] = (st, None, None)
        print(f"[{i}/{len(classes)}] {key} -> {st}", flush=True)
    out = []
    for key, cells in classes.items():
        st, b, per_byte = est[key]
        for c in cells:
            N = int(c["S_MiB"]) * 2 ** 20
            T = TIMEOUT_S
            if st == "ok":
                scan = per_byte * N
                pred = "timeout" if scan > T else "ok"
                # chính sách run: warm-up + 3 đo + count (~2.5x) + mem; nếu dự báo timeout: chỉ T (warm-up) + mem
                cost = (T + b) if pred == "timeout" else 4 * (b + scan) + 2.5 * scan + 3 * b
            else:
                scan, pred, cost = None, "timeout(pilot)", T
            out.append({"cell_id": c["cell_id"], "rq": c["rq"], "algo": c["algo"], "S_MiB": c["S_MiB"], "k": c["k"],
                        "m": c["m"], "est_build_s": b, "est_scan_s": scan, "prediction": pred,
                        "est_cell_cost_s": cost, "note": f"ngoại suy tuyến tính từ tiền tố {a.prefix} byte"})
    with open(ensure_parent(a.out), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, list(out[0].keys()))
        w.writeheader(); w.writerows(out)
    tot = sum(float(o["est_cell_cost_s"]) for o in out)
    print(f"-> {a.out}: {len(out)} ô, tổng ước lượng ≈ {tot / 3600:.1f} giờ (chưa tính lệch do ngoại suy)")


def _machine_windows(info):
    """Thông tin máy trên Windows (không có os.getloadavg, /proc, /sys)."""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as k:
            info["cpu_model"] = winreg.QueryValueEx(k, "ProcessorNameString")[0].strip()
            info["cpu_mhz_nominal"] = winreg.QueryValueEx(k, "~MHz")[0]
    except Exception:
        info["cpu_model"] = platform.processor()
    try:
        import ctypes

        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
        st = MEMORYSTATUSEX()
        st.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st)):
            info["mem_total_MiB"] = st.ullTotalPhys // 2 ** 20
            info["mem_load_pct"] = st.dwMemoryLoad
    except Exception:
        pass
    try:   # chế độ nguồn: nên là "High performance"/"Ultimate Performance" khi đo
        r = subprocess.run(["powercfg", "/getactivescheme"], capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            info["power_scheme"] = r.stdout.strip()
    except Exception:
        pass
    try:   # đang cắm sạc hay chạy pin
        import ctypes

        class SYSTEM_POWER_STATUS(ctypes.Structure):
            _fields_ = [("ACLineStatus", ctypes.c_byte), ("BatteryFlag", ctypes.c_byte),
                        ("BatteryLifePercent", ctypes.c_byte), ("SystemStatusFlag", ctypes.c_byte),
                        ("BatteryLifeTime", ctypes.c_ulong), ("BatteryFullLifeTime", ctypes.c_ulong)]
        ps = SYSTEM_POWER_STATUS()
        if ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(ps)):
            info["ac_power"] = {0: False, 1: True}.get(ps.ACLineStatus)
    except Exception:
        pass


def _machine_posix(info):
    try:
        info["loadavg"] = os.getloadavg()
    except (AttributeError, OSError):
        pass
    try:
        info["cpu_model"] = [l.split(":", 1)[1].strip() for l in open("/proc/cpuinfo") if l.startswith("model name")][0]
        info["mem_total_MiB"] = int([l for l in open("/proc/meminfo") if l.startswith("MemTotal")][0].split()[1]) // 1024
    except Exception:
        info.setdefault("cpu_model", platform.processor())
    for p in ("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor",):
        if os.path.exists(p):
            info["cpu_governor"] = open(p).read().strip()


def cmd_machine(a):
    info = {"time_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()), "python": sys.version,
            "implementation": platform.python_implementation(), "platform": platform.platform(),
            "machine": platform.machine(), "cpu_count": os.cpu_count(), "bench_py_sha256": hashlib.sha256(
                open(__file__, "rb").read()).hexdigest()}
    if os.name == "nt":
        _machine_windows(info)
    else:
        _machine_posix(info)
    with open(ensure_parent(a.out), "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2, ensure_ascii=False)
    print(json.dumps(info, indent=2, ensure_ascii=False))


def main():
    for stream in (sys.stdout, sys.stderr):      # in tiếng Việt ra console/file trên Windows không làm dừng runner
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("machine"); p.add_argument("--out", default=os.path.join(HERE, "machine_log.json"))
    p = sp.add_parser("plan"); p.add_argument("--out", default=DEFAULT_PLAN); p.add_argument("--timeout-s", type=int, choices=(TIMEOUT_S,), default=TIMEOUT_S)
    p = sp.add_parser("estimate")
    p.add_argument("--plan", default=DEFAULT_PLAN); p.add_argument("--out", default=os.path.join(HERE, "workload_estimate.csv"))
    p.add_argument("--prefix", type=int, default=65536); p.add_argument("--pilot-timeout", type=int, default=TIMEOUT_S)
    p.add_argument("--algo-dir", default=ALGO_DIR)
    p = sp.add_parser("run")
    p.add_argument("--plan", default=DEFAULT_PLAN); p.add_argument("--out", default=DEFAULT_RAW)
    p.add_argument("--algo-dir", default=ALGO_DIR); p.add_argument("--rq", nargs="*")
    p.add_argument("--cell", help="chỉ chạy đúng cell_id được chỉ định")
    p.add_argument("--reps", type=int, default=3); p.add_argument("--limit", type=int, default=0, help="chỉ chạy N nhóm đầu (debug)")
    p.add_argument("--no-count", action="store_true"); p.add_argument("--no-mem", action="store_true")
    p.add_argument("--force-count", action="store_true")
    p.add_argument("--min-cpu-ratio", type=float, default=0.90,
                   help="lượt timing có cpu/wall thấp hơn ngưỡng bị coi là nhiễu")
    p.add_argument("--retry-contended", type=int, default=2, help="số lần đo lại tối đa cho lượt bị nhiễu")
    p = sp.add_parser("worker")
    p.add_argument("--cell", required=True)
    lane = p.add_mutually_exclusive_group(required=True)
    lane.add_argument("--lane", choices=("oracle", "timing", "count", "mem"))
    lane.add_argument("--oracle", dest="lane", action="store_const", const="oracle", help="= --lane oracle")
    lane.add_argument("--timing", dest="lane", action="store_const", const="timing", help="= --lane timing")
    lane.add_argument("--count", dest="lane", action="store_const", const="count",
                      help="= --lane count (quy định chung §6: lượt đếm phép toán riêng)")
    lane.add_argument("--mem", dest="lane", action="store_const", const="mem",
                      help="= --lane mem (quy định chung §6: lượt tracemalloc riêng)")
    p.add_argument("--algo-dir", required=True); p.add_argument("--prefix", type=int, default=0)
    a = ap.parse_args()
    if a.cmd == "worker":
        worker(json.loads(a.cell), a.lane, a.algo_dir, a.prefix)
    elif a.cmd == "run":
        run_plan(a)
    else:
        {"plan": cmd_plan, "estimate": cmd_estimate, "machine": cmd_machine}[a.cmd](a)


if __name__ == "__main__":
    main()
