import os
import csv
import json
import sys

workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

from framework.parser import parse_champsim_log

def verify_branch_suite():
    csv_path = os.path.join(workspace_root, "results", "branch_suite_summary.csv")
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
    
    assert len(reader) == 25, f"Expected 25 branch runs, got {len(reader)}"
    print(f"[*] Validating {len(reader)} branch suite entries against logs and JSON...")
    
    for row in reader:
        log_file = row["log_file"]
        json_file = log_file.rsplit(".", 1)[0] + ".json"
        
        txt_path = os.path.join(workspace_root, "results", "branch_suite", log_file)
        json_path = os.path.join(workspace_root, "results", "branch_suite", json_file)
        
        assert os.path.exists(txt_path), f"Missing log: {txt_path}"
        assert os.path.exists(json_path), f"Missing JSON: {json_path}"
        
        # 1. Check JSON file
        with open(json_path, "r", encoding="utf-8") as jf:
            jdata = json.load(jf)
            
        csv_ipc = float(row["ipc"])
        json_ipc = float(jdata["cpu"]["0"]["ipc"])
        assert abs(csv_ipc - json_ipc) < 1e-4, f"Branch IPC mismatch: {csv_ipc} vs {json_ipc} in {log_file}"
        
        csv_cycles = int(row["cycles"])
        json_cycles = int(jdata["cpu"]["0"]["cycles"])
        assert csv_cycles == json_cycles, f"Branch cycle mismatch in {log_file}"
        
        csv_acc = float(row["accuracy_pct"])
        json_acc = float(jdata["branch"]["0"]["accuracy_pct"])
        assert abs(csv_acc - json_acc) < 1e-2, f"Branch accuracy mismatch in {log_file}"

        # 2. Re-parse raw text log directly
        reparsed = parse_champsim_log(txt_path, is_path=True)
        assert reparsed["status"] == "COMPLETED"
        assert abs(reparsed["cpu"][0]["ipc"] - csv_ipc) < 1e-4
        assert reparsed["cpu"][0]["cycles"] == csv_cycles
        assert abs(reparsed["branch"][0]["accuracy_pct"] - csv_acc) < 1e-2
        
    print("[+] Branch suite 100% verified! All CSV, JSON, and raw logs match exactly.")

def verify_cache_suite():
    csv_path = os.path.join(workspace_root, "results", "cache_suite_summary.csv")
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        
    assert len(reader) == 96, f"Expected 96 cache runs, got {len(reader)}"
    print(f"[*] Validating {len(reader)} cache suite entries against logs and JSON...")
    
    for row in reader:
        log_file = row["log_file"]
        json_file = log_file.rsplit(".", 1)[0] + ".json"
        
        txt_path = os.path.join(workspace_root, "results", "cache_suite", log_file)
        json_path = os.path.join(workspace_root, "results", "cache_suite", json_file)
        
        assert os.path.exists(txt_path), f"Missing log: {txt_path}"
        assert os.path.exists(json_path), f"Missing JSON: {json_path}"
        
        with open(json_path, "r", encoding="utf-8") as jf:
            jdata = json.load(jf)
            
        csv_ipc = float(row["ipc"])
        json_ipc = float(jdata["cpu"]["0"]["ipc"])
        assert abs(csv_ipc - json_ipc) < 1e-4, f"Cache IPC mismatch: {csv_ipc} vs {json_ipc} in {log_file}"
        
        csv_hit_rate = float(row["llc_hit_rate"])
        json_hit_rate = float(jdata["cache"]["LLC"]["hit_rate"])
        assert abs(csv_hit_rate - json_hit_rate) < 1e-4, f"Cache hit rate mismatch in {log_file}"
        
        csv_accesses = int(row["llc_accesses"])
        json_accesses = int(jdata["cache"]["LLC"]["access"])
        assert csv_accesses == json_accesses, f"Cache accesses mismatch in {log_file}"

        # Re-parse raw text log directly
        reparsed = parse_champsim_log(txt_path, is_path=True)
        assert reparsed["status"] == "COMPLETED"
        assert abs(reparsed["cpu"][0]["ipc"] - csv_ipc) < 1e-4
        assert reparsed["cpu"][0]["cycles"] == int(row["cycles"])
        assert abs(reparsed["cache"]["LLC"]["hit_rate"] - csv_hit_rate) < 1e-4
        assert reparsed["cache"]["LLC"]["access"] == csv_accesses

    print("[+] Cache suite 100% verified! All CSV, JSON, and raw logs match exactly.")

if __name__ == "__main__":
    verify_branch_suite()
    verify_cache_suite()
