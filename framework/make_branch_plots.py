import os
import sys

workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

from framework.visualizer import generate_branch_plots

if __name__ == "__main__":
    csv_file = os.path.join(workspace_root, "results", "branch_suite_summary.csv")
    out_dir = os.path.join(workspace_root, "results", "figures", "branch")
    generate_branch_plots(csv_file, out_dir)
