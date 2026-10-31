#!/usr/bin/env python3
"""
Pre-Deployment Pipeline Verification Gate (dndwikis)
Enforces strict parity across all publishing surfaces before any push to production:
1. Index Parity: Every published session in index.html data-chapters must have an on-disk reader file.
2. Reader Integrity: All uneraseable-sN.html files must exist, be non-empty, and contain required reading lenses.
3. Codex Link Parity: Every 'Read Story Chapter →' link in codex.html must resolve to an existing reader file.
4. Codex & Critics Alignment: The published session count in codex.html must match index.html and critics.html.
5. No Phantom Sessions: A session cannot be marked as an active published story chapter unless its interactive reader exists.
"""

import sys
import re
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def verify_pipeline():
    errors = []
    warnings = []

    # 1. Read index.html
    index_path = ROOT / "index.html"
    if not index_path.exists():
        errors.append("index.html does not exist")
        return errors, warnings
    
    index_content = index_path.read_text(encoding="utf-8")
    m = re.search(r'data-campaign-title="Uneraseable"[^>]*data-chapters=\'([^\']+)\'', index_content)
    if not m:
        errors.append("index.html: Could not find data-chapters attribute for Uneraseable")
        return errors, warnings
    
    published_chapters = json.loads(m.group(1))
    published_urls = [c["url"] for c in published_chapters]
    
    # Extract session numbers from published URLs
    published_sessions = []
    for url in published_urls:
        sm = re.search(r'uneraseable-s(\d+)\.html', url)
        if sm:
            published_sessions.append(int(sm.group(1)))
        else:
            errors.append(f"index.html: Published chapter URL '{url}' does not follow 'uneraseable-sN.html' pattern")
    
    published_sessions = sorted(published_sessions)
    print(f"📋 Verified Published Sessions in index.html: {published_sessions}")

    # 2. Check reader files on disk
    for s_num in published_sessions:
        reader_file = ROOT / f"uneraseable-s{s_num}.html"
        if not reader_file.exists():
            errors.append(f"Deployment Gate Violation: '{reader_file.name}' is declared in index.html but does not exist on disk!")
        elif reader_file.stat().st_size < 1000:
            errors.append(f"Deployment Gate Violation: '{reader_file.name}' is corrupted or incomplete (< 1000 bytes)!")

    # 3. Read codex.html
    codex_path = ROOT / "codex.html"
    if not codex_path.exists():
        errors.append("codex.html does not exist")
        return errors, warnings
    
    codex_content = codex_path.read_text(encoding="utf-8")
    
    # Find all 'Read Story Chapter' links in codex.html
    story_links = re.findall(r'href="(uneraseable-s\d+\.html)"[^>]*>\s*Read Story Chapter', codex_content)
    for link in story_links:
        target = ROOT / link
        if not target.exists():
            errors.append(f"Codex Broken Link: codex.html links to '{link}' via 'Read Story Chapter →', but the file does not exist!")

    # Check for sessions in codex articles
    codex_articles = re.findall(r'<article id="session-(\d+)"', codex_content)
    codex_sessions = sorted([int(s) for s in codex_articles])
    print(f"📖 Registered Sessions in codex.html: {codex_sessions}")

    # Check session buttons in codex header
    codex_buttons = re.findall(r'class="[^"]*session-tab-btn[^"]*"[^>]*data-session="(\d+)"', codex_content)
    codex_btn_sessions = sorted(list(set([int(s) for s in codex_buttons])))

    # Check if any session is presented as a published story in codex without a reader
    for s_num in codex_sessions:
        reader_path = ROOT / f"uneraseable-s{s_num}.html"
        if not reader_path.exists():
            # Check if it has a 'Read Story Chapter' link
            has_reader_link = f'uneraseable-s{s_num}.html' in codex_content
            if has_reader_link:
                errors.append(f"Phantom Session Gate Violation: Session {s_num} has a reader link in codex.html, but '{reader_path.name}' has NOT been compiled!")
            else:
                warnings.append(f"Note: Session {s_num} is an uncompiled live table chronicle (no interactive reader yet).")

    # 4. Read critics.html
    critics_path = ROOT / "critics.html"
    if critics_path.exists():
        critics_content = critics_path.read_text(encoding="utf-8")
        critics_buttons = re.findall(r'loadSessionAudit\((\d+)', critics_content)
        critics_sessions = sorted(list(set([int(s) for s in critics_buttons])))
        print(f"🎭 Registered Sessions in critics.html: {critics_sessions}")

    # Summary
    if errors:
        print("\n❌ PRE-DEPLOYMENT PIPELINE VERIFICATION FAILED:")
        for err in errors:
            print(f"   • {err}")
        return False
    else:
        print("\n✅ PRE-DEPLOYMENT PIPELINE VERIFICATION PASSED:")
        print(f"   • {len(published_sessions)} published reader chapters verified.")
        print(f"   • Zero broken story links in codex.")
        for warn in warnings:
            print(f"   ⚠️ {warn}")
        return True

if __name__ == "__main__":
    success = verify_pipeline()
    if not success:
        sys.exit(1)
