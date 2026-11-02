import csv
import matplotlib.pyplot as plt
import numpy as np
import os

def main():
    if not os.path.exists("summary_stats.csv"):
        print("summary_stats.csv not found")
        return
        
    with open("summary_stats.csv", "r") as f:
        reader = csv.DictReader(f)
        data = list(reader)
        
    traces = sorted(list(set([row['Trace'] for row in data])))
    sizes = sorted(list(set([int(row['Size'].replace('MB', '')) for row in data])))
    policies = ["lru", "mru", "random", "adaptive_hcit"]
    
    metrics = [
        {'key': 'IPC', 'name': 'IPC Comparison', 'ylabel': 'Instructions Per Cycle (IPC)'},
        {'key': 'LLC_MPKI', 'name': 'MPKI Comparison', 'ylabel': 'Misses Per Kilo-Instruction (MPKI)'},
        {'key': 'LLC_Miss_Rate', 'name': 'LLC Miss Rate', 'ylabel': 'LLC Miss Rate'},
        {'key': 'LLC_Hit_Rate', 'name': 'LLC Hit Rate', 'ylabel': 'LLC Hit Rate'},
        {'key': 'LLC_Writes', 'name': 'Total LLC Writes', 'ylabel': 'Total Writes'},
        {'key': 'Cycles', 'name': 'Execution Time', 'ylabel': 'Cycles'}
    ]
    
    os.makedirs("graphs", exist_ok=True)
    
    def find_val(trace, size, policy, metric_key):
        for r in data:
            if r['Trace'] == trace and int(r['Size'].replace('MB', '')) == size and r['Policy'] == policy and int(r['Ways'].replace('way', '')) == 16:
                return float(r[metric_key])
        return 0.0
        
    for metric in metrics:
        for trace in traces:
            plt.figure(figsize=(10, 6))
            x = np.arange(len(sizes))
            width = 0.2
            
            for i, policy in enumerate(policies):
                y = [find_val(trace, size, policy, metric['key']) for size in sizes]
                plt.bar(x + (i - 1.5) * width, y, width, label=policy.upper())
                
            plt.xlabel('Cache Size (MB)')
            plt.ylabel(metric['ylabel'])
            plt.title(f"{metric['name']} - {trace} (16-way)")
            plt.xticks(x, [f"{s}MB" for s in sizes])
            plt.legend()
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            
            safe_trace = trace.replace('.champsimtrace.xz', '')
            filename = f"graphs/{metric['key']}_{safe_trace}.png"
            plt.savefig(filename, bbox_inches='tight')
            plt.close()
            print(f"Generated {filename}")

if __name__ == "__main__":
    main()
