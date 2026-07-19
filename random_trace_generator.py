import random

# List of 15 traces from the assignment
traces = [
    "401.bzip2-277B.champsimtrace.xz",
    "403.gcc-16B.champsimtrace.xz",
    "434.zeusmp-10B.champsimtrace.xz",
    "437.leslie3d-273B.champsimtrace.xz",
    "450.soplex-92B.champsimtrace.xz",
    "456.hmmer-327B.champsimtrace.xz",
    "462.libquantum-1343B.champsimtrace.xz",
    "482.sphinx3-1522B.champsimtrace.xz",
    "605.mcf_s-1644B.champsimtrace.xz",
    "605.mcf_s-665B.champsimtrace.xz",
    "619.lbm_s-3766B.champsimtrace.xz",
    "620.omnetpp_s-874B.champsimtrace.xz",
    "621.wrf_s-8100B.champsimtrace.xz",
    "623.xalancbmk_s-700B.champsimtrace.xz",
    "628.pop2_s-17B.champsimtrace.xz"
]

selected_traces = random.sample(traces, 4)

print("Selected Traces:")
for i, trace in enumerate(selected_traces):
    print(f"Trace {i}: {trace}")

print("\nChampSim command to run 4-core multi-core simulation:")
# Command syntax from README: ./run_4core.sh [BINARY] [N_WARM] [N_SIM] [N_MIX] [TRACE0] [TRACE1] [TRACE2] [TRACE3] [OPTION]
binary = "adaptive_bullseye-no-no-no-no-lru-4core"
command = f"./run_4core.sh {binary} 1 10 0 " + " ".join(selected_traces)

print(command)
