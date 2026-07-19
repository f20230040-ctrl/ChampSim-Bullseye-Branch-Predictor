import csv
import json
import collections

def main():
    try:
        with open("summary_stats.csv", "r") as f:
            reader = csv.DictReader(f)
            data = list(reader)
    except FileNotFoundError:
        print("summary_stats.csv not found")
        return
        
    # Group by Trace and Size
    # Target: compare MRU, Random, Adaptive HCIT against LRU
    
    traces = list(set([row['Trace'] for row in data]))
    sizes = sorted(list(set([int(row['Size'].replace('MB', '')) for row in data])))
    policies = ["lru", "mru", "random", "adaptive_hcit"]
    
    # We want to output:
    # 1. IPC comparison table (1MB, 2MB, 4MB, 8MB)
    # 2. MPKI comparison table
    
    md_lines = []
    md_lines.append("# ChampSim Experimental Results")
    md_lines.append("")
    
    # Helper to find a specific row
    def find_row(trace, size, policy, ways=16):
        for r in data:
            if r['Trace'] == trace and int(r['Size'].replace('MB', '')) == size and r['Policy'] == policy and int(r['Ways'].replace('way', '')) == ways:
                return r
        return None
        
    md_lines.append("## IPC Comparison (16-way)")
    md_lines.append("| Trace | Size (MB) | LRU | MRU | Random | Adaptive HCIT | Imprv. over LRU (HCIT) |")
    md_lines.append("|-------|-----------|-----|-----|--------|---------------|------------------------|")
    
    for trace in sorted(traces):
        for size in sizes:
            lru_r = find_row(trace, size, "lru")
            if not lru_r: continue
            mru_r = find_row(trace, size, "mru")
            rand_r = find_row(trace, size, "random")
            hcit_r = find_row(trace, size, "adaptive_hcit")
            
            lru_ipc = float(lru_r['IPC'])
            mru_ipc = float(mru_r['IPC']) if mru_r else 0.0
            rand_ipc = float(rand_r['IPC']) if rand_r else 0.0
            hcit_ipc = float(hcit_r['IPC']) if hcit_r else 0.0
            
            imprv = ((hcit_ipc - lru_ipc) / lru_ipc * 100.0) if lru_ipc > 0 else 0.0
            
            md_lines.append(f"| {trace} | {size} | {lru_ipc:.4f} | {mru_ipc:.4f} | {rand_ipc:.4f} | {hcit_ipc:.4f} | {imprv:+.2f}% |")

    md_lines.append("")
    md_lines.append("## MPKI Comparison (16-way)")
    md_lines.append("| Trace | Size (MB) | LRU | MRU | Random | Adaptive HCIT | Imprv. over LRU (HCIT) |")
    md_lines.append("|-------|-----------|-----|-----|--------|---------------|------------------------|")
    
    for trace in sorted(traces):
        for size in sizes:
            lru_r = find_row(trace, size, "lru")
            if not lru_r: continue
            mru_r = find_row(trace, size, "mru")
            rand_r = find_row(trace, size, "random")
            hcit_r = find_row(trace, size, "adaptive_hcit")
            
            lru_mpki = float(lru_r['LLC_MPKI'])
            mru_mpki = float(mru_r['LLC_MPKI']) if mru_r else 0.0
            rand_mpki = float(rand_r['LLC_MPKI']) if rand_r else 0.0
            hcit_mpki = float(hcit_r['LLC_MPKI']) if hcit_r else 0.0
            
            imprv = ((lru_mpki - hcit_mpki) / lru_mpki * 100.0) if lru_mpki > 0 else 0.0
            
            md_lines.append(f"| {trace} | {size} | {lru_mpki:.4f} | {mru_mpki:.4f} | {rand_mpki:.4f} | {hcit_mpki:.4f} | {imprv:+.2f}% |")

    md_lines.append("")
    md_lines.append("## IPC Comparison (8-way)")
    md_lines.append("| Trace | Size (MB) | LRU | MRU | Random | Adaptive HCIT | Imprv. over LRU (HCIT) |")
    md_lines.append("|-------|-----------|-----|-----|--------|---------------|------------------------|")
    for trace in sorted(traces):
        lru_r = find_row(trace, 2, "lru", ways=8)
        if not lru_r: continue
        mru_r = find_row(trace, 2, "mru", ways=8)
        rand_r = find_row(trace, 2, "random", ways=8)
        hcit_r = find_row(trace, 2, "adaptive_hcit", ways=8)
        
        lru_ipc = float(lru_r['IPC'])
        mru_ipc = float(mru_r['IPC']) if mru_r else 0.0
        rand_ipc = float(rand_r['IPC']) if rand_r else 0.0
        hcit_ipc = float(hcit_r['IPC']) if hcit_r else 0.0
        imprv = ((hcit_ipc - lru_ipc) / lru_ipc * 100.0) if lru_ipc > 0 else 0.0
        md_lines.append(f"| {trace} | 2 | {lru_ipc:.4f} | {mru_ipc:.4f} | {rand_ipc:.4f} | {hcit_ipc:.4f} | {imprv:+.2f}% |")

    with open("results.md", "w") as f:
        f.write("\n".join(md_lines))
        
    # Generate HTML with Chart.js
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>ChampSim Results</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .chart-container { width: 800px; margin: 20px auto; }
        </style>
    </head>
    <body>
        <h1 style="text-align: center;">ChampSim Experimental Results (IPC)</h1>
        <div id="charts"></div>
        
        <script>
            const data = DATA_PLACEHOLDER;
            const traces = TRACES_PLACEHOLDER;
            const sizes = SIZES_PLACEHOLDER;
            const policies = ['lru', 'mru', 'random', 'adaptive_hcit'];
            
            const container = document.getElementById('charts');
            
            traces.forEach(trace => {
                const wrapper = document.createElement('div');
                wrapper.className = 'chart-container';
                const canvas = document.createElement('canvas');
                wrapper.appendChild(canvas);
                container.appendChild(wrapper);
                
                const datasets = policies.map(pol => {
                    return {
                        label: pol.toUpperCase(),
                        data: sizes.map(sz => {
                            const row = data.find(r => r.Trace === trace && parseInt(r.Size) === sz && r.Policy === pol && parseInt(r.Ways) === 16);
                            return row ? parseFloat(row.IPC) : 0;
                        }),
                        borderWidth: 2
                    };
                });
                
                new Chart(canvas, {
                    type: 'bar',
                    data: {
                        labels: sizes.map(s => s + 'MB'),
                        datasets: datasets
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            title: { display: true, text: 'IPC Comparison - ' + trace }
                        }
                    }
                });
            });
        </script>
    </body>
    </html>
    """
    
    html = html_template.replace("DATA_PLACEHOLDER", json.dumps(data))
    html = html.replace("TRACES_PLACEHOLDER", json.dumps(list(traces)))
    html = html.replace("SIZES_PLACEHOLDER", json.dumps(list(sizes)))
    
    with open("report.html", "w") as f:
        f.write(html)
        
    print("Generated results.md and report.html")

if __name__ == "__main__":
    main()
