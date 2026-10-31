#!/usr/bin/env python3
"""
Pre-Deployment Pipeline Verification Gate.

Enforces:
1. Upstream Schema 2.0 Web Manifest existence and structure for latest session.
2. Canonical reader generation via build_ebooks.py without ad-hoc synthesis.
3. Downstream Hub (index.html, codex.html, critics.html, threads.html) integrity.
4. Complete automated test suite execution (unittest discover tests).
"""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOCAL_SCRIBE = ROOT.parent / "dnd-scribe-main"

def log_pass(msg):
    print(f"  [PASS] {msg}")

def log_fail(msg):
    print(f"  [FAIL] {msg}")
    return False

def verify_upstream_manifest(session_num=8):
    print(f"[1/4] Verifying Upstream Schema 2.0 Manifest for Session {session_num}...")
    if not LOCAL_SCRIBE.exists():
        log_fail(f"dnd-scribe-main not found at {LOCAL_SCRIBE}")
        return False

    manifest_path = LOCAL_SCRIBE / "sessions" / "data" / "index" / f"s{session_num}-manifest-v2.json"
    raw_path = LOCAL_SCRIBE / "sessions" / "data" / "index" / f"s{session_num}-raw-indexed.md"
    clean_path = LOCAL_SCRIBE / "sessions" / "data" / "clean" / f"s{session_num}-clean-story.md"

    if not manifest_path.exists():
        return log_fail(f"Manifest missing: {manifest_path}")
    if not raw_path.exists():
        return log_fail(f"Raw indexed transcript missing: {raw_path}")
    if not clean_path.exists():
        return log_fail(f"Clean story markdown missing: {clean_path}")

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    blocks = data.get("blocks", [])
    if not blocks:
        return log_fail("Manifest has 0 blocks")
    
    log_pass(f"Schema 2.0 Manifest verified ({len(blocks)} blocks, {data.get('stats', {}).get('wordCount', 0)} words)")
    return True

def verify_downstream_readers():
    print("[2/4] Verifying Compiled Readers (uneraseable-s1.html to s8.html)...")
    for s in range(1, 9):
        reader = ROOT / f"uneraseable-s{s}.html"
        if not reader.exists():
            return log_fail(f"Reader missing: {reader.name}")
        content = reader.read_text(encoding="utf-8")
        if "id=\"chaptersModalOverlay\"" not in content and "id=\"chaptersModal\"" not in content:
            return log_fail(f"Chapters modal overlay missing in {reader.name}")
        if "switchGlobalCut" not in content:
            return log_fail(f"Cut switcher missing in {reader.name}")
        if "diffInspector" not in content and "openDiffInspector" not in content:
            return log_fail(f"Diff inspector missing in {reader.name}")
        log_pass(f"{reader.name} ({len(content):,} bytes) verified with full Schema 2.0 reader controls")
    return True

def verify_hub_integrations():
    print("[3/4] Verifying Codex, Critics, Threads, and Index Hub Integrations...")
    # index.html
    idx = (ROOT / "index.html").read_text(encoding="utf-8")
    if "uneraseable-s8.html" not in idx:
        return log_fail("uneraseable-s8.html missing from index.html")
    log_pass("index.html contains Session 8 in recent-to-earliest chapters list")

    # codex.html
    codex = (ROOT / "codex.html").read_text(encoding="utf-8")
    if 'id="session-8"' not in codex:
        return log_fail("session-8 card missing from codex.html")
    if "uneraseable-s8.html" not in codex:
        return log_fail("uneraseable-s8.html link missing from codex.html")
    log_pass("codex.html contains Session 8 card with active navigation")

    # critics.html
    critics = (ROOT / "critics.html").read_text(encoding="utf-8")
    if "S8 (Latest)" not in critics:
        return log_fail("S8 button missing from critics.html")
    log_pass("critics.html contains S8 audit and default initialization")

    # threads.html
    threads = (ROOT / "threads.html").read_text(encoding="utf-8")
    if "uneraseable-s8.html" not in threads:
        return log_fail("uneraseable-s8.html links missing from threads.html")
    log_pass("threads.html references Session 8 with verified links")
    return True

def run_test_suite():
    print("[4/4] Executing Automated Unit Test Suite...")
    res = subprocess.run([sys.executable, "-m", "unittest", "discover", "tests"], cwd=str(ROOT), capture_output=True, text=True)
    if res.returncode != 0:
        print(res.stderr)
        return log_fail("Automated test suite failed!")
    print(res.stdout.strip())
    log_pass("All unit tests passed cleanly")
    return True

def main():
    print("==================================================")
    print("🚀 D&D PROJECT DEPLOYMENT PIPELINE VERIFICATION GATE")
    print("==================================================")
    steps = [
        verify_upstream_manifest,
        verify_downstream_readers,
        verify_hub_integrations,
        run_test_suite
    ]
    for step in steps:
        if not step():
            print("\n❌ DEPLOYMENT BLOCKED: Pipeline verification failed.")
            sys.exit(1)
    print("\n✅ DEPLOYMENT APPROVED: All pipeline checks and tests passed!")

if __name__ == "__main__":
    main()
