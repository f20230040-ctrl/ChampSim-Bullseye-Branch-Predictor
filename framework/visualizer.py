"""
Automated visualization suite for generating publication-quality plots
from ChampSim benchmark suite summaries.
"""

import csv
import os
import matplotlib.pyplot as plt
import numpy as np


def generate_branch_plots(csv_path: str, output_dir: str):
    """Generates comparison bar charts for the branch prediction suite."""
    if not os.path.exists(csv_path):
        print(f"[-] CSV not found: {csv_path}")
        return

    with open(csv_path, "r", encoding="utf-8") as f:
        data = list(csv.DictReader(f))

    os.makedirs(output_dir, exist_ok=True)

    traces = sorted(list(set(row["trace"] for row in data)))
    predictors = ["bimodal", "gshare", "hashed_perceptron", "bullseye", "adaptive_bullseye"]
    pred_labels = ["Bimodal", "Gshare", "Hashed Perceptron (Base)", "Bullseye", "Adaptive Bullseye"]
    colors = ["#7f7f7f", "#1f77b4", "#2ca02c", "#ff7f0e", "#d62728"]

    def get_val(trace, pred, key):
        for r in data:
            if r["trace"] == trace and r["predictor"] == pred:
                return float(r[key])
        return 0.0

    metrics = [
        {"key": "accuracy_pct", "name": "Branch Prediction Accuracy", "ylabel": "Accuracy (%)", "filename": "branch_accuracy_comparison.png", "ylim": (85, 100.5)},
        {"key": "mpki", "name": "Branch Misses Per Kilo-Instruction (MPKI)", "ylabel": "MPKI (lower is better)", "filename": "branch_mpki_comparison.png", "ylim": None},
        {"key": "ipc", "name": "CPU Instructions Per Cycle (IPC)", "ylabel": "IPC (higher is better)", "filename": "branch_ipc_comparison.png", "ylim": None},
    ]

    for m in metrics:
        fig, ax = plt.subplots(figsize=(12, 6))
        x = np.arange(len(traces))
        width = 0.16

        for i, (pred, label, color) in enumerate(zip(predictors, pred_labels, colors)):
            y = [get_val(t, pred, m["key"]) for t in traces]
            rects = ax.bar(x + (i - 2) * width, y, width, label=label, color=color, edgecolor="black", linewidth=0.5)

        ax.set_xlabel("Benchmark Trace", fontsize=11, fontweight="bold")
        ax.set_ylabel(m["ylabel"], fontsize=11, fontweight="bold")
        ax.set_title(f"{m['name']} Across SPEC CPU Workloads", fontsize=13, fontweight="bold", pad=12)
        ax.set_xticks(x)
        clean_traces = [t.replace(".champsimtrace.xz", "") for t in traces]
        ax.set_xticklabels(clean_traces, fontsize=10)
        if m["ylim"]:
            ax.set_ylim(m["ylim"])
        ax.legend(frameon=True, fontsize=10, loc="lower right" if m["key"] == "accuracy_pct" else "upper right")
        ax.grid(axis="y", linestyle="--", alpha=0.6)

        plt.tight_layout()
        save_path = os.path.join(output_dir, m["filename"])
        plt.savefig(save_path, dpi=300)
        plt.close()
        print(f"[+] Saved figure: {save_path}")


