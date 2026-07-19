import os
import glob
import csv

def parse_file(filepath):
    data = {}
    with open(filepath, "r") as f:
        lines = f.readlines()
        
        # For multi-core, there are multiple CPUs. We will sum up accesses or just take CPU 0 IPC for simplicity?
        # Actually for multi-core, ChampSim prints "CPU 0 cumulative IPC", "CPU 1 cumulative IPC", etc.
        # And it prints "LLC TOTAL ACCESS" for the shared cache.
        # Let's collect total IPC across all cores
        total_ipc = 0
        total_cycles = 0
        cpu_count = 0
        for i, line in enumerate(lines):
            if "cumulative IPC:" in line and "CPU" in line:
                parts = line.split()
                try:
                    idx = parts.index("IPC:")
                    total_ipc += float(parts[idx+1])
                    idx2 = parts.index("cycles:")
                    total_cycles = max(total_cycles, int(parts[idx2+1]))
                    cpu_count += 1
                except ValueError:
                    pass
            if "L1D TOTAL" in line:
                parts = line.split()
                hits = int(parts[5])
                misses = int(parts[7])
                data['L1_Miss_Rate'] = misses / (hits + misses) if (hits + misses) > 0 else 0
            if "L2C TOTAL" in line:
                parts = line.split()
                hits = int(parts[5])
                misses = int(parts[7])
                data['L2_Miss_Rate'] = misses / (hits + misses) if (hits + misses) > 0 else 0
            if "LLC TOTAL" in line:
                parts = line.split()
                hits = int(parts[5])
                misses = int(parts[7])
                data['LLC_Miss_Rate'] = misses / (hits + misses) if (hits + misses) > 0 else 0
                data['LLC_Hit_Rate'] = hits / (hits + misses) if (hits + misses) > 0 else 0
                data['LLC_MPKI'] = misses / 10000.0  # 10M instructions per core
            if "LLC WRITEBACK" in line:
                parts = line.split()
                hits = int(parts[5])
                misses = int(parts[7])
                data['LLC_Writes'] = hits + misses
                
        if cpu_count > 0:
            data['IPC'] = total_ipc # cumulative IPC sum
            data['Cycles'] = total_cycles
    return data

def main():
    results = []
    # parse 1core
    for f in glob.glob("results_10M/*.txt"):
        base = os.path.basename(f).replace(".txt", "")
        parts = base.split("-bimodal-no-no-no-no-")
        if len(parts) == 2:
            trace = parts[0]
            rest = parts[1].split("-")
            if len(rest) >= 4:
                policy = rest[0]
                cores = rest[1]
                size = rest[2]
                ways = rest[3]
                stats = parse_file(f)
                stats['Trace'] = trace
                stats['Policy'] = policy
                stats['Cores'] = cores
                stats['Size'] = size
                stats['Ways'] = ways
                results.append(stats)
                
    # parse 4core
    for f in glob.glob("results_4core_10M/*.txt"):
        base = os.path.basename(f).replace(".txt", "")
        parts = base.split("-bimodal-no-no-no-no-")
        if len(parts) == 2:
            trace = parts[0]
            rest = parts[1].split("-")
            if len(rest) >= 4:
                policy = rest[0]
                cores = rest[1]
                size = rest[2]
                ways = rest[3]
                stats = parse_file(f)
                stats['Trace'] = trace
                stats['Policy'] = policy
                stats['Cores'] = cores
                stats['Size'] = size
                stats['Ways'] = ways
                results.append(stats)
                
    keys = ['Trace', 'Policy', 'Cores', 'Size', 'Ways', 'IPC', 'Cycles', 'L1_Miss_Rate', 'L2_Miss_Rate', 'LLC_Miss_Rate', 'LLC_Hit_Rate', 'LLC_MPKI', 'LLC_Writes']
    with open("summary_stats.csv", "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for r in results:
            row = {k: r.get(k, 0) for k in keys}
            writer.writerow(row)
            
    print("Generated summary_stats.csv")

if __name__ == "__main__":
    main()
