#!/usr/bin/env python3
"""
Pre-Deployment Pipeline Verification Gate.

Enforces:
1. Upstream Schema 2.0 Web Manifest existence, structure, narrative density, and anti-meta bleed:
   - Minimum block threshold (>= 50 blocks).
   - Minimum word count threshold (>= 3,000 words).
   - Anti-meta leak filter (blocks out-of-character GM table dialogue).
2. Downstream reader integrity & Zero-Hyperlink Prose Invariant:
   - Chapters modal overlay, cut switcher, diff inspector.
   - Non-empty Codex Wiki modal (at least 30 embedded articles in codexArticlesData).
   - ZERO <a> tags / codex-entity-link elements inside novel blocks container.
3. Bot authentication credentials health across all readers and codex-wiki.html:
   - Non-empty base64 PKCS#8 key, valid app ID, and installation ID.
4. Downstream Hubs (index.html, codex.html, critics.html, threads.html, codex-wiki.html) integrity.
5. Complete automated test suite execution (unittest discover tests).
"""

import base64
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOCAL_SCRIBE = ROOT.parent / "dnd-scribe-main"

MIN_SESSION_BLOCKS = 50
MIN_SESSION_WORDS = 3000
MIN_CODEX_ARTICLES = 30

# Words/phrases forbidden in clean novel narrative prose (Track B)
FORBIDDEN_META_TERMS = [
    r"\bGame Master\b",
    r"\bGamemaster\b",
    r"\bLuke Foreman\b",
    r"\bcharcoal clocks\b",
    r"\bPrize Clock\b",
    r"\bThreat Clock\b",
    r"\bHunter Clock\b",
    r"\broll initiative\b",
    r"\bsaving throw\b",
    r"\bcharacter sheet\b",
]

def log_pass(msg):
    print(f"  [PASS] {msg}")

def log_fail(msg):
    print(f"  [FAIL] {msg}")
    return False

def discover_all_sessions():
    """Dynamically discovers all sessions across upstream and downstream."""
    sessions = set()
    # Check downstream readers
    for r in ROOT.glob("uneraseable-s*.html"):
        m = re.search(r"uneraseable-s(\d+)\.html", r.name)
        if m:
            sessions.add(int(m.group(1)))
    # Check upstream manifests if scribe exists
    if LOCAL_SCRIBE.exists():
        manifest_dir = LOCAL_SCRIBE / "sessions" / "data" / "index"
        for p in manifest_dir.glob("s*-manifest-v2.json"):
            m = re.search(r"s(\d+)-manifest-v2\.json", p.name)
            if m:
                sessions.add(int(m.group(1)))
    return sorted(list(sessions))

def verify_upstream_manifests(sessions):
    print("[1/5] Verifying Upstream Schema 2.0 Manifests & Anti-Meta Bleed...")
    if not LOCAL_SCRIBE.exists():
        log_fail(f"dnd-scribe-main not found at {LOCAL_SCRIBE}")
        return False

    manifest_dir = LOCAL_SCRIBE / "sessions" / "data" / "index"
    clean_dir = LOCAL_SCRIBE / "sessions" / "data" / "clean"

    # Only verify manifests that exist in this checkout (e.g. latest sessions)
    verified_count = 0
    for s_num in sessions:
        manifest_path = manifest_dir / f"s{s_num}-manifest-v2.json"
        clean_path = clean_dir / f"s{s_num}-clean-story.md"

        if not manifest_path.exists():
            continue

        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        blocks = data.get("blocks", [])
        word_count = data.get("stats", {}).get("wordCount", 0)

        if len(blocks) < MIN_SESSION_BLOCKS:
            return log_fail(f"Manifest s{s_num} blocks ({len(blocks)}) below minimum requirement ({MIN_SESSION_BLOCKS})")
        if word_count < MIN_SESSION_WORDS:
            return log_fail(f"Manifest s{s_num} word count ({word_count:,}) below minimum required ({MIN_SESSION_WORDS:,})")

        # Anti-Meta Leak Scan across blocks
        for b in blocks:
            b_text = b.get("text", "")
            for term in FORBIDDEN_META_TERMS:
                if re.search(term, b_text, re.IGNORECASE):
                    return log_fail(f"Out-of-character meta table leak '{term}' found in s{s_num} block {b.get('id')}")

        # Anti-Meta Leak Scan across clean story markdown
        if clean_path.exists():
            c_text = clean_path.read_text(encoding="utf-8")
            for term in FORBIDDEN_META_TERMS:
                if re.search(term, c_text, re.IGNORECASE):
                    return log_fail(f"Out-of-character meta table leak '{term}' found in {clean_path.name}")

        log_pass(f"Session {s_num}: Verified manifest ({len(blocks)} blocks, {word_count:,} words) with zero meta bleed")
        verified_count += 1

    if verified_count == 0:
        return log_fail("No upstream Schema 2.0 manifests found to verify!")
    return True

