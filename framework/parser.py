"""
Robust parser for ChampSim simulation logs.
Extracts configuration metadata, branch predictor statistics, cache metrics,
and validates execution completeness.
"""

import re
from typing import Dict, Any, Optional


class ParseError(Exception):
    """Raised when log parsing fails or output is malformed."""
    pass


class IncompleteExecutionError(ParseError):
    """Raised when simulation output is truncated or did not finish cleanly."""
    pass


def parse_champsim_log(content_or_path: str, is_path: bool = False) -> Dict[str, Any]:
    """
    Parse a ChampSim output text log into a structured dictionary.
    Raises IncompleteExecutionError if 'ChampSim completed all CPUs' is missing.
    """
    if is_path:
        with open(content_or_path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
    else:
        text = content_or_path

    # Verify run completion
    if "ChampSim completed all CPUs" not in text:
        raise IncompleteExecutionError("Log is incomplete: 'ChampSim completed all CPUs' not found.")

    data: Dict[str, Any] = {
        "status": "COMPLETED",
        "header": {},
        "cpu": {},
        "cache": {},
        "branch": {},
    }

    # 1. Header Metadata
    m_warmup = re.search(r"Warmup Instructions:\s+(\d+)", text)
    if m_warmup:
        data["header"]["warmup_instructions"] = int(m_warmup.group(1))

    m_sim = re.search(r"Simulation Instructions:\s+(\d+)", text)
    if m_sim:
        data["header"]["simulation_instructions"] = int(m_sim.group(1))

    m_cpus = re.search(r"Number of CPUs:\s+(\d+)", text)
    if m_cpus:
        data["header"]["num_cpus"] = int(m_cpus.group(1))

    m_llc_sets = re.search(r"LLC sets:\s+(\d+)", text)
    if m_llc_sets:
        data["header"]["llc_sets"] = int(m_llc_sets.group(1))

    m_llc_ways = re.search(r"LLC ways:\s+(\d+)", text)
    if m_llc_ways:
        data["header"]["llc_ways"] = int(m_llc_ways.group(1))

    traces = re.findall(r"CPU\s+(\d+)\s+runs\s+(.+)", text)
    data["header"]["traces"] = {int(cpu): path.strip() for cpu, path in traces}

    # 2. CPU IPC and Execution Cycles
    # Pattern: "CPU 0 cumulative IPC: 0.694392 instructions: 10000000 cycles: 14401078"
    cpu_ipc_matches = re.findall(
        r"CPU\s+(\d+)\s+cumulative IPC:\s+([\d\.]+)\s+instructions:\s+(\d+)\s+cycles:\s+(\d+)",
        text
    )
    total_ipc = 0.0
    max_cycles = 0
    for cpu_id_str, ipc_str, instrs_str, cycles_str in cpu_ipc_matches:
        c_id = int(cpu_id_str)
        ipc = float(ipc_str)
        instrs = int(instrs_str)
        cycles = int(cycles_str)
        data["cpu"][c_id] = {
            "ipc": ipc,
            "instructions": instrs,
            "cycles": cycles,
        }
        total_ipc += ipc
        if cycles > max_cycles:
            max_cycles = cycles

    data["cpu"]["cumulative_ipc"] = total_ipc
    data["cpu"]["max_cycles"] = max_cycles

    # 3. Branch Prediction Statistics
    # Pattern: "CPU 0 Branch Prediction Accuracy: 98.9243% MPKI: 1.0032 Average ROB Occupancy at Mispredict: 161.886"
    bp_matches = re.findall(
        r"CPU\s+(\d+)\s+Branch Prediction Accuracy:\s+([\d\.]+)%\s+MPKI:\s+([\d\.]+)\s+Average ROB Occupancy at Mispredict:\s+([\d\.]+)",
        text
    )
    for cpu_id_str, acc_str, mpki_str, rob_str in bp_matches:
        c_id = int(cpu_id_str)
        data["branch"][c_id] = {
            "accuracy_pct": float(acc_str),
            "mpki": float(mpki_str),
            "rob_occupancy_at_mispredict": float(rob_str),
        }

    # 4. Cache Statistics (L1D, L1I, L2C, LLC)
    cache_levels = ["L1D", "L1I", "L2C", "LLC"]
    for level in cache_levels:
        m_tot = re.search(
            rf"{level}\s+TOTAL\s+ACCESS:\s+(\d+)\s+HIT:\s+(\d+)\s+MISS:\s+(\d+)",
            text
        )
        if m_tot:
            accesses = int(m_tot.group(1))
            hits = int(m_tot.group(2))
            misses = int(m_tot.group(3))
            miss_rate = (misses / accesses) if accesses > 0 else 0.0
            hit_rate = (hits / accesses) if accesses > 0 else 0.0
            data["cache"][level] = {
                "access": accesses,
                "hit": hits,
                "miss": misses,
                "hit_rate": hit_rate,
                "miss_rate": miss_rate,
            }

    # LLC Writes / Writebacks
    m_wb = re.search(r"LLC WRITEBACK ACCESS:\s+(\d+)\s+HIT:\s+(\d+)\s+MISS:\s+(\d+)", text)
    if m_wb:
        wb_access = int(m_wb.group(1))
        wb_hit = int(m_wb.group(2))
        wb_miss = int(m_wb.group(3))
        data["cache"]["LLC_WRITEBACK"] = {
            "access": wb_access,
            "hit": wb_hit,
            "miss": wb_miss,
            "total_writes": wb_hit + wb_miss,
        }

    return data
