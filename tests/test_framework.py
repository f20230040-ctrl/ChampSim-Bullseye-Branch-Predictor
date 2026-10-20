"""
Unit tests for the experiment framework:
1. Cache capacity and set calculations
2. Configuration generation
3. Simulator log parsing and error handling
"""

import os
import sys
import unittest

workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

from framework.geometry import (
    calculate_sets,
    calculate_capacity_bytes,
    CacheGeometry,
)
from framework.parser import (
    parse_champsim_log,
    IncompleteExecutionError,
)


class TestCacheGeometry(unittest.TestCase):
    def test_standard_16way_geometries(self):
        # 1MB 16-way: 1024 sets
        self.assertEqual(calculate_sets(1 * 1024 * 1024, 16, 64), 1024)
        # 2MB 16-way: 2048 sets
        self.assertEqual(calculate_sets(2 * 1024 * 1024, 16, 64), 2048)
        # 4MB 16-way: 4096 sets
        self.assertEqual(calculate_sets(4 * 1024 * 1024, 16, 64), 4096)
        # 8MB 16-way: 8192 sets
        self.assertEqual(calculate_sets(8 * 1024 * 1024, 16, 64), 8192)

    def test_corrected_8way_geometry(self):
        # 2MB 8-way must be 4096 sets (NOT 2048 sets)
        sets_2mb_8way = calculate_sets(2 * 1024 * 1024, 8, 64)
        self.assertEqual(sets_2mb_8way, 4096)
        self.assertEqual(calculate_capacity_bytes(4096, 8, 64), 2 * 1024 * 1024)

    def test_legacy_mismatched_8way_geometry(self):
        # Verify that 2048 sets with 8 ways was actually 1MB
        cap_legacy = calculate_capacity_bytes(2048, 8, 64)
        self.assertEqual(cap_legacy, 1 * 1024 * 1024)

    def test_invalid_parameters_raise_error(self):
        # Non-power-of-two ways
        with self.assertRaises(ValueError):
            calculate_sets(2 * 1024 * 1024, 7, 64)
        # Negative capacity
        with self.assertRaises(ValueError):
            calculate_sets(-1024, 16, 64)

    def test_geometry_cflags_generation(self):
        geom_2mb_16way = CacheGeometry(capacity_mb=2, ways=16)
        self.assertEqual(geom_2mb_16way.sets_per_core, 2048)
        self.assertEqual(geom_2mb_16way.get_cflags(), "-DLLC_SET=NUM_CPUS*2048 -DLLC_WAY=16")

        geom_2mb_8way = CacheGeometry(capacity_mb=2, ways=8)
        self.assertEqual(geom_2mb_8way.sets_per_core, 4096)
        self.assertEqual(geom_2mb_8way.get_cflags(), "-DLLC_SET=NUM_CPUS*4096 -DLLC_WAY=8")


class TestLogParser(unittest.TestCase):
    def test_parse_real_existing_log(self):
        sample_log = "results_10M/401.bzip2-38B.champsimtrace.xz-bimodal-no-no-no-no-lru-1core-2MB-16way.txt"
        if not os.path.exists(sample_log):
            self.skipTest(f"Sample log {sample_log} not found")

        data = parse_champsim_log(sample_log, is_path=True)
        self.assertEqual(data["status"], "COMPLETED")
        self.assertEqual(data["header"]["warmup_instructions"], 1000000)
        self.assertEqual(data["header"]["simulation_instructions"], 10000000)
        self.assertEqual(data["header"]["llc_sets"], 2048)
        self.assertEqual(data["header"]["llc_ways"], 16)
        self.assertIn(0, data["cpu"])
        # True ROI IPC is 0.939065 (legacy parse_results.py erroneously summed heartbeat + finished + ROI lines to 2.89722)
        self.assertAlmostEqual(data["cpu"][0]["ipc"], 0.939065, places=4)
        self.assertIn("LLC", data["cache"])
        self.assertGreater(data["cache"]["LLC"]["access"], 0)

    def test_incomplete_log_raises_error(self):
        truncated_text = (
            "*** ChampSim Multicore Out-of-Order Simulator ***\n"
            "Warmup Instructions: 1000000\n"
            "Simulation Instructions: 10000000\n"
            "LLC sets: 2048\n"
            "LLC ways: 16\n"
        )
        with self.assertRaises(IncompleteExecutionError):
            parse_champsim_log(truncated_text, is_path=False)


if __name__ == "__main__":
    unittest.main()
