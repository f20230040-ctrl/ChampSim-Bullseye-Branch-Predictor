"""
Automated smoke test for the ChampSim experiment framework.
Builds a binary with the new builder, runs a short simulation,
and parses the result to confirm end-to-end functionality.
"""

import os
import sys

workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

from framework.geometry import CacheGeometry
from framework.builder import ChampSimBuilder
from framework.runner import run_simulation


def main():
    workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(f"[*] Workspace root: {workspace_root}")

    # 1. Define geometry (2 MiB, 16-way)
    geometry = CacheGeometry(capacity_mb=2, ways=16, line_size=64, num_cpus=1)
    print(f"[*] Configured Geometry: {geometry}")
    print(f"[*] CFlags: {geometry.get_cflags()}")

    # 2. Build simulator binary cleanly
    builder = ChampSimBuilder(workspace_root)
    print("[*] Building binary via ChampSimBuilder...")
    bin_path = builder.build(
        branch="bimodal",
        llc_repl="lru",
        geometry=geometry,
        cores=1,
    )
    print(f"[+] Successfully built: {bin_path}")

    # 3. Select trace
    trace_file = os.path.join(workspace_root, "dpc3_traces", "401.bzip2-38B.champsimtrace.xz")
    if not os.path.exists(trace_file):
        print(f"[-] Error: Trace file not found at {trace_file}")
        sys.exit(1)

    # 4. Run short smoke simulation (100K warmup, 100K simulation)
    smoke_out = os.path.join(workspace_root, "results", "smoke", "smoke_bimodal_lru_2MB_16way.txt")
    print(f"[*] Executing smoke test run -> {smoke_out}")

    parsed = run_simulation(
        binary_path=bin_path,
        trace_paths=[trace_file],
        output_log_path=smoke_out,
        warmup_instructions=100_000,
        simulation_instructions=100_000,
        timeout_seconds=60,
    )

    # 5. Verify outputs
    print("[+] Simulation completed successfully!")
    print(f"    - Status: {parsed['status']}")
    print(f"    - LLC Sets: {parsed['header'].get('llc_sets')}")
    print(f"    - LLC Ways: {parsed['header'].get('llc_ways')}")
    print(f"    - CPU 0 IPC: {parsed['cpu'][0]['ipc']}")
    print(f"    - CPU 0 Instructions: {parsed['cpu'][0]['instructions']}")
    print(f"    - CPU 0 Execution Cycles: {parsed['cpu'][0]['cycles']}")
    print(f"    - Branch Accuracy: {parsed['branch'].get(0, {}).get('accuracy_pct')}%")
    print(f"    - Branch MPKI: {parsed['branch'].get(0, {}).get('mpki')}")
    print(f"    - LLC Miss Rate: {parsed['cache'].get('LLC', {}).get('miss_rate') * 100:.2f}%")
    print(f"    - Elapsed execution time: {parsed['execution_metadata']['elapsed_seconds']}s")

    # Sanity checks
    assert parsed["header"]["llc_sets"] == 2048, "LLC sets mismatch"
    assert parsed["header"]["llc_ways"] == 16, "LLC ways mismatch"
    assert parsed["cpu"][0]["ipc"] > 0, "IPC must be > 0"
    assert parsed["cpu"][0]["cycles"] > 0, "Cycles must be > 0"

    print("[+] ALL SMOKE TEST ASSERTIONS PASSED!")


if __name__ == "__main__":
    main()
