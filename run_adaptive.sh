#!/bin/bash
set -e

# Run adaptive_bullseye
./run_champsim.sh adaptive_bullseye-no-no-no-no-lru-1core 1 10 401.bzip2-277B.champsimtrace.xz
./run_champsim.sh adaptive_bullseye-no-no-no-no-lru-1core 1 10 403.gcc-16B.champsimtrace.xz
./run_champsim.sh adaptive_bullseye-no-no-no-no-lru-1core 1 10 434.zeusmp-10B.champsimtrace.xz
./run_champsim.sh adaptive_bullseye-no-no-no-no-lru-1core 1 10 450.soplex-92B.champsimtrace.xz
