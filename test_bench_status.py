import unittest
import gc
import inspect
from types import SimpleNamespace
from unittest.mock import patch

import bench
from review_tv2 import recompute_per_cell


class BenchmarkStatusTests(unittest.TestCase):
    def test_timing_lane_does_not_change_gc_state(self):
        source = inspect.getsource(bench.worker)

        self.assertNotIn("gc.disable()", source)
        self.assertNotIn("gc.enable()", source)
        self.assertNotIn("gc.collect()", source)
        self.assertTrue(gc.isenabled())

    def test_plan_uses_sixty_second_timeout(self):
        plan = bench.build_plan(bench.TIMEOUT_S)
        self.assertTrue(plan)
        self.assertEqual({row["timeout_s"] for row in plan}, {60})

    def test_process_exit_classification(self):
        self.assertEqual(bench.classify_process_exit(1, "MemoryError"), "oom")
        self.assertEqual(bench.classify_process_exit(1, "ValueError: bad input"), "crash")
        self.assertEqual(bench.classify_process_exit(-1073741801, ""), "oom")

    @patch("bench.subprocess.run")
    def test_spawn_never_exceeds_sixty_seconds(self, run):
        run.return_value = SimpleNamespace(returncode=0, stdout="RESULT {}\n", stderr="")

        status, result, note = bench.spawn({}, "timing", 300, "algos_ref")

        self.assertEqual((status, result, note), ("ok", {}, ""))
        self.assertEqual(run.call_args.kwargs["timeout"], 60)

    def test_failed_warmup_keeps_its_failure_status(self):
        warmup = {
            "mode": "warmup",
            "status": "timeout",
            "cell_id": "cell-1",
            "rq": "RQ1",
            "corpus_id": "T1",
            "S_MiB": "1",
            "k": "1",
            "m_bytes": "16",
            "algo": "bf",
            "seed": "11",
        }

        result = recompute_per_cell([warmup])["cell-1"]

        self.assertEqual(result["status"], "timeout")
        self.assertEqual(result["n_reps"], 0)
        self.assertNotIn("elapsed_med", result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
