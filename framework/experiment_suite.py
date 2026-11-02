"""
Comprehensive experiment suite for:
1. Branch prediction evaluation (Bimodal, Gshare, Hashed Perceptron, Bullseye, Adaptive Bullseye)
2. Cache replacement evaluation across validated cache geometries (LRU, MRU, Random, Adaptive HCIT)
Includes strict validation, metadata recording, and automated CSV export.
"""

import csv
import json
import os
import sys
import time
from typing import Dict, Any, List

workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

from framework.geometry import CacheGeometry
from framework.builder import ChampSimBuilder
from framework.runner import run_simulation


def run_validation_check(workspace_root: str):
    """
    Runs a small multi-configuration validation test (100k instructions)
    confirming both Bullseye, Adaptive Bullseye, and Adaptive HCIT (with 4096 sets 8-way)
    build, run, and parse without errors before launching full sweeps.
    """
    print("=" * 70)
    print("STAGE 1: VALIDATION CHECK (Small scale smoke test for all custom modules)")
    print("=" * 70)

    builder = ChampSimBuilder(workspace_root)
    val_out_dir = os.path.join(workspace_root, "results", "validation")
    os.makedirs(val_out_dir, exist_ok=True)

    geom_2mb_16way = CacheGeometry(capacity_mb=2, ways=16, line_size=64, num_cpus=1)
    geom_2mb_8way = CacheGeometry(capacity_mb=2, ways=8, line_size=64, num_cpus=1)

    test_cases = [
        {
            "name": "Bullseye Predictor on 2MB 16-way",
            "branch": "bullseye",
            "repl": "lru",
            "geom": geom_2mb_16way,
            "trace": "401.bzip2-277B.champsimtrace.xz",
        },
        {
            "name": "Adaptive Bullseye Predictor on 2MB 16-way",
            "branch": "adaptive_bullseye",
            "repl": "lru",
            "geom": geom_2mb_16way,
            "trace": "401.bzip2-277B.champsimtrace.xz",
        },
        {
            "name": "Adaptive HCIT Replacement on Corrected 2MB 8-way (4096 sets)",
            "branch": "bimodal",
            "repl": "adaptive_hcit",
            "geom": geom_2mb_8way,
            "trace": "401.bzip2-38B.champsimtrace.xz",
        },
    ]

    for tc in test_cases:
        print(f"\n[*] Testing: {tc['name']}")
        bin_path = builder.build(
            branch=tc["branch"],
            llc_repl=tc["repl"],
            geometry=tc["geom"],
            cores=1,
        )
        print(f"[+] Built binary: {os.path.basename(bin_path)}")

        trace_path = os.path.join(workspace_root, "dpc3_traces", tc["trace"])
        log_path = os.path.join(val_out_dir, f"val_{tc['branch']}_{tc['repl']}_{tc['geom'].ways}way.txt")

        parsed = run_simulation(
            binary_path=bin_path,
            trace_paths=[trace_path],
            output_log_path=log_path,
            warmup_instructions=50_000,
            simulation_instructions=50_000,
            timeout_seconds=60,
        )
        print(f"[+] Run successful: status={parsed['status']}, IPC={parsed['cpu'][0]['ipc']:.4f}")
        if tc["branch"] in ["bullseye", "adaptive_bullseye"]:
            print(f"    Branch accuracy: {parsed['branch'][0]['accuracy_pct']:.2f}% | MPKI: {parsed['branch'][0]['mpki']:.4f}")
        if tc["repl"] == "adaptive_hcit":
            print(f"    LLC Sets: {parsed['header']['llc_sets']} (Expected: 4096) | LLC Ways: {parsed['header']['llc_ways']} (Expected: 8)")
            assert parsed["header"]["llc_sets"] == 4096, "LLC sets must be 4096 for 2MB 8-way"
            assert parsed["header"]["llc_ways"] == 8, "LLC ways must be 8"

    print("\n[+] ALL VALIDATION CHECKS PASSED!\n")


