import os
import subprocess
import glob
import re

predictors = ['hashed_perceptron', 'bullseye', 'adaptive_bullseye']
traces = [
    '401.bzip2-277B.champsimtrace.xz',
    '403.gcc-16B.champsimtrace.xz',
    '434.zeusmp-10B.champsimtrace.xz',
    '450.soplex-92B.champsimtrace.xz'
]

# 1. Build
print("Building predictors...")
for p in predictors:
    print(f"Building {p}...")
    subprocess.run(["bash", "./build_champsim.sh", p, "no", "no", "no", "no", "lru", "1"], check=True)

# 2. Run
print("Running simulations...")
procs = []
for p in predictors:
    binary = f"{p}-no-no-no-no-lru-1core"
    for t in traces:
        print(f"Starting {binary} on {t}...")
        proc = subprocess.Popen(["bash", "./run_champsim.sh", binary, "1", "10", t])
        procs.append(proc)

for proc in procs:
    proc.wait()

print("Simulations finished.")

# 3. Parse
print("Parsing results...")
results = {}

for p in predictors:
    binary = f"{p}-no-no-no-no-lru-1core"
    for t in traces:
        res_file = f"results_10M/{t}-{binary}-.txt"
        if not os.path.exists(res_file):
            print(f"File not found: {res_file}")
            continue
            
        with open(res_file, 'r') as f:
            content = f.read()
            
        mpki = "N/A"
        accuracy = "N/A"
        latency = "1 cycle (assumed)"
        exec_time = "N/A"
        
        m_mpki = re.search(r'MPKI:\s*([\d.]+)', content)
        if m_mpki: mpki = m_mpki.group(1)
            
        # Accuracy pattern might be: CPU 0 Branch Prediction Accuracy: 98.24% MPKI: 3.52
        # Let's use a generic percentage match for Accuracy if MPKI is nearby
        m_acc = re.search(r'Accuracy:\s*([\d.]+%)', content)
        if m_acc: accuracy = m_acc.group(1)
            
        m_exec = re.search(r'CPU 0 cumulative IPC:\s*([\d.]+)\s*instructions:\s*\d+\s*cycles:\s*(\d+)', content)
        if m_exec: exec_time = m_exec.group(2)
            
        results[(p, t)] = {
            'mpki': mpki,
            'accuracy': accuracy,
            'latency': latency,
            'exec_time': exec_time
        }

# 4. Generate Markdown Table
with open('comparison_table.md', 'w') as out:
    out.write("| Trace | Predictor | MPKI | Accuracy | Prediction Latency | Execution Time (cycles) |\n")
    out.write("|---|---|---|---|---|---|\n")
    for t in traces:
        for p in predictors:
            res = results.get((p, t), {'mpki':'N/A', 'accuracy':'N/A', 'latency':'N/A', 'exec_time':'N/A'})
            out.write(f"| {t} | {p} | {res['mpki']} | {res['accuracy']} | {res['latency']} | {res['exec_time']} |\n")

print("Done. Wrote comparison_table.md")
