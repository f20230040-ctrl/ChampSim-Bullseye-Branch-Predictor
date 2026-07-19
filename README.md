# ChampSim Bullseye Branch Predictor & Adaptive HCIT Replacement

## Overview

This repository contains my implementation of the **Bullseye Branch Predictor**, the **Adaptive Bullseye Branch Predictor**, and **Adaptive HCIT (Hard-to-Cache Instruction Tracker) LLC Replacement Policy** in the ChampSim simulator for the Computer Architecture assignment.

The objective of this project is to:
1. Improve branch prediction accuracy by identifying Hard-to-Predict (H2P) branches and assigning dedicated prediction resources to them.
2. Improve Last-Level Cache (LLC) performance by dynamically identifying dead-on-arrival vs. reusable cache lines using a PC-based Adaptive HCIT replacement policy.

---

# Implemented Cache Replacement Policies (Task 2)

## 1. MRU (Most Recently Used)
The MRU policy evicts the block that was most recently accessed. This is typically beneficial for access patterns that strictly cycle through working sets larger than the cache (e.g., sequential scanning without temporal locality).

## 2. Random
The Random policy evicts a cache block uniformly at random from the set. This policy is simple to implement and avoids pathological edge cases (like cyclic thrashing) where LRU performs exceptionally poorly.

## 3. Adaptive HCIT
The Adaptive HCIT policy is designed to solve a fundamental weakness of LRU: treating all misses equally. Some cache blocks are dead-on-arrival (streaming patterns), while others are evicted just before they would have been reused (Hard-to-Cache Instructions).

**Features:**
- **Victim Tag Buffer (VTB):** Tracks metadata of recently evicted LLC lines to detect premature evictions.
- **PC-based Profiling:** Identifies the PCs responsible for causing premature evictions and protects them, while penalizing PCs that cause dead-on-arrival streaming blocks.
- **Adaptive Thresholds:** Automatically measures global cache hit-rate and adjusts the aggressiveness of the HCIT protection mechanism.

---

# Implemented Predictors (Task 1)

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

## 2. Adaptive Bullseye Predictor

The Adaptive Bullseye predictor further improves the Bullseye design by replacing fixed confidence thresholds with adaptive thresholds that automatically adjust according to recent prediction accuracy.

---

# Build Instructions

Build Adaptive HCIT LLC Policy:
```bash
./build_champsim.sh bimodal no no no no adaptive_hcit 1
```

Build Bullseye Predictor:
```bash
./build_champsim.sh bullseye no no no no lru 1
```

---

# Experimental Results

Experiments were performed on the benchmark traces specified in the assignment.

**Task 2 (Cache Evaluation):**
- 1MB, 2MB, 4MB, 8MB caches with 16-way associativity.
- 2MB cache with 8-way associativity.
- Results and graphical charts are available in `results.md` and `report.html`.

**Task 1 (Branch Prediction Evaluation):**
- Branch Prediction Accuracy, MPKI, Cache Miss Latency, Execution Time.
- Results are available in `accuracy_1core.txt`, `mpki_1core.txt`, etc.

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

results.md
report.html
summary_stats.csv
README.md
```

---

## Author

**Sai Tejas Andey**  
Student ID: F20230040  
BITS Pilani
