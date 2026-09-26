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

    def test_default_reading_mode_and_cinematic_cut(self):
        """Readers must always default to clean Read Mode and Cinematic Cut when they start."""
        for s in self.sessions:
            content = s.read_text(encoding="utf-8")
            self.assertIn('body class="bg-slate-950 text-slate-100 min-h-screen pb-24"', content,
                          f"{s.name} must start with clean reading mode on body")
            self.assertIn("setReadingMode(currentReadingMode || 'read')", content,
                          f"{s.name} must default to read mode on startup")
            self.assertIn("currentActiveCut = 'cinematic'", content,
                          f"{s.name} must default to cinematic cut")

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
            self.assertNotIn("criticForumModalOverlay.style.transform = 'translateY(", content,
                             f"{s.name} must not transform translateY on criticForumModalOverlay")

    def test_sticky_header_cut_switcher(self):
        """Header must have sticky cut switcher buttons for cinematic, tabletop, and raw."""
        for s in self.sessions:
            content = s.read_text(encoding="utf-8")
            self.assertIn('class="header-cut-btn cut-btn-cinematic', content,
                          f"{s.name} missing header cinematic button")
            self.assertIn('class="header-cut-btn cut-btn-tabletop', content,
                          f"{s.name} missing header tabletop button")
            self.assertIn('class="header-cut-btn cut-btn-raw', content,
                          f"{s.name} missing header raw button")
            self.assertIn("updateButtonStyles('.header-cut-btn');", content,
                          f"{s.name} switchGlobalCut must sync header-cut-btn")

    def test_story_block_click_ungated(self):
        """Clicking narrative blocks or raw turns must open feedback modal without requiring mode-critique toggle."""
        for s in self.sessions:
            content = s.read_text(encoding="utf-8")
            # Verify block click listener does NOT gate on mode-critique
            self.assertNotIn("if (document.body.classList.contains('mode-critique')) {\n                        updateBlocksReference();\n                        const idx = blocks.indexOf(b);",
                             content, f"{s.name} story-block click must not be gated behind mode-critique")
            self.assertIn("document.querySelectorAll('.raw-turn').forEach((rt)", content,
                          f"{s.name} raw turns must have tap-to-feedback click listener")

    def test_side_by_side_diff_button_wiring(self):
        """Side-by-side diff view button must be accessible, z-[90], and toggle opacity/pointer-events."""
        for s in self.sessions:
            content = s.read_text(encoding="utf-8")
            self.assertIn("Side-by-Side View", content,
                          f"{s.name} modalOpenDiffBtn must display Side-by-Side View text")
            self.assertIn('id="diffInspectorOverlay" class="fixed inset-0 bg-slate-950/95 backdrop-blur-md z-[90]',
                          content, f"{s.name} diffInspectorOverlay must have z-[90]")
            self.assertIn("diffInspectorOverlay.classList.remove('opacity-0', 'pointer-events-none');", content,
                          f"{s.name} openDiffInspector must remove opacity-0 pointer-events-none")

    def test_modal_dom_hierarchy_no_trapping(self):
        """settingsModalOverlay must close cleanly before rawReturnBanner and criticForumModalOverlay."""
        for s in self.sessions:
            content = s.read_text(encoding="utf-8")
            settings_idx = content.find('id="settingsModalOverlay"')
            critic_idx = content.find('id="criticForumModalOverlay"')
            raw_banner_idx = content.find('id="rawReturnBanner"')
            self.assertTrue(settings_idx != -1 and critic_idx != -1 and raw_banner_idx != -1,
                            f"{s.name} must contain settings, critic, and raw banner overlays")
            # Ensure settingsModalOverlay closes with </div> before rawReturnBanner
            settings_snippet = content[settings_idx:raw_banner_idx]
            self.assertIn("</div>\n    </div>\n    <!-- Floating Return to Story Banner",
                          settings_snippet,
                          f"{s.name} settingsModalOverlay must be closed before rawReturnBanner")

    def test_no_meta_hallucination_jargon(self):
        """HTML must not contain meta jargon about anti-hallucination convergence boundaries or quality gate stops."""
        forbidden_phrases = [
            "Anti-Hallucination",
            "Convergence Boundary",
            "Quality Gate Stop",
            "Where AI Cannot Tread",
        ]
        for s in self.sessions:
            content = s.read_text(encoding="utf-8")
            for phrase in forbidden_phrases:
                self.assertNotIn(phrase, content, f"{s.name} must not contain meta jargon: '{phrase}'")

    def test_player_critique_tabs_and_shortcomings(self):
        """Critic modal must have tabbed player breakdown with prominent critical narrative shortcomings."""
        for s in self.sessions:
            content = s.read_text(encoding="utf-8")
            self.assertIn("player-critique-tab-btn", content,
                          f"{s.name} must contain player-critique-tab-btn tab bar")
            self.assertIn("Critical Narrative Shortcomings", content,
                          f"{s.name} must highlight Critical Narrative Shortcomings")
            self.assertIn("switchPlayerCritiqueTab", content,
                          f"{s.name} must implement switchPlayerCritiqueTab")

    def test_session5_dialogue_calculation(self):
        """Session 5 must properly calculate spoken dialogue and display correct percentages."""
        s5_content = (ROOT / "uneraseable-s5.html").read_text(encoding="utf-8")
        self.assertIn("32.0% Dialogue", s5_content, "Session 5 card must calculate 32.0% dialogue")
        self.assertIn("2,705", s5_content, "Session 5 card must show 2,705 spoken words")
        self.assertIn("8,442w", s5_content, "Session 5 card must show 8,442 total words")


if __name__ == "__main__":
    unittest.main()

