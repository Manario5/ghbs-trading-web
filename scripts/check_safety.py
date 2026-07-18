#!/usr/bin/env python3
import urllib.request
import json
import sys

URL = "http://127.0.0.1:8000/api/system/safety-matrix"

print("Checking System Safety State...")

try:
    req = urllib.request.Request(URL)
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
except Exception as e:
    print(f"ERROR: Could not reach backend at {URL}")
    print(f"Details: {e}")
    sys.exit(1)

safety_state = data.get("safety_state", "UNKNOWN")
db_path = data.get("db_path", "UNKNOWN")
allow_prod = data.get("allow_production_db", False)
scheduler = data.get("alert_scheduler_enabled", False)
provider_scan = data.get("provider_coverage_scan_enabled", False)
scout = data.get("live_scout_preview_enabled", False)
analyze = data.get("live_analyze_preview_enabled", False)

print("-" * 40)
print(" SAFETY MATRIX STATUS")
print("-" * 40)
print(f" Safety State:                   {safety_state}")
print(f" Production DB Access Allowed:   {allow_prod}")
print(f" Database Path:                  {db_path}")
print(f" Alert Scheduler:                {scheduler}")
print(f" Provider Coverage Scan:         {provider_scan}")
print(f" Live Scout Preview:             {scout}")
print(f" Live Analyze Preview:           {analyze}")
print("-" * 40)

if safety_state == "UNSAFE":
    print("WARNING: System is in UNSAFE mode.")
    sys.exit(1)
elif safety_state == "WARNING":
    print("NOTICE: System is in WARNING mode.")
else:
    print("OK: System is SAFE.")
sys.exit(0)