def run_branch_prediction_suite(workspace_root: str, n_warm: int = 1_000_000, n_sim: int = 10_000_000) -> List[Dict[str, Any]]:
    """
    Executes branch prediction evaluation across:
    - Predictors: bimodal, gshare, hashed_perceptron (baseline), bullseye, adaptive_bullseye
    - Traces: 401.bzip2-277B, 401.bzip2-38B, 403.gcc-16B, 450.soplex-92B, 482.sphinx3-1522B
    """
    print("=" * 70)
    print("STAGE 2: BRANCH PREDICTION BENCHMARK SUITE")
    print(f"Parameters: Warmup = {n_warm:,} | Simulation = {n_sim:,}")
    print("=" * 70)

    builder = ChampSimBuilder(workspace_root)
    out_dir = os.path.join(workspace_root, "results", "branch_suite")
    os.makedirs(out_dir, exist_ok=True)

    geom = CacheGeometry(capacity_mb=2, ways=16, line_size=64, num_cpus=1)

    predictors = [
        "bimodal",
        "gshare",
        "hashed_perceptron",
        "bullseye",
        "adaptive_bullseye",
    ]

    traces = [
        "401.bzip2-277B.champsimtrace.xz",
        "401.bzip2-38B.champsimtrace.xz",
        "403.gcc-16B.champsimtrace.xz",
        "450.soplex-92B.champsimtrace.xz",
        "482.sphinx3-1522B.champsimtrace.xz",
    ]

    results = []

    # Build all binaries first
    binaries = {}
    for pred in predictors:
        print(f"[*] Compiling binary for predictor: {pred}")
        bin_path = builder.build(
            branch=pred,
            llc_repl="lru",
            geometry=geom,
            cores=1,
        )
        binaries[pred] = bin_path
        print(f"[+] Ready: {os.path.basename(bin_path)}")

    # Run simulations
    total_runs = len(predictors) * len(traces)
    run_idx = 0

    for trace_name in traces:
        trace_path = os.path.join(workspace_root, "dpc3_traces", trace_name)
        for pred in predictors:
            run_idx += 1
            log_name = f"{trace_name}_{pred}_2MB_16way.txt"
            log_path = os.path.join(out_dir, log_name)

            print(f"[{run_idx}/{total_runs}] Running {pred} on {trace_name}...")
            bin_path = binaries[pred]

            start_t = time.time()
            parsed = run_simulation(
                binary_path=bin_path,
                trace_paths=[trace_path],
                output_log_path=log_path,
                warmup_instructions=n_warm,
                simulation_instructions=n_sim,
                timeout_seconds=300,
            )
            elapsed = time.time() - start_t

            record = {
                "trace": trace_name,
                "predictor": pred,
                "warmup_instr": n_warm,
                "sim_instr": n_sim,
                "ipc": parsed["cpu"][0]["ipc"],
                "cycles": parsed["cpu"][0]["cycles"],
                "accuracy_pct": parsed["branch"][0]["accuracy_pct"],
                "mpki": parsed["branch"][0]["mpki"],
                "rob_occupancy": parsed["branch"][0]["rob_occupancy_at_mispredict"],
                "elapsed_sec": round(elapsed, 2),
                "log_file": log_name,
            }
            results.append(record)
            print(
                f"    -> Acc: {record['accuracy_pct']:.4f}% | "
                f"MPKI: {record['mpki']:.4f} | "
                f"IPC: {record['ipc']:.4f} | "
                f"Cycles: {record['cycles']:,} ({elapsed:.1f}s)"
            )

    # Save summary CSV
    csv_path = os.path.join(workspace_root, "results", "branch_suite_summary.csv")
    fieldnames = [
        "trace", "predictor", "warmup_instr", "sim_instr",
        "ipc", "cycles", "accuracy_pct", "mpki", "rob_occupancy",
        "elapsed_sec", "log_file"
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\n[+] Branch Suite Complete! Summary saved to {csv_path}\n")
    return results


def run_cache_replacement_suite(workspace_root: str, n_warm: int = 1_000_000, n_sim: int = 10_000_000) -> List[Dict[str, Any]]:
    """
    Executes cache replacement evaluation across:
    - Policies: lru (baseline), mru, random, adaptive_hcit
    - Validated Cache Geometries:
      - 1MB 16-way (sets=1024)
      - 2MB 16-way (sets=2048)
      - 4MB 16-way (sets=4096)
      - 8MB 16-way (sets=8192)
      - 2MB 8-way (sets=4096, corrected!)
      - 1MB 8-way (sets=2048, legacy config for direct comparison)
    - Traces: 401.bzip2-38B, 403.gcc-16B, 450.soplex-92B, 482.sphinx3-1522B
    """
    print("=" * 70)
    print("STAGE 3: CACHE REPLACEMENT BENCHMARK SUITE")
    print(f"Parameters: Warmup = {n_warm:,} | Simulation = {n_sim:,}")
    print("=" * 70)

    builder = ChampSimBuilder(workspace_root)
    out_dir = os.path.join(workspace_root, "results", "cache_suite")
    os.makedirs(out_dir, exist_ok=True)

    geometries = [
        {"name": "1MB_16way", "geom": CacheGeometry(capacity_mb=1, ways=16, line_size=64)},
        {"name": "2MB_16way", "geom": CacheGeometry(capacity_mb=2, ways=16, line_size=64)},
        {"name": "4MB_16way", "geom": CacheGeometry(capacity_mb=4, ways=16, line_size=64)},
        {"name": "8MB_16way", "geom": CacheGeometry(capacity_mb=8, ways=16, line_size=64)},
        {"name": "2MB_8way",  "geom": CacheGeometry(capacity_mb=2, ways=8,  line_size=64)}, # Corrected!
        {"name": "1MB_8way",  "geom": CacheGeometry(capacity_mb=1, ways=8,  line_size=64)}, # Legacy geometry
    ]

    policies = ["lru", "mru", "random", "adaptive_hcit"]

    traces = [
        "401.bzip2-38B.champsimtrace.xz",
        "403.gcc-16B.champsimtrace.xz",
        "450.soplex-92B.champsimtrace.xz",
        "482.sphinx3-1522B.champsimtrace.xz",
    ]

    results = []

    # Build all binaries
    binaries = {}
    for g_info in geometries:
        g_name = g_info["name"]
        geom = g_info["geom"]
        for pol in policies:
            key = (g_name, pol)
            print(f"[*] Building {pol} for geometry {g_name} (sets={geom.sets_per_core}, ways={geom.ways})...")
            bin_path = builder.build(
                branch="bimodal",
                llc_repl=pol,
                geometry=geom,
                cores=1,
            )
            binaries[key] = bin_path

    total_runs = len(geometries) * len(policies) * len(traces)
    run_idx = 0

    for g_info in geometries:
        g_name = g_info["name"]
        geom = g_info["geom"]
        for trace_name in traces:
            trace_path = os.path.join(workspace_root, "dpc3_traces", trace_name)
            for pol in policies:
                run_idx += 1
                key = (g_name, pol)
                bin_path = binaries[key]

                log_name = f"{trace_name}_{pol}_{g_name}.txt"
                log_path = os.path.join(out_dir, log_name)

                print(f"[{run_idx}/{total_runs}] Running {pol} on {trace_name} ({g_name})...")
                start_t = time.time()
                parsed = run_simulation(
                    binary_path=bin_path,
                    trace_paths=[trace_path],
                    output_log_path=log_path,
                    warmup_instructions=n_warm,
                    simulation_instructions=n_sim,
                    timeout_seconds=300,
                )
                elapsed = time.time() - start_t

                llc_stat = parsed["cache"].get("LLC", {})
                l1d_stat = parsed["cache"].get("L1D", {})
                l2c_stat = parsed["cache"].get("L2C", {})
                wb_stat = parsed["cache"].get("LLC_WRITEBACK", {})

                record = {
                    "trace": trace_name,
                    "policy": pol,
                    "geometry": g_name,
                    "capacity_mb": geom.capacity_mb,
                    "ways": geom.ways,
                    "sets": geom.sets_per_core,
                    "ipc": parsed["cpu"][0]["ipc"],
                    "cycles": parsed["cpu"][0]["cycles"],
                    "l1d_miss_rate": l1d_stat.get("miss_rate", 0.0),
                    "l2c_miss_rate": l2c_stat.get("miss_rate", 0.0),
                    "llc_accesses": llc_stat.get("access", 0),
                    "llc_hits": llc_stat.get("hit", 0),
                    "llc_misses": llc_stat.get("miss", 0),
                    "llc_hit_rate": llc_stat.get("hit_rate", 0.0),
                    "llc_miss_rate": llc_stat.get("miss_rate", 0.0),
                    "llc_mpki": (llc_stat.get("miss", 0) / (n_sim / 1000.0)),
                    "llc_writes": wb_stat.get("total_writes", 0),
                    "elapsed_sec": round(elapsed, 2),
                    "log_file": log_name,
                }
                results.append(record)
                print(
                    f"    -> IPC: {record['ipc']:.4f} | "
                    f"LLC Hit: {record['llc_hit_rate']*100:.2f}% | "
                    f"LLC MPKI: {record['llc_mpki']:.4f} | "
                    f"Writes: {record['llc_writes']} ({elapsed:.1f}s)"
                )

    # Save summary CSV
    csv_path = os.path.join(workspace_root, "results", "cache_suite_summary.csv")
    fieldnames = list(results[0].keys())
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\n[+] Cache Suite Complete! Summary saved to {csv_path}\n")
    return results


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # First execute the validation check
    run_validation_check(root)

    # Run full suites
    run_branch_prediction_suite(root, n_warm=1_000_000, n_sim=10_000_000)
    run_cache_replacement_suite(root, n_warm=1_000_000, n_sim=10_000_000)


if __name__ == "__main__":
    main()
