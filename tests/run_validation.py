import os
import sys

workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

from framework.experiment_suite import run_validation_check

if __name__ == "__main__":
    run_validation_check(workspace_root)
