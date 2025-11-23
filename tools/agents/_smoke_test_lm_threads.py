import sys
import time
from pathlib import Path

# Ensure repo and servers are on path
REPO = Path(__file__).resolve().parents[2]
SERVERS = REPO / "03-dev" / "002-meetingroom" / "servers"
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(SERVERS))

import importlib.util

srv_path = SERVERS / "meetingroom_server.py"
spec = importlib.util.spec_from_file_location("meetingroom_server", str(srv_path))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

print("[SMOKE] REPO_ROOT:", REPO)
print("[SMOKE] LM_DIR:", m.LM_DIR)
print("[SMOKE] LM_CONFIG_DIR:", m.LM_CONFIG_DIR)
print("[SMOKE] Ensure LM loaded:", m._ensure_lm_loaded())

mods = m._ensure_lm_loaded()

print("[SMOKE] Starting reminder (direct instantiate)...")
rem_mod = mods.get("reminder")
assert rem_mod is not None, "proactive_reminder module not loaded"
rem_inst = rem_mod.ProactiveReminder(config_path=str(m.reminder_cfg))
try:
    rem_inst.memory_path = str(m.storage_path)
    if hasattr(rem_inst, "load_memory_data"):
        rem_inst.load_memory_data()
except Exception:
    pass
rem_inst.start_monitoring()
time.sleep(1.0)
print("[SMOKE] reminder statistics:", getattr(rem_inst, "get_statistics", lambda: {} )())
print("[SMOKE] Stopping reminder...")
try:
    rem_inst.stop_monitoring()
except Exception as e:
    print("[SMOKE] reminder stop error:", e)

print("[SMOKE] Starting monitor (direct instantiate)...")
mon_mod = mods.get("monitor")
assert mon_mod is not None, "intelligent_monitor module not loaded"
mon_inst = mon_mod.IntelligentMonitor(config_path=str(m.monitor_cfg))
try:
    mon_inst.memory_path = str(m.storage_path)
    if hasattr(mon_mod, "LearningEngine"):
        mon_inst.learning_engine = mon_mod.LearningEngine(mon_inst.memory_path)
except Exception:
    pass
mon_inst.start_monitoring()
time.sleep(1.0)
print("[SMOKE] monitor status:", getattr(mon_inst, "get_system_status", lambda: {} )())
print("[SMOKE] Stopping monitor...")
try:
    mon_inst.stop_monitoring()
except Exception as e:
    print("[SMOKE] monitor stop error:", e)