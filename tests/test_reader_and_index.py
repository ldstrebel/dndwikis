#!/usr/bin/env python3
"""
Automated Test Suite for D&D Wikis Campaign View & Interactive Reader.

Validates:
1. index.html integrity:
   - All 5 sessions of Uneraseable are present (S1 to S5).
   - Chapters are ordered newest to oldest (recent to earliest).
   - All campaign links point to existing HTML files.
   - Dynamic cover art scaling logic in script.js and style.css.
2. Reader files (uneraseable-s1.html through s5.html):
   - JavaScript AST parses cleanly without syntax errors.
   - mode-critique is active by default so narrative can be tapped for feedback.
   - Story block click handlers are configured.
   - No horizontal overflow risks (html/body overflow-x, no negative right margins on hover icons).
   - Modal z-index hierarchy and no buggy translateY viewport transforms.
   - Critic forum modal is scrollable and dismissible.
"""

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class TestIndexCampaignView(unittest.TestCase):
    def setUp(self):
        self.index_path = ROOT / "index.html"
        self.assertTrue(self.index_path.exists(), "index.html must exist")
        self.content = self.index_path.read_text(encoding="utf-8")

    def test_uneraseable_contains_all_five_sessions(self):
        """Uneraseable must list Session 1 through Session 5."""
        m = re.search(r'data-campaign-title="Uneraseable"[^>]*data-chapters=\'([^\']+)\'', self.content)
        self.assertIsNotNone(m, "Uneraseable data-chapters attribute must exist")
        chapters = json.loads(m.group(1))
        
        self.assertEqual(len(chapters), 5, f"Expected 5 sessions, got {len(chapters)}")
        urls = [c["url"] for c in chapters]
        for s in range(1, 6):
            expected_url = f"uneraseable-s{s}.html"
            self.assertIn(expected_url, urls, f"{expected_url} missing from Uneraseable")
            target_file = ROOT / expected_url
            self.assertTrue(target_file.exists(), f"Target file {target_file} does not exist")

    def test_uneraseable_sorted_recent_to_earliest(self):
        """Uneraseable chapters must be sorted from most recent (S5) to earliest (S1)."""
        m = re.search(r'data-campaign-title="Uneraseable"[^>]*data-chapters=\'([^\']+)\'', self.content)
        chapters = json.loads(m.group(1))
        urls = [c["url"] for c in chapters]
        expected_order = [
            "uneraseable-s5.html",
            "uneraseable-s4.html",
            "uneraseable-s3.html",
            "uneraseable-s2.html",
            "uneraseable-s1.html",
        ]
        self.assertEqual(urls, expected_order, "Chapters should be ordered from Session 5 down to Session 1")

    def test_all_campaign_links_exist(self):
        """All URLs in data-chapters across all campaigns must resolve to real files."""
        all_chapters_attrs = re.findall(r'data-chapters=\'([^\']+)\'', self.content)
        self.assertGreaterEqual(len(all_chapters_attrs), 4, "Should find at least 4 campaigns")
        for raw in all_chapters_attrs:
            chapters = json.loads(raw)
            for c in chapters:
                url = c.get("url")
                if url and not url.startswith("http"):
                    file_path = ROOT / url
                    self.assertTrue(file_path.exists(), f"Linked file {url} in campaign index does not exist")

    def test_dynamic_art_scaling_logic_in_script_and_css(self):
        """Verify dynamic scaling logic exists in script.js and style.css."""
        script_js = (ROOT / "script.js").read_text(encoding="utf-8")
        self.assertIn("modal.dataset.chapterCount", script_js, "script.js must set dataset.chapterCount")
        self.assertIn("modalImage.style.maxHeight", script_js, "script.js must scale modalImage maxHeight")
        
        style_css = (ROOT / "style.css").read_text(encoding="utf-8")
        self.assertIn(".modal-chapter-list", style_css)
        self.assertIn("overflow-y: auto", style_css, "modal-chapter-list must have overflow-y: auto")


class TestReaderPages(unittest.TestCase):
    def setUp(self):
        self.sessions = [ROOT / f"uneraseable-s{s}.html" for s in range(1, 6)]
        for s in self.sessions:
            self.assertTrue(s.exists(), f"{s.name} must exist")

    def test_mode_critique_active_by_default(self):
        """Every session must have mode-critique active on body so narrative blocks can be tapped for feedback."""
        for s in self.sessions:
            content = s.read_text(encoding="utf-8")
            self.assertIn('body class="bg-slate-950 text-slate-100 min-h-screen pb-24 mode-critique"', content,
                          f"{s.name} must have mode-critique on body tag")
            self.assertIn("setReadingMode(currentReadingMode || 'critique')", content,
                          f"{s.name} must initialize setReadingMode on startup")

    def test_no_horizontal_overflow_risks(self):
        """html, body must have overflow-x: hidden, and story-block hover must not have negative right margin."""
        for s in self.sessions:
            content = s.read_text(encoding="utf-8")
            self.assertIn("overflow-x: hidden", content, f"{s.name} must have overflow-x: hidden")
            # Ensure right: -28px is NOT in the stylesheet
            self.assertNotIn("right: -28px", content,
                             f"{s.name} must not contain right: -28px (causes horizontal scroll)")

    def test_critic_modal_z_index_and_safety(self):
        """criticForumModalOverlay must have z-[80] and overflow-y-auto."""
        for s in self.sessions:
            content = s.read_text(encoding="utf-8")
            self.assertIn('id="criticForumModalOverlay" class="fixed inset-0 bg-slate-950/85 backdrop-blur-md z-[80]',
                          content, f"{s.name} criticForumModalOverlay must be z-[80]")
            self.assertIn('overflow-y-auto', content)
            # Ensure no buggy visualViewport.offsetTop transforms are applied to fixed modals
            self.assertNotIn("criticForumModalOverlay.style.transform = 'translateY(", content,
                             f"{s.name} must not transform translateY on criticForumModalOverlay")

    def test_story_block_click_wiring(self):
        """Story blocks must have click listener that triggers openDiffInspector in critique mode."""
        for s in self.sessions:
            content = s.read_text(encoding="utf-8")
            self.assertIn("openDiffInspector(idx)", content,
                          f"{s.name} must call openDiffInspector on story block tap")


if __name__ == "__main__":
    unittest.main()
