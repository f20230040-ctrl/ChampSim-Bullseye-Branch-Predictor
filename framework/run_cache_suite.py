import os
import sys

workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

from framework.experiment_suite import run_cache_replacement_suite

if __name__ == "__main__":
    print("[*] Launching Cache Replacement Benchmark Suite...")
    run_cache_replacement_suite(workspace_root, n_warm=1_000_000, n_sim=10_000_000)
