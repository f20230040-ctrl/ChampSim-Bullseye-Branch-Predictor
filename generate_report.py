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
        
    traces = list(set([row['Trace'] for row in data]))
    sizes = sorted(list(set([int(row['Size'].replace('MB', '')) for row in data])))
    policies = ["lru", "mru", "random", "adaptive_hcit"]
    
    md_lines = []
    md_lines.append("# ChampSim Experimental Results (Extended)")
    md_lines.append("")
    
    def find_row(trace, size, policy, ways=16):
        for r in data:
            if r['Trace'] == trace and int(r['Size'].replace('MB', '')) == size and r['Policy'] == policy and int(r['Ways'].replace('way', '')) == ways:
                return r
        return None
        
    def add_table(title, metric_key, is_percent=False, invert_imprv=False):
        md_lines.append(f"## {title} (16-way)")
        md_lines.append("| Trace | Size (MB) | LRU | MRU | Random | Adaptive HCIT | Imprv. over LRU (HCIT) |")
        md_lines.append("|-------|-----------|-----|-----|--------|---------------|------------------------|")
        
        for trace in sorted(traces):
            for size in sizes:
                lru_r = find_row(trace, size, "lru")
                if not lru_r: continue
                mru_r = find_row(trace, size, "mru")
                rand_r = find_row(trace, size, "random")
                hcit_r = find_row(trace, size, "adaptive_hcit")
                
                lru_v = float(lru_r[metric_key])
                mru_v = float(mru_r[metric_key]) if mru_r else 0.0
                rand_v = float(rand_r[metric_key]) if rand_r else 0.0
                hcit_v = float(hcit_r[metric_key]) if hcit_r else 0.0
                
                if invert_imprv:
                    imprv = ((lru_v - hcit_v) / lru_v * 100.0) if lru_v > 0 else 0.0
                else:
                    imprv = ((hcit_v - lru_v) / lru_v * 100.0) if lru_v > 0 else 0.0
                    
                if is_percent:
                    md_lines.append(f"| {trace} | {size} | {lru_v*100:.2f}% | {mru_v*100:.2f}% | {rand_v*100:.2f}% | {hcit_v*100:.2f}% | {imprv:+.2f}% |")
                else:
                    # For integers like Cycles or Writes
                    if lru_v > 1000:
                        md_lines.append(f"| {trace} | {size} | {int(lru_v)} | {int(mru_v)} | {int(rand_v)} | {int(hcit_v)} | {imprv:+.2f}% |")
                    else:
                        md_lines.append(f"| {trace} | {size} | {lru_v:.4f} | {mru_v:.4f} | {rand_v:.4f} | {hcit_v:.4f} | {imprv:+.2f}% |")
        md_lines.append("")
        
    add_table("IPC Comparison", "IPC", False, False)
    add_table("L1 Miss Rate", "L1_Miss_Rate", True, True)
    add_table("L2 Miss Rate", "L2_Miss_Rate", True, True)
    add_table("L3 (LLC) Miss Rate", "LLC_Miss_Rate", True, True)
    add_table("LLC Hit Rate", "LLC_Hit_Rate", True, False)
    add_table("Total LLC Writes", "LLC_Writes", False, True)
    add_table("Execution Time (Cycles)", "Cycles", False, True)

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
            .section { margin-bottom: 50px; }
        </style>
    </head>
    <body>
        <h1 style="text-align: center;">ChampSim Experimental Results</h1>
        <div id="charts"></div>
        
        <script>
            const data = DATA_PLACEHOLDER;
            const traces = TRACES_PLACEHOLDER;
            const sizes = SIZES_PLACEHOLDER;
            const policies = ['lru', 'mru', 'random', 'adaptive_hcit'];
            
            const metrics = [
                { key: 'IPC', name: 'IPC' },
                { key: 'LLC_Miss_Rate', name: 'LLC Miss Rate' },
                { key: 'LLC_Hit_Rate', name: 'LLC Hit Rate' },
                { key: 'LLC_Writes', name: 'Total LLC Writes' },
                { key: 'Cycles', name: 'Execution Time (Cycles)' }
            ];
            
            const container = document.getElementById('charts');
            
            metrics.forEach(metric => {
                const sec = document.createElement('div');
                sec.className = 'section';
                sec.innerHTML = `<h2 style="text-align: center;">${metric.name} Comparison</h2>`;
                container.appendChild(sec);
                
                traces.forEach(trace => {
                    const wrapper = document.createElement('div');
                    wrapper.className = 'chart-container';
                    const canvas = document.createElement('canvas');
                    wrapper.appendChild(canvas);
                    sec.appendChild(wrapper);
                    
                    const datasets = policies.map(pol => {
                        return {
                            label: pol.toUpperCase(),
                            data: sizes.map(sz => {
                                const row = data.find(r => r.Trace === trace && parseInt(r.Size) === sz && r.Policy === pol && parseInt(r.Ways) === 16);
                                return row ? parseFloat(row[metric.key]) : 0;
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
                                title: { display: true, text: `${metric.name} - ${trace}` }
                            }
                        }
                    });
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
