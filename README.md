# ChampSim Bullseye Branch Predictor

## Overview

This repository contains my implementation of the **Bullseye Branch Predictor** and an **Adaptive Bullseye Branch Predictor** in the ChampSim simulator for the Computer Architecture assignment.

The objective of this project is to improve branch prediction accuracy by identifying Hard-to-Predict (H2P) branches and assigning dedicated prediction resources to them while allowing easy branches to continue using the baseline predictor.

---

# Implemented Predictors

## 1. Bullseye Predictor

The Bullseye predictor extends the existing Hashed Perceptron predictor by introducing:

- Hard-to-Predict Identification Table (HIT)
- H2P Cache
- Local History Perceptron
- Global History Perceptron
- Confidence Arbiter
- Selective update filtering

The implementation is based on the paper:

> **Taming Wild Branches: Overcoming Hard-to-Predict Branches using the Bullseye Predictor**

with necessary adaptations for this version of ChampSim.

---

## 2. Adaptive Bullseye Predictor

The Adaptive Bullseye predictor further improves the Bullseye design by replacing fixed confidence thresholds with adaptive thresholds that automatically adjust according to recent prediction accuracy.

Adaptive features include:

- Adaptive confidence threshold
- Adaptive HIT admission threshold
- Dynamic confidence arbitration
- Automatic tuning based on recent prediction performance

---

# Modifications Made

The following files were added to the simulator:

```
branch/bullseye.bpred
branch/adaptive_bullseye.bpred
```

These files implement the complete Bullseye and Adaptive Bullseye branch predictors.

No unrelated simulator components were modified.

---

# Changes Made in the Simulator

The following functionality was added:

- Bullseye prediction pipeline
- Hard-to-Predict (H2P) branch detection
- H2P cache management
- Local-history perceptron
- Global-history perceptron
- Confidence arbiter
- Selective baseline predictor updates
- Adaptive confidence mechanism
- Adaptive admission thresholds

These changes are fully integrated into ChampSim's branch prediction framework.

---

# Build Instructions

Build Bullseye:

```bash
./build_champsim.sh bullseye no no no no lru 1
```

Build Adaptive Bullseye:

```bash
./build_champsim.sh adaptive_bullseye no no no no lru 1
```

---

# Running Simulations

Example:

```bash
./run_champsim.sh bullseye-no-no-no-no-lru-1core 1 10 401.bzip2-277B.champsimtrace.xz
```

Adaptive version:

```bash
./run_champsim.sh adaptive_bullseye-no-no-no-no-lru-1core 1 10 401.bzip2-277B.champsimtrace.xz
```

---

# Experimental Results

Experiments were performed on the benchmark traces specified in the assignment.

Metrics collected include:

- Branch Prediction Accuracy
- MPKI
- Cache Miss Latency
- Execution Time

Both single-core and four-core experiments were completed.

Results are available in:

```
results_10M/
results_4core_10M/
```

Summary tables are available in:

```
accuracy_1core.txt
accuracy_4core.txt
mpki_1core.txt
mpki_4core.txt
time_1core.txt
time_4core.txt
comparison_table.md
```

---

# Repository Structure

```
branch/
src/
inc/
prefetcher/
replacement/
scripts/

results_10M/
results_4core_10M/

README.md
```

---

## References

1. A. Seznec et al., *Taming Wild Branches: Overcoming Hard-to-Predict Branches using the Bullseye Predictor.*

2. ChampSim: A Trace-Based Microarchitecture Simulator.

---

# Author

## Author

**Sai Tejas Andey**  
Student ID: F20230040  
BITS Pilani