def verify_downstream_readers(sessions):
    print(f"[2/5] Verifying Compiled Readers & Zero-Hyperlink Invariant (Sessions {sessions[0]}–{sessions[-1]})...")
    for s in sessions:
        reader = ROOT / f"uneraseable-s{s}.html"
        if not reader.exists():
            return log_fail(f"Omission failure: Compiled reader missing: {reader.name}")
        
        content = reader.read_text(encoding="utf-8")
        if "id=\"chaptersModalOverlay\"" not in content and "id=\"chaptersModal\"" not in content:
            return log_fail(f"Chapters modal overlay missing in {reader.name}")
        if "switchGlobalCut" not in content:
            return log_fail(f"Cut switcher missing in {reader.name}")
        if "diffInspector" not in content and "openDiffInspector" not in content:
            return log_fail(f"Diff inspector missing in {reader.name}")
        
        # Verify Codex Articles Data is populated in reader modal
        m = re.search(r'id="codexArticlesData"[^>]*>(.*?)</script>', content, re.DOTALL)
        if not m:
            return log_fail(f"codexArticlesData script tag missing in {reader.name}")
        try:
            articles = json.loads(m.group(1))
            if len(articles) < MIN_CODEX_ARTICLES:
                return log_fail(f"Codex modal in {reader.name} has only {len(articles)} articles (minimum {MIN_CODEX_ARTICLES} required)")
        except Exception as e:
            return log_fail(f"Failed to parse codexArticlesData in {reader.name}: {e}")

        # Zero-Hyperlink Invariant: Novel blocks container must contain STRICTLY ZERO <a> tags
        match = re.search(r'<div class="novel-blocks-container">(.*?)<div class="cut-block cut-block-raw', content, re.DOTALL)
        if not match:
            return log_fail(f"novel-blocks-container missing in {reader.name}")
        novel_html = match.group(1)

        links = re.findall(r'<a\s+[^>]*>.*?</a>', novel_html)
        if len(links) > 0:
            return log_fail(f"Scope creep violation: {len(links)} links found in {reader.name} novel blocks: {links[:3]}")
        if "codex-entity-link" in novel_html:
            return log_fail(f"codex-entity-link found inside novel container in {reader.name}")
        if "codex-crosslink" in novel_html:
            return log_fail(f"codex-crosslink found inside novel container in {reader.name}")

        log_pass(f"{reader.name} ({len(content):,} bytes) verified (pure prose, zero links, full controls, {len(articles)} codex entries)")
    return True

