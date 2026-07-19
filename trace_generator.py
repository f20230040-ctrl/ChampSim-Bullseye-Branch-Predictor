import os
import random
import sys

def main():
    trace_dir = "dpc3_traces"
    if not os.path.exists(trace_dir):
        print(f"Error: {trace_dir} directory not found.")
        sys.exit(1)
        
    available_traces = []
    for f in os.listdir(trace_dir):
        if f.endswith(".xz"):
            available_traces.append(f)
            
    if len(available_traces) < 4:
        print(f"Error: Not enough traces found in {trace_dir}. Need at least 4, found {len(available_traces)}.")
        sys.exit(1)
        
    selected_traces = random.sample(available_traces, 4)
    
    binary_name = "<BINARY_NAME>"
    if len(sys.argv) > 1:
        binary_name = sys.argv[1]
        
    n_warm = 1
    n_sim = 10
    n_mix = 1
    
    command = f"./run_4core.sh {binary_name} {n_warm} {n_sim} {n_mix} {' '.join(selected_traces)}"
    
    print("Run the following command for a random 4-core simulation:")
    print(command)

if __name__ == "__main__":
    main()
