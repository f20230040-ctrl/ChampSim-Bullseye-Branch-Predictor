#!/bin/bash

# Parse output files and generate a markdown table

OUTPUT_FILE="comparison_table.md"

echo "| Trace | Predictor | MPKI | Accuracy | Prediction Latency (cycles) | Execution Time (cycles) |" > $OUTPUT_FILE
echo "|---|---|---|---|---|---|" >> $OUTPUT_FILE

TRACES=("401.bzip2-277B.champsimtrace.xz" "403.gcc-16B.champsimtrace.xz" "434.zeusmp-10B.champsimtrace.xz" "450.soplex-92B.champsimtrace.xz")
PREDICTORS=("hashed_perceptron" "bullseye" "adaptive_bullseye")

for trace in "${TRACES[@]}"; do
    for pred in "${PREDICTORS[@]}"; do
        file="results_10M/${trace}-${pred}-no-no-no-no-lru-1core.txt"
        
        mpki="N/A"
        acc="N/A"
        exec_cycles="N/A"
        latency="1"
        
        if [ -f "$file" ]; then
            # CPU 0 Branch Prediction Accuracy: 98.3304% MPKI: 2.6127 Average ROB Occupancy at Mispredict: 127.492
            mpki=$(grep "MPKI:" "$file" | awk '{for(i=1;i<=NF;i++) if($i=="MPKI:") print $(i+1)}')
            acc=$(grep "Accuracy:" "$file" | awk '{for(i=1;i<=NF;i++) if($i=="Accuracy:") print $(i+1)}')
            # CPU 0 cumulative IPC: 0.939221 instructions: 10000000 cycles: 10647122
            exec_cycles=$(grep "CPU 0 cumulative IPC:" "$file" | awk '{for(i=1;i<=NF;i++) if($i=="cycles:") print $(i+1)}')
        fi
        
        echo "| ${trace} | ${pred} | ${mpki} | ${acc} | ${latency} | ${exec_cycles} |" >> $OUTPUT_FILE
    done
done

echo "Generated $OUTPUT_FILE"