def verify_bot_authentication(sessions):
    print("[3/5] Verifying GitHub App Bot Authentication Health...")
    targets = [ROOT / f"uneraseable-s{s}.html" for s in sessions]
    wiki = ROOT / "codex-wiki.html"
    if wiki.exists():
        targets.append(wiki)

    for target in targets:
        content = target.read_text(encoding="utf-8")
        m_app = re.search(r'const BOT_APP_ID = "([^"]*)";', content)
        m_inst = re.search(r'const BOT_INSTALLATION_ID = "([^"]*)";', content)
        m_key = re.search(r'const BOT_PKCS8_B64 = "([^"]*)";', content)

        if not m_app or m_app.group(1) != "4866708":
            return log_fail(f"Invalid BOT_APP_ID in {target.name}")
        if not m_inst or m_inst.group(1) != "159911323":
            return log_fail(f"Invalid BOT_INSTALLATION_ID in {target.name}")
        if not m_key or len(m_key.group(1)) < 1000:
            return log_fail(f"Missing or truncated BOT_PKCS8_B64 key in {target.name}")

        try:
            der = base64.b64decode(m_key.group(1))
            if len(der) < 1000:
                return log_fail(f"Decoded PKCS#8 DER key unexpectedly small in {target.name}")
        except Exception as e:
            return log_fail(f"Invalid base64 in BOT_PKCS8_B64 for {target.name}: {e}")

    log_pass(f"All {len(targets)} readers & wiki have valid, decodable GitHub App bot credentials")
    return True

def verify_hub_integrations(sessions):
    print("[4/5] Verifying Cross-Hub Navigation & Omission Prevention...")
    # index.html
    idx = (ROOT / "index.html").read_text(encoding="utf-8")
    for s in sessions:
        if f"uneraseable-s{s}.html" not in idx:
            return log_fail(f"uneraseable-s{s}.html missing from index.html")
    log_pass(f"index.html contains all {len(sessions)} sessions in recent-to-earliest chapters list")

    # codex.html
    codex = (ROOT / "codex.html").read_text(encoding="utf-8")
    for s in sessions:
        if f'id="session-{s}"' not in codex:
            return log_fail(f"session-{s} card missing from codex.html")
        if f"uneraseable-s{s}.html" not in codex:
            return log_fail(f"uneraseable-s{s}.html link missing from codex.html")
    log_pass(f"codex.html contains active cards and links for all {len(sessions)} sessions")

    # critics.html
    critics = (ROOT / "critics.html").read_text(encoding="utf-8")
    latest = max(sessions)
    if f"S{latest} (Latest)" not in critics:
        return log_fail(f"S{latest} (Latest) button missing from critics.html")
    log_pass(f"critics.html contains S{latest} audit and active initialization")

    # threads.html
    threads = (ROOT / "threads.html").read_text(encoding="utf-8")
    if f"uneraseable-s{latest}.html" not in threads:
        return log_fail(f"uneraseable-s{latest}.html links missing from threads.html")
    log_pass(f"threads.html references Session {latest} with verified links")

    # Standalone codex-wiki.html
    wiki = ROOT / "codex-wiki.html"
    if not wiki.exists():
        return log_fail("Standalone codex-wiki.html missing")
    wiki_content = wiki.read_text(encoding="utf-8")
    if "The Margin Campaign Codex" not in wiki_content:
        return log_fail("Standalone codex-wiki.html title missing")
    log_pass("Standalone codex-wiki.html verified and active")
    return True

def run_test_suite():
    print("[5/5] Executing Automated Unit Test Suite...")
    res = subprocess.run([sys.executable, "-m", "unittest", "discover", "tests"], cwd=str(ROOT), capture_output=True, text=True)
    if res.returncode != 0:
        print(res.stderr)
        return log_fail("Automated test suite failed!")
    print(res.stdout.strip())
    log_pass("All unit tests passed cleanly")
    return True

def main():
    print("==================================================")
    print("🛡️ D&D HARDENED PRE-DEPLOYMENT VERIFICATION GATE")
    print("==================================================")
    sessions = discover_all_sessions()
    print(f"[INFO] Discovered active session roster: {sessions}")

    steps = [
        lambda: verify_upstream_manifests(sessions),
        lambda: verify_downstream_readers(sessions),
        lambda: verify_bot_authentication(sessions),
        lambda: verify_hub_integrations(sessions),
        run_test_suite
    ]
    for step in steps:
        if not step():
            print("\n❌ DEPLOYMENT BLOCKED: Hardened pipeline verification failed.")
            sys.exit(1)
    print("\n✅ DEPLOYMENT APPROVED: All 5 hardened pipeline gates passed!")

if __name__ == "__main__":
    main()
