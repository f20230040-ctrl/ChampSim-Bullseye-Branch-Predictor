"""
Simulation execution runner.
Executes ChampSim simulations, records configuration metadata, verifies completion,
and writes structured outputs.
"""

import json
import os
import subprocess
import time
from typing import Dict, Any, List, Optional
from framework.parser import parse_champsim_log, IncompleteExecutionError


WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _sanitize_path(path_str: str) -> str:
    """Normalizes paths to repo-relative paths for portable metadata."""
    if not path_str:
        return path_str
    norm = path_str.replace("\\", "/")
    # Derive possible root prefixes dynamically
    root_norm = WORKSPACE_ROOT.replace("\\", "/")
    cwd_norm = os.getcwd().replace("\\", "/")
    for prefix in [root_norm, cwd_norm]:
        if norm.startswith(prefix):
            rel = norm[len(prefix):].lstrip("/")
            return "./" + rel if rel else "."
    return path_str


class RunError(Exception):
    """Raised when simulation execution fails."""
    pass


def run_simulation(
    binary_path: str,
    trace_paths: List[str],
    output_log_path: str,
    warmup_instructions: int = 1_000_000,
    simulation_instructions: int = 10_000_000,
    timeout_seconds: Optional[int] = None,
    extra_options: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Executes a ChampSim simulation run and parses output upon completion.
    Writes both the raw stdout/stderr text log and a companion .json file.
    """
    if not os.path.exists(binary_path):
        raise RunError(f"Binary not found: {binary_path}")

    for t in trace_paths:
        if not os.path.exists(t):
            raise RunError(f"Trace file not found: {t}")

    os.makedirs(os.path.dirname(os.path.abspath(output_log_path)), exist_ok=True)

    cmd = [
        binary_path,
        "-warmup_instructions", str(warmup_instructions),
        "-simulation_instructions", str(simulation_instructions),
    ]
    if extra_options:
        cmd.extend(extra_options.split())
    cmd.append("-traces")
    cmd.extend(trace_paths)

    start_time = time.time()
    try:
        with open(output_log_path, "w", encoding="utf-8") as out_file:
            proc = subprocess.run(
                cmd,
                stdout=out_file,
                stderr=subprocess.STDOUT,
                timeout=timeout_seconds,
                check=False,
            )
    except subprocess.TimeoutExpired:
        raise RunError(f"Simulation timed out after {timeout_seconds} seconds")

    elapsed_time = time.time() - start_time

    if proc.returncode != 0:
        raise RunError(
            f"Simulator exited with non-zero code {proc.returncode}. "
            f"See log at {output_log_path}"
        )

    # Parse and validate completion
    parsed_data = parse_champsim_log(output_log_path, is_path=True)
    
    # Store clean relative paths for portability across environments
    clean_cmd = [_sanitize_path(arg) for arg in cmd]

    # Sanitize trace paths in header if present
    if "header" in parsed_data and "traces" in parsed_data["header"]:
        for k, v in parsed_data["header"]["traces"].items():
            parsed_data["header"]["traces"][k] = _sanitize_path(v)

    parsed_data["execution_metadata"] = {
        "binary": os.path.basename(binary_path),
        "command": " ".join(clean_cmd),
        "warmup_instructions": warmup_instructions,
        "simulation_instructions": simulation_instructions,
        "elapsed_seconds": round(elapsed_time, 2),
        "output_log": _sanitize_path(output_log_path),
        "traces": [os.path.basename(t) for t in trace_paths],
    }

    # Write companion JSON
    json_path = output_log_path.rsplit(".", 1)[0] + ".json"
    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(parsed_data, jf, indent=2)

    return parsed_data
