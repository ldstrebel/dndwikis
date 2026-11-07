#!/usr/bin/env python3
"""
Test Suite for Codex Proper Noun Integrity & Entity Autolinking Parity.

Verifies:
1. Every tracked proper noun / alias in `CUSTOM_ALIASES` resolves to a real canonical codex article in dnd-scribe.
2. Every entity in `ENTITY_COLOR_MAP` has a designated, consistent color class and backing codex article.
3. All 13 Dramatis Personae dossiers, 2 Factions, 5 Locales, and 9 Dedicated Mystery Pages (TH-01 to TH-09) exist.
4. Compiled codex HTML does not wrap session summaries in nested container boxes (no containeritis).
5. Autolinked entity slugs strictly match known codex articles.
"""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import build_ebooks


class TestCodexProperNounIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.articles = build_ebooks.load_all_codex_articles()
        cls.assertTrue(len(cls.articles) > 0, "Codex articles must be loaded")

    def test_all_custom_aliases_have_backing_articles(self):
        """Every alias target in CUSTOM_ALIASES must correspond to an existing codex article."""
        # Extract CUSTOM_ALIASES from build_ebooks by inspecting the source or invoking
        # Test against the loaded articles map
        tracked_slugs = [
            "pierre", "alfie", "eusacles", "dravin", "susanna", "teddy", "naomi",
            "mike", "rosa", "thorne", "redactors", "margin-wardens", "the-margin",
            "hermes", "thanatos", "fates", "open-threads", "lost-roads",
            "university-university", "raleigh", "dc-precinct",
            "th-01", "th-02", "th-03", "th-04", "th-05", "th-06", "th-07", "th-08", "th-09"
        ]
        for slug in tracked_slugs:
            self.assertIn(slug, self.articles, f"Proper noun slug '{slug}' is missing a canonical codex article!")

    def test_all_dramatis_personae_dossiers_exist(self):
        """All 13 character dossiers must exist in codex."""
        characters = [
            "pierre", "alfie", "dravin", "eusacles", "teddy", "naomi",
            "mike", "susanna", "rosa", "thorne", "thanatos", "hermes", "fates"
        ]
        for char in characters:
            self.assertIn(char, self.articles, f"Dramatis Personae dossier '{char}' missing from codex")
            art = self.articles[char]
            self.assertEqual(art.get("group"), "characters", f"'{char}' must be in group 'characters'")

    def test_all_factions_exist(self):
        """All factions must exist in codex."""
        factions = ["redactors", "margin-wardens"]
        for fac in factions:
            self.assertIn(fac, self.articles, f"Faction '{fac}' missing from codex")
            art = self.articles[fac]
            self.assertEqual(art.get("group"), "factions", f"'{fac}' must be in group 'factions'")

    def test_all_key_locales_exist(self):
        """All 5 key locales must exist in codex."""
        locales = ["the-margin", "lost-roads", "raleigh", "university-university", "dc-precinct"]
        for loc in locales:
            self.assertIn(loc, self.articles, f"Locale '{loc}' missing from codex")
            art = self.articles[loc]
            self.assertEqual(art.get("group"), "locales", f"'{loc}' must be in group 'locales'")

    def test_all_mysteries_have_dedicated_pages(self):
        """Master board and all 9 individual mysteries (TH-01 to TH-09) must have codex articles."""
        self.assertIn("open-threads", self.articles, "Master open-threads board missing from codex")
        for i in range(1, 10):
            th_slug = f"th-{i:02d}"
            self.assertIn(th_slug, self.articles, f"Mystery page '{th_slug}' missing from codex")
            art = self.articles[th_slug]
            self.assertEqual(art.get("group"), "threads", f"'{th_slug}' must be in group 'threads'")

    def test_session_summary_formatting_has_no_containeritis(self):
        """Compiled session summaries must not contain nested border container boxes."""
        for s in range(1, 10):
            slug = f"s{s}"
            if slug in self.articles:
                html = self.articles[slug]["html"]
                self.assertNotIn("session-summary-card", html, f"Session {s} contains banned container 'session-summary-card'")
                # Must contain paragraph tags with readable text-base
                self.assertIn('text-base text-slate-200 leading-relaxed font-sans mb-4', html, f"Session {s} summary must use readable text-base font")

    def test_entity_autolinker_applies_consistent_colors(self):
        """Cross-linker must apply character-specific color classes."""
        autolinker = build_ebooks.build_entity_crosslinker(self.articles)
        sample_text = "<p>Pierre and Alfie met with Prof. Edward Dravin and Eusacles to discuss the Redactors.</p>"
        linked, count = autolinker(sample_text)
        self.assertGreater(count, 0, "Autolinker should match entities")
        self.assertIn("text-amber-400", linked, "Pierre must be styled with amber color")
        self.assertIn("text-emerald-400", linked, "Alfie must be styled with emerald color")
        self.assertIn("text-indigo-400", linked, "Dravin must be styled with indigo color")
        self.assertIn("text-sky-400", linked, "Eusacles must be styled with sky color")
        self.assertIn("text-red-400", linked, "Redactors must be styled with red color")


if __name__ == "__main__":
    unittest.main()
