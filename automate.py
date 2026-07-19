import os
import subprocess
import time

policies = ["lru", "mru", "random", "adaptive_hcit"]
sizes_mb = [1, 2, 4, 8]
traces_1c = ["401.bzip2-38B.champsimtrace.xz", "403.gcc-16B.champsimtrace.xz", "450.soplex-92B.champsimtrace.xz", "482.sphinx3-1522B.champsimtrace.xz"]

def set_llc_config(sets, ways):
    cache_h_path = "inc/cache.h"
    with open(cache_h_path, "r") as f:
        lines = f.readlines()
    with open(cache_h_path, "w") as f:
        for line in lines:
            if line.startswith("#define LLC_SET"):
                f.write(f"#define LLC_SET NUM_CPUS*{sets}\n")
            elif line.startswith("#define LLC_WAY"):
                f.write(f"#define LLC_WAY {ways}\n")
            else:
                f.write(line)
    
    # Force a clean build whenever cache configuration changes to prevent ODR violations
    subprocess.run(["make", "clean"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def build(pol, cores):
    print(f"Building {pol} for {cores} cores...")
    binary = f"bimodal-no-no-no-no-{pol}-{cores}core"
    for attempt in range(3):
        # Clean build required before changing policy or if size changed
        subprocess.run(["make", "clean"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        res = subprocess.run(["bash", "build_champsim.sh", "bimodal", "no", "no", "no", "no", pol, str(cores)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(f"bin/{binary}") and res.returncode == 0:
            return binary
        print(f"Build failed for {pol}, retrying...")
        time.sleep(2)
    raise Exception(f"Failed to build {pol} after 3 attempts")

procs = []
def run_exp(binary, cores, mb, ways, trace_args):
    global procs
    os.makedirs("results_10M", exist_ok=True)
    os.makedirs("results_4core_10M", exist_ok=True)
    
    trace_paths = [f"dpc3_traces/{t}" for t in trace_args]
    
    if cores == 1:
        out_file = f"results_10M/{trace_args[0]}-{binary}-{mb}MB-{ways}way.txt"
        cmd = [f"./bin/{binary}", "-warmup_instructions", "1000000", "-simulation_instructions", "10000000", "-traces"] + trace_paths
    else:
        out_file = f"results_4core_10M/mix-{binary}-{mb}MB-{ways}way.txt"
        cmd = [f"./bin/{binary}", "-warmup_instructions", "1000000", "-simulation_instructions", "10000000", "-traces"] + trace_paths
    
    if os.path.exists(out_file) and os.path.getsize(out_file) > 1000:
        print(f"Skipping {out_file}, already exists.")
        return
        
    print(f"Running {binary} on {cores} cores with size {mb}MB {ways}way...")
    f = open(out_file, "w")
    p = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT)
    procs.append((p, f))
    
    # Bound concurrency (running up to 4 parallel jobs to avoid overloading)
    if len(procs) >= 4:
        for p, f in procs:
            p.wait()
            f.close()
        procs = []

def main():
    mc_mix = ["401.bzip2-38B.champsimtrace.xz", "403.gcc-16B.champsimtrace.xz", "450.soplex-92B.champsimtrace.xz", "482.sphinx3-1522B.champsimtrace.xz"]
    
    # Original LLC Configs (16-way, variable sizes)
    for mb in sizes_mb:
        sets = mb * 1024
        set_llc_config(sets, 16)
        
        # Single-core
        for pol in policies:
            binary = build(pol, 1)
            for tr in traces_1c:
                run_exp(binary, 1, mb, 16, [tr])
        
        # Multi-core
        for pol in policies:
            binary = build(pol, 4)
            run_exp(binary, 4, mb, 16, mc_mix)
            
    # Task 2(b): 8-way, subset of experiments (2MB)
    set_llc_config(2048, 8)
    for pol in policies:
        binary = build(pol, 1)
        for tr in traces_1c:
            run_exp(binary, 1, 2, 8, [tr])
            
    global procs
    for p, f in procs:
        p.wait()
        f.close()

if __name__ == "__main__":
    main()