def generate_cache_plots(csv_path: str, output_dir: str):
    """Generates comparison plots for the cache replacement suite."""
    if not os.path.exists(csv_path):
        print(f"[-] CSV not found: {csv_path}")
        return

    with open(csv_path, "r", encoding="utf-8") as f:
        data = list(csv.DictReader(f))

    os.makedirs(output_dir, exist_ok=True)

    traces = sorted(list(set(row["trace"] for row in data)))
    policies = ["lru", "mru", "random", "adaptive_hcit"]
    policy_labels = ["LRU (Base)", "MRU", "Random", "Adaptive HCIT"]
    colors = {"lru": "#1f77b4", "mru": "#d62728", "random": "#9467bd", "adaptive_hcit": "#2ca02c"}

    # 1. Capacity scaling (1MB, 2MB, 4MB, 8MB 16-way)
    capacities = [1, 2, 4, 8]
    for trace in traces:
        clean_trace = trace.replace(".champsimtrace.xz", "")

        fig, (ax_ipc, ax_hit) = plt.subplots(1, 2, figsize=(14, 5))

        for pol in policies:
            y_ipc = []
            y_hit = []
            for cap in capacities:
                row_match = None
                for r in data:
                    if r["trace"] == trace and r["policy"] == pol and float(r["capacity_mb"]) == cap and int(r["ways"]) == 16:
                        row_match = r
                        break
                if row_match:
                    y_ipc.append(float(row_match["ipc"]))
                    y_hit.append(float(row_match["llc_hit_rate"]) * 100)
                else:
                    y_ipc.append(0.0)
                    y_hit.append(0.0)

            ax_ipc.plot(capacities, y_ipc, marker="o", label=pol.upper(), color=colors[pol], linewidth=2)
            ax_hit.plot(capacities, y_hit, marker="s", label=pol.upper(), color=colors[pol], linewidth=2)

        ax_ipc.set_title(f"IPC vs LLC Capacity - {clean_trace}", fontsize=11, fontweight="bold")
        ax_ipc.set_xlabel("LLC Capacity (MB, 16-way)", fontsize=10)
        ax_ipc.set_ylabel("IPC", fontsize=10)
        ax_ipc.set_xticks(capacities)
        ax_ipc.grid(True, linestyle="--", alpha=0.5)
        ax_ipc.legend()

        ax_hit.set_title(f"LLC Hit Rate (%) vs LLC Capacity - {clean_trace}", fontsize=11, fontweight="bold")
        ax_hit.set_xlabel("LLC Capacity (MB, 16-way)", fontsize=10)
        ax_hit.set_ylabel("Hit Rate (%)", fontsize=10)
        ax_hit.set_xticks(capacities)
        ax_hit.grid(True, linestyle="--", alpha=0.5)
        ax_hit.legend()

        plt.tight_layout()
        save_path = os.path.join(output_dir, f"capacity_scaling_{clean_trace}.png")
        plt.savefig(save_path, dpi=300)
        plt.close()
        print(f"[+] Saved figure: {save_path}")

    # 2. Associativity comparison: 2MB 16-way vs 2MB 8-way (Corrected!) vs 1MB 8-way (Legacy)
    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(traces))
    width = 0.22

    # Plotting Adaptive HCIT vs LRU delta on 2MB 16-way vs 2MB 8-way
    def get_ipc(trace, pol, cap, ways):
        for r in data:
            if r["trace"] == trace and r["policy"] == pol and float(r["capacity_mb"]) == cap and int(r["ways"]) == ways:
                return float(r["ipc"])
        return 0.0

    deltas_16way = []
    deltas_8way_corrected = []
    deltas_8way_legacy = []

    for t in traces:
        lru_16 = get_ipc(t, "lru", 2, 16)
        hcit_16 = get_ipc(t, "adaptive_hcit", 2, 16)
        d_16 = ((hcit_16 - lru_16) / lru_16 * 100) if lru_16 > 0 else 0

        lru_8c = get_ipc(t, "lru", 2, 8)
        hcit_8c = get_ipc(t, "adaptive_hcit", 2, 8)
        d_8c = ((hcit_8c - lru_8c) / lru_8c * 100) if lru_8c > 0 else 0

        lru_8l = get_ipc(t, "lru", 1, 8)
        hcit_8l = get_ipc(t, "adaptive_hcit", 1, 8)
        d_8l = ((hcit_8l - lru_8l) / lru_8l * 100) if lru_8l > 0 else 0

        deltas_16way.append(d_16)
        deltas_8way_corrected.append(d_8c)
        deltas_8way_legacy.append(d_8l)

    ax.bar(x - width, deltas_16way, width, label="2MB 16-way (2048 sets)", color="#1f77b4", edgecolor="black")
    ax.bar(x, deltas_8way_corrected, width, label="2MB 8-way Corrected (4096 sets)", color="#2ca02c", edgecolor="black")
    ax.bar(x + width, deltas_8way_legacy, width, label="1MB 8-way Legacy (2048 sets)", color="#ff7f0e", edgecolor="black")

    ax.axhline(0, color="black", linestyle="-", linewidth=0.8)
    ax.set_ylabel("Adaptive HCIT Speedup over LRU (%)", fontsize=11, fontweight="bold")
    ax.set_title("Adaptive HCIT Relative Performance Across Associativity & Capacity Configurations", fontsize=12, fontweight="bold", pad=12)
    ax.set_xticks(x)
    clean_traces = [t.replace(".champsimtrace.xz", "") for t in traces]
    ax.set_xticklabels(clean_traces, fontsize=10)
    ax.legend(frameon=True, fontsize=10)
    ax.grid(axis="y", linestyle="--", alpha=0.6)

    plt.tight_layout()
    save_path = os.path.join(output_dir, "associativity_sensitivity.png")
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f"[+] Saved figure: {save_path}")
