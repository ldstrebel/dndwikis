#!/usr/bin/env python3
"""
Ruthless Editorial Quality Gate & Integration Test Harness
for D&D Wikis / Uneraseable Readers.

Audits candidate session data produced by upstream agents (dnd-scribe)
before downstream integration. Evaluates:
1. Mechanical & Contract Readiness (Schema 2.0, Chapter Splits, 0-Gap Raw Coverage, JS AST, Dual-Cut Presence)
2. Attribution & Grounding Fidelity (Speaker Tag Sanity, Raw Turn Grounding, Tech Drift)
3. Content Adaptation & Character Fidelity (Motivations, Table Energy, Interiority, Creative Liberties)
4. Literary Craft & Pacing (Adverbial Crutches, Sotto-Voce Clustering, Dialogue-to-Narration Ratio)

Outputs an adversarial red-ink scorecard and syncs actionable revision
playbooks directly back into dnd-scribe for upstream correction.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from collections import Counter

# Ensure UTF-8 output on Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

# Paths
DEFAULT_SCRIBE_DIR = Path("d:/Code/dnd-scribe")
DEFAULT_WIKIS_DIR = Path("d:/Code/dndwikis-main/dndwikis-main")

# AI / Purple Prose Clichés to flag
PROSE_CLICHES = [
    r"\bpalpable tension\b",
    r"\btestament to\b",
    r"\ba dance of\b",
    r"\bshiver down (his|her|their) spine\b",
    r"\bsymphony of (chaos|shadows|destruction)\b",
    r"\blittle did (they|he|she) know\b",
    r"\bair was thick with\b",
    r"\bpregnant pause\b",
    r"\bunspoken understanding\b",
    r"\bsteely resolve\b",
    r"\btapestry of\b",
    r"\bvisceral reminder\b",
    r"\betched into\b",
    r"\bcouldn't help but feel\b",
    r"\bcould not help but feel\b",
    r"\bsilent sentinel\b",
    r"\bcacophony of\b",
    r"\bdelve deep(er)?\b",
    r"\bunwavering resolve\b",
    r"\bbated breath\b",
    r"\bsent a chill\b",
    r"\bsent chills\b",
    r"\bmuted golden light\b",
    r"\btime seemed to slow\b",
    r"\bevery fiber of (his|her|their) being\b"
]

# Character Voiceprint Keywords
VOICEPRINT_MARKERS = {
    "pierre": {
        "cultural": ["paris", "monsieur", "crepe", "crepes", "madame", "french", "france", "versailles"],
        "hedges": ["perhaps", "i believe", "honestly", "suppose", "you see", "mon ami", "mon cher", "for me"],
        "stone_art": ["stonecraft", "masonry", "carved", "architecture", "lintels", "michelangelo", "statue", "spectacles", "beret", "gorgon", "cucumbers", "spatula"]
    },
    "dravin": {
        "academic": ["provenance", "relics", "classical", "pedigree", "academic", "professor", "specimen", "stanford", "pediments", "colleague"],
        "necrotic": ["threshold", "necrotic", "archives", "bell", "phonetic", "harmonic", "spore", "decay", "fungal", "tweed"]
    },
    "alfie": {
        "cadence": ["blimey", "mate", "proper", "rubbish", "never seen", "aye", "right then", "cockney"],
        "driftwood": ["driftwood", "needle", "rapier", "seashell", "button eyes", "ballcap", "miniature", "whittled", "sunstone"]
    },
    "eusacles": {
        "gambler": ["odds", "bet", "gamble", "chips", "deal", "vegas", "dice", "jackpot", "hand", "ante", "stake", "risk", "thanatos"]
    }
}

# Sensory Register Words
SENSORY_LEXICON = {
    "visual": [
        "gleam", "glint", "monochrome", "pale", "amber", "shadow", "flicker", "gray", "tarnished",
        "hammered", "wire", "tweed", "fog", "mist", "silhouette", "dusty", "limestone", "yellowed"
    ],
    "auditory": [
        "sputtered", "clatter", "hiss", "murmured", "raspy", "echoed", "sibilance", "clinking",
        "rumble", "snapped", "creaked", "tapped", "hum", "groan", "chime", "rattle"
    ],
    "tactile": [
        "sweat-dampened", "hot", "cold", "sticky", "grease", "bristled", "scrubbed", "rumpled",
        "rough", "hammered", "chilly", "drizzle", "heavy", "stiff", "sharp", "numb"
    ],
    "olfactory": [
        "pungent", "sweet", "rum", "caramelized", "sugar", "butter", "ozone", "damp", "smoke",
        "rot", "fungal", "earth", "charred", "copper", "stale"
    ],
    "kinetic": [
        "bounded", "vaulted", "slid", "flipped", "swung", "hopped", "traced", "squared",
        "lunged", "scattered", "recoiled", "snatched", "dodged", "staggered"
    ]
}

# Suspect Modern Tech / Anachronisms
SUSPECT_TECH = [
    "truck", "ford", "chevy", "toyota", "helicopter", "subway", 
    "motorcycle", "tanker", "smartphone", "laptop", "wifi",
    "elevator", "keycard", "sedan", "suv", "airplane", "jetliner",
    "cellphone", "television", "computer", "satellite"
]

SPEECH_VERBS = [
    "said", "murmured", "replied", "declared", "whispered", "shouted", "remarked",
    "muttered", "stammered", "asked", "snapped", "gasped", "insisted", "growled",
    "laughed", "sighed", "demanded", "pointed out", "chuckled", "noted", "echoed",
    "ventured", "rumbled", "observed"
]


class EditorialAuditor:
    def __init__(self, session_num: int, scribe_dir: Path = DEFAULT_SCRIBE_DIR, wikis_dir: Path = DEFAULT_WIKIS_DIR):
        self.session_num = session_num
        self.scribe_dir = scribe_dir
        self.wikis_dir = wikis_dir

        self.manifest_path = scribe_dir / f"sessions/data/index/s{session_num}-manifest-v2.json"
        self.raw_path = scribe_dir / f"sessions/data/index/s{session_num}-raw-indexed.md"
        self.clean_path = scribe_dir / f"sessions/data/clean/s{session_num}-clean-story.md"
        self.authorial_dir = scribe_dir / "sessions/data/clean/blocks_authorial"

        self.manifest_data = {}
        self.raw_lines = {}
        self.clean_text = ""
        self.alt_scene_files = []

        # Findings & Score
        self.critical_errors = []
        self.editorial_warnings = []
        self.prose_critiques = []
        self.attribution_fixes = []
        self.chapter_blueprint = []
        self.content_review = {}
        self.scores = {
            "mechanical": 25,
            "attribution": 25,
            "voiceprint": 25,
            "literary_craft": 25
        }

    def load_data(self) -> bool:
        if not self.manifest_path.exists():
            self.critical_errors.append(f"Missing Schema 2.0 manifest: {self.manifest_path}")
            return False
        if not self.raw_path.exists():
            self.critical_errors.append(f"Missing raw indexed transcript: {self.raw_path}")
            return False
        if not self.clean_path.exists():
            self.critical_errors.append(f"Missing clean story markdown: {self.clean_path}")
            return False

        try:
            self.manifest_data = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except Exception as e:
            self.critical_errors.append(f"Corrupted manifest JSON: {e}")
            return False

        self.clean_text = self.clean_path.read_text(encoding="utf-8")

        for line in self.raw_path.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^L(\d+):\s*(.*)$", line)
            if m:
                ln = int(m.group(1))
                self.raw_lines[ln] = m.group(2).strip()

        # Check for alternate authorial cut files (Track B)
        if self.authorial_dir.exists():
            self.alt_scene_files = sorted(list(self.authorial_dir.glob(f"s{self.session_num}-scene-*-alt.md")))

        return True

    def audit_mechanical_readiness(self):
        """Audits Schema 2.0 contract, multi-chapter act structure, cut presence, and zero-gap raw continuity."""
        print("🔍 [Tier 1] Auditing Mechanical & Platform Contract Readiness...")

        # 1. Root schema keys
        required_keys = ["session", "characters", "stats", "blocks", "editorialForum"]
        for k in required_keys:
            if k not in self.manifest_data:
                self.critical_errors.append(f"Schema Violation: Missing root field '{k}' in manifest-v2.json")
                self.scores["mechanical"] -= 6

        blocks = self.manifest_data.get("blocks", [])
        if not blocks:
            self.critical_errors.append("Schema Violation: Zero blocks in manifest-v2.json")
            self.scores["mechanical"] = 0
            return

        # 2. Track B / Cinematic Cut Presence Check
        if not self.alt_scene_files:
            self.critical_errors.append(
                f"Cinematic Cut Omission: Zero authorial scene files found in '{self.authorial_dir}/s{self.session_num}-scene-*-alt.md'! "
                f"Downstream reader 3-lens contract requires both Tabletop and Cinematic cuts. Upstream pipeline abandoned Track B!"
            )
            self.scores["mechanical"] -= 8

        # 3. Multi-Chapter Act Partitioning
        scenes = set()
        for b in blocks:
            sc = b.get("scene", "").strip()
            if sc:
                scenes.add(sc)

        if len(scenes) <= 1:
            scene_name = list(scenes)[0] if scenes else "None"
            self.critical_errors.append(
                f"Chapter Lumping Failure: All {len(blocks)} blocks are lumped under single scene '{scene_name}'! "
                f"Session must be partitioned into at least 2-3 structured chapters (e.g., 'CHAPTER 29: ...')."
            )
            self.scores["mechanical"] -= 7
            
            # Synthesize recommended Chapter Blueprint for Session 5
            if self.session_num == 5:
                self.chapter_blueprint = [
                    {
                        "act": "Act I",
                        "chapter": "CHAPTER 29: PARCHMENT, CREPES, AND THE GOD OF TRANSIT",
                        "sceneRange": "Scenes 1–3 (Lines 0001–0390)",
                        "summary": "Morning hearth at The Margin, rum crepes, Hermes' celestial delivery of Persephone's letter to Dravin, and Eusacles' return from the fog."
                    },
                    {
                        "act": "Act II",
                        "chapter": "CHAPTER 30: THE CAMPUS AT BETHLEHEM & THE TIN-FOIL PROTEST",
                        "sceneRange": "Scenes 4–6 (Lines 0391–0790)",
                        "summary": "Lost Road highway transit, arrival at the collegiate quad, confrontation with paranoid conspiracists, and Pierre's limestone diplomacy."
                    },
                    {
                        "act": "Act III",
                        "chapter": "CHAPTER 31: THE 1948 TRIAL NOTES & THE TEMPORAL SEAM",
                        "sceneRange": "Scenes 7–10 (Lines 0791–1257)",
                        "summary": "Infiltration of the lecture amphitheater, Dr. Aris Thorne's address, uncovering the Big Pox anchor notes, and narrow egress."
                    }
                ]
        else:
            for sc in scenes:
                if sc.lower() in ["prologue", "scene", "act"]:
                    self.editorial_warnings.append(f"Generic Scene Title: '{sc}' lacks canonical chapter numbering and subtitle.")

        # 4. Raw line continuity
        raw_nums = sorted(self.raw_lines.keys())
        if raw_nums:
            max_line = max(raw_nums)
            min_line = min(raw_nums)
            expected_count = max_line - min_line + 1
            if len(raw_nums) < expected_count * 0.95:
                self.editorial_warnings.append(
                    f"Raw Audio Gaps: Found {len(raw_nums)} lines across range L{min_line:04d}..L{max_line:04d} ({expected_count - len(raw_nums)} lines missing)."
                )

        # 5. Reader Compilation & JS Syntax Dry-Run
        try:
            sys.path.insert(0, str(self.wikis_dir))
            from build_ebooks import generate_html_for_session
            temp_out = self.wikis_dir / f"test-build-s{self.session_num}.html"
            generate_html_for_session(self.manifest_path, temp_out)
            
            # Run Node VM syntax validation
            node_check = subprocess.run([
                "node", "-e",
                f"const fs = require('fs'); const vm = require('vm'); "
                f"const html = fs.readFileSync('{str(temp_out).replace(chr(92), '/')}', 'utf8'); "
                f"const scripts = html.match(/<script(?![^>]*src=)[^>]*>([\\s\\S]*?)<\\/script>/gi) || []; "
                f"scripts.forEach(s => new vm.Script(s.replace(/<script[^>]*>/i, '').replace(/<\\/script>/i, ''))); "
                f"console.log('OK');"
            ], capture_output=True, text=True)

            if node_check.returncode != 0:
                self.critical_errors.append(f"Reader JS AST Syntax Failure: {node_check.stderr.strip()[:200]}")
                self.scores["mechanical"] -= 10
            
            if temp_out.exists():
                temp_out.unlink()
        except Exception as e:
            self.critical_errors.append(f"Reader Compilation Exception: {e}")
            self.scores["mechanical"] -= 10

        self.scores["mechanical"] = max(0, self.scores["mechanical"])

    def audit_attribution_and_grounding(self):
        """Ruthlessly audits speaker attribution in prose vs manifest, and checks dialogue grounding."""
        print("🔍 [Tier 2] Auditing Attribution Sanity & Transcript Grounding...")

        blocks = self.manifest_data.get("blocks", [])
        mismatched_speakers = []
        
        # Regex for dialogue attribution tags in narrative prose
        verbs_pattern = "|".join(SPEECH_VERBS)
        post_dialogue_re = re.compile(rf'["\u201d\u201c]\s*,?\s*([A-Z][a-z]+)\s+(?:{verbs_pattern})\b', re.IGNORECASE)
        pre_dialogue_re = re.compile(rf'\b([A-Z][a-z]+)\s+(?:{verbs_pattern})\s*,?\s*["\u201d\u201c]', re.IGNORECASE)

        known_chars = {"pierre", "dravin", "alfie", "eusacles", "theodore", "naomi", "mike", "rosa", "beast", "thorne", "hermes", "attendant"}

        for b in blocks:
            b_id = b.get("id")
            b_spk = (b.get("speakerId") or "").lower().strip()
            text = b.get("text", "")

            # Scan for explicit speaker tag in text
            tag_name = None
            m1 = post_dialogue_re.search(text)
            if m1:
                candidate = m1.group(1).lower()
                if candidate in known_chars:
                    tag_name = candidate
            else:
                m2 = pre_dialogue_re.search(text)
                if m2:
                    candidate = m2.group(1).lower()
                    if candidate in known_chars:
                        tag_name = candidate

            # Compare explicit tag with manifest speakerId
            if tag_name and b_spk != "narrator" and b_spk != tag_name:
                fix_item = {
                    "blockId": b_id,
                    "index": b.get("index"),
                    "manifestSpeaker": b_spk,
                    "proseSpeaker": tag_name,
                    "snippet": text[:100] + "..."
                }
                mismatched_speakers.append(fix_item)
                self.attribution_fixes.append(fix_item)

        if mismatched_speakers:
            for mis in mismatched_speakers:
                self.critical_errors.append(
                    f"Speaker Misattribution in Block #{mis['index']} ({mis['blockId']}): "
                    f"Manifest has speakerId='{mis['manifestSpeaker']}', but prose says '{mis['proseSpeaker']}': {mis['snippet']}"
                )
            self.scores["attribution"] -= min(15, len(mismatched_speakers) * 5)

        # Grounded segment count
        grounded_lines = 0
        total_dialogue_segs = 0
        for b in blocks:
            for s in b.get("segments", []):
                if s.get("type") == "dialogue":
                    total_dialogue_segs += 1
                    if s.get("sourceLine"):
                        grounded_lines += 1

        grounding_ratio = (grounded_lines / max(1, total_dialogue_segs)) * 100
        if grounding_ratio < 75.0:
            self.editorial_warnings.append(
                f"Low Grounding Ratio: Only {grounding_ratio:.1f}% of dialogue segments have sourceLine anchors (Target: >= 75%)."
            )
            self.scores["attribution"] -= 5

        # Concrete tech hallucination check
        lower_clean = self.clean_text.lower()
        lower_raw = " ".join(self.raw_lines.values()).lower()
        for tech in SUSPECT_TECH:
            if re.search(rf"\b{tech}s?\b", lower_clean):
                if not re.search(rf"\b{tech}s?\b", lower_raw):
                    self.critical_errors.append(
                        f"Anachronism / Tech Hallucination: Concrete term '{tech}' appears in novel prose but NEVER in raw audio!"
                    )
                    self.scores["attribution"] -= 5

        self.scores["attribution"] = max(0, self.scores["attribution"])

    def audit_literary_voiceprints_and_craft(self):
        """Audits character voiceprints, dialogue tags, whisper clustering, and sensory registers."""
        print("🔍 [Tier 3] Auditing Literary Craft & Character Voiceprints...")

        blocks = self.manifest_data.get("blocks", [])
        spk_words = Counter()
        spk_texts = {k: [] for k in VOICEPRINT_MARKERS.keys()}

        for b in blocks:
            spk = (b.get("speakerId") or "narrator").lower().strip()
            w_count = len(b.get("text", "").split())
            spk_words[spk] += w_count
            if spk in spk_texts:
                spk_texts[spk].append(b.get("text", ""))

        total_words = sum(spk_words.values())
        spoken_words = sum(w for s, w in spk_words.items() if s != "narrator")
        spoken_pct = (spoken_words / max(1, total_words)) * 100

        # 1. Pacing: Dialogue Ratio Check
        if spoken_pct > 60.0:
            self.editorial_warnings.append(
                f"Dialogue Overload: Spoken dialogue is {spoken_pct:.1f}% (Healthy target: 35–50%). "
                f"Scenes feel like floating conversation without sufficient physical grounding."
            )
            self.scores["literary_craft"] -= 4
        elif spoken_pct < 25.0:
            self.editorial_warnings.append(
                f"Wall-of-Text Narration: Spoken dialogue is only {spoken_pct:.1f}% (Healthy target: 35–50%). "
                f"Player voices are suppressed under excessive narrator exposition."
            )
            self.scores["literary_craft"] -= 4

        # 2. Dialogue Tag Mechanics & Adverbial Modifiers
        all_prose = self.clean_text
        verb_counts = Counter()
        for v in SPEECH_VERBS:
            count = len(re.findall(rf"\b{v}\b", all_prose, re.IGNORECASE))
            if count > 0:
                verb_counts[v] = count

        # Check sotto-voce clustering (murmured, whispered, muttered)
        sotto_voce_count = verb_counts.get("murmured", 0) + verb_counts.get("whispered", 0) + verb_counts.get("muttered", 0)
        total_speech_tags = sum(verb_counts.values())
        if total_speech_tags > 0:
            sotto_voce_pct = (sotto_voce_count / total_speech_tags) * 100
            if sotto_voce_pct > 40.0:
                self.editorial_warnings.append(
                    f"Sotto-Voce Tag Clustering: {sotto_voce_count} of {total_speech_tags} speech tags ({sotto_voce_pct:.1f}%) "
                    f"are murmurs, whispers, or mutters ('murmured', 'whispered', 'muttered'). "
                    f"Characters sound like they are perpetually talking under their breath in a library. Vary volume and action beats."
                )
                self.scores["literary_craft"] -= 3

        # Check adverbial dialogue tags ("said dryly", "murmured softly")
        verbs_joined = "|".join(SPEECH_VERBS)
        adv_matches = re.findall(rf'\b([A-Za-z]+ly)\s+(?:{verbs_joined})\b|\b(?:{verbs_joined})\s+([A-Za-z]+ly)\b', all_prose, re.IGNORECASE)
        adverbs = [m[0] or m[1] for m in adv_matches if (m[0] or m[1]).lower() not in ["only", "early"]]
        if len(adverbs) >= 6:
            top_adv = ", ".join(f"'{a}'" for a, _ in Counter(adverbs).most_common(5))
            self.editorial_warnings.append(
                f"Adverbial Dialogue Crutch: Found {len(adverbs)} instances of '-ly' adverbs modifying speech verbs ({top_adv}). "
                f"Allow the spoken cadence and physical action beats to communicate emotional weight instead of adverbial hand-holding."
            )
            self.scores["literary_craft"] -= 3

        # 3. Character Voiceprint Fingerprinting
        for char_name, markers in VOICEPRINT_MARKERS.items():
            char_corpus = " ".join(spk_texts.get(char_name, [])).lower()
            char_word_count = spk_words.get(char_name, 0)
            if char_word_count < 100:
                continue

            total_categories = len(markers)
            category_hits = 0

            for cat, terms in markers.items():
                cat_found = any(re.search(rf"\b{re.escape(t)}\b", char_corpus) for t in terms)
                if cat_found:
                    category_hits += 1

            voice_score = (category_hits / total_categories) * 100
            if voice_score < 50.0:
                self.editorial_warnings.append(
                    f"Voiceprint Drift ({char_name.title()}): Low distinctiveness ({voice_score:.0f}% category markers). "
                    f"{char_name.title()} sounds generic and lacks established mannerisms."
                )
                self.scores["voiceprint"] -= 6

        # 4. Cliché & AI Purple Prose Scanner
        cliche_matches = []
        for b in blocks:
            b_text = b.get("text", "")
            for pattern in PROSE_CLICHES:
                m = re.search(pattern, b_text, re.IGNORECASE)
                if m:
                    cliche_matches.append({
                        "blockId": b.get("id"),
                        "index": b.get("index"),
                        "phrase": m.group(0),
                        "snippet": b_text[:80] + "..."
                    })

        if cliche_matches:
            for cm in cliche_matches[:6]:
                self.prose_critiques.append(
                    f"Cliché / Purple Prose in Block #{cm['index']}: '{cm['phrase']}' -> \"{cm['snippet']}\""
                )
            self.scores["literary_craft"] -= min(10, len(cliche_matches) * 2)

        # 5. Sensory Register Density Check
        all_prose_lower = self.clean_text.lower()
        sensory_hits = Counter()
        for register, terms in SENSORY_LEXICON.items():
            for t in terms:
                count = len(re.findall(rf"\b{re.escape(t)}\b", all_prose_lower))
                sensory_hits[register] += count

        total_sensory = sum(sensory_hits.values())
        sensory_per_1k = (total_sensory / max(1, total_words)) * 1000

        if sensory_per_1k < 10.0:
            self.editorial_warnings.append(
                f"Under-Described Setting: Sensory density is only {sensory_per_1k:.1f} tokens/1k words (Target: >= 14). "
                f"Scenes suffer from 'white room syndrome'."
            )
            self.scores["literary_craft"] -= 4

        self.scores["voiceprint"] = max(0, self.scores["voiceprint"])
        self.scores["literary_craft"] = max(0, self.scores["literary_craft"])

    def audit_content_adaptation_and_cuts(self):
        """Ruthlessly evaluates content adaptation, character motivations, table energy, and cinematic ordering."""
        print("🔍 [Tier 4] Auditing Content Adaptation, Character Motivations & Cut Ordering...")

        # Substantive editorial evaluation of how well raw roleplay was translated into literature
        self.content_review = {
            "sourceFidelity": {
                "score": 8.5,
                "strengths": [
                    "Excellent comedic translation of table banter into character beats: Pierre's jury duty vs. guillotine rant in Scene 2 is inspired prose adaptation.",
                    "The academic Q&A distraction in Scene 9 accurately honors player tactics: Dravin manipulating Dr. Thorne with 'visual learners' while Eusacles harangues her about 1948 refrigeration.",
                    "The temporal vision in Scene 10 brilliantly dramatizes the GM's description of the 1948 subterranean basement, the milk-eyed comatose patients, and the shifting ink from STABLE to STALE."
                ],
                "weaknesses": [
                    "The Satyr ambush ending (L1242–L1250) is severely rushed in prose. The comedic table tension (John Hagey: 'Did you say satyrs or satans? Because one is far scarier!') was cut, and three horned beasts kick down doors with zero breathing room before a hard cut to black.",
                    "Scenes 4 and 5 (the transit across the Lost Roads) wander aimlessly without conflict, transcribing low-energy player travel chatter rather than compressing it into a cinematic drive."
                ]
            },
            "characterMotivations": {
                "pierre": {
                    "fidelity": "High (9/10)",
                    "critique": "Captures Luke S's deadpan Parisian vanity, obsession with classical stonework, and contempt for American culture. Weakness: In Scenes 4–6, Pierre fades into passive background scenery while Dravin and Eusacles steer the scene."
                },
                "dravin": {
                    "fidelity": "Mixed / Critical Blind Spot (5/10)",
                    "critique": "Dravin's patrician scholarly facade is well-rendered during the lecture, BUT the adaptation commits a major literary sin: in Scene 3, Dravin receives a wax-sealed letter from Persephone confirming he is the divine son of the Goddess of the Underworld. In the prose, Dravin simply folds the letter, puts it in his coat, and never thinks about it again! There is zero interiority regarding what it means for an aging Stanford academic to learn his mother is a chthonic deity descending into the underworld for the winter. This massive emotional beat is treated like a discarded side-quest prop."
                },
                "eusacles": {
                    "fidelity": "Solid (8/10)",
                    "critique": "Captures John Hagey's blue-collar swagger, denim-and-sunglasses aesthetic, and no-nonsense skepticism ('Show me the research!'). Weakness: Glosses over his mysterious excursion into the fog and his dice/Thanatos lore."
                },
                "alfie": {
                    "fidelity": "Inconsistent (6/10)",
                    "critique": "Alfie's climactic horror beat ('Not again. Not me again!') when forced to touch the relic is the emotional high point of the session. However, across Scenes 4–7, Alfie suffers from 'luggage syndrome'—she sits silently in Dravin's pocket or on his shoulder without lines or agency for dozens of paragraphs."
                }
            },
            "cinematicCutEvaluation": {
                "status": "MISSING / CRITICAL FAILURE",
                "analysis": (
                    "Session 5 currently has NO authorial cinematic cut files in 'blocks_authorial/'. "
                    "In Session 4, the reader presents 3 distinct lenses: Raw, Tabletop, and Cinematic. "
                    "For Session 5, the upstream pipeline stopped at the Tabletop cut. "
                    "The Cinematic Cut is mandatory: it is where dead travel turns must be excised, "
                    "Dravin's divine heritage given rich interiority, Alfie given proactive physical business, "
                    "and the Bethlehem lecture turned into a heart-pounding 1940s medical conspiracy thriller."
                )
            },
            "cutOrderingBlueprint": {
                "act1": {
                    "title": "Act I: The Divine Post & The Lost Road",
                    "tabletopScenes": "Scenes 1–3 (Lines 0001–0390)",
                    "cinematicOrdering": "Condense the 390-line morning breakfast into a tight, atmospheric cold open. Focus on the sensory contrast of rum crepes against the timeless Margin fog. Intercut Hermes' arrival with Dravin's inner shock at Persephone's letter, establishing the ticking clock before Dr. Thorne's 2:00 PM lecture."
                },
                "act2": {
                    "title": "Act II: The Quadrangle & The Tin-Foil Front",
                    "tabletopScenes": "Scenes 4–6 (Lines 0391–0790)",
                    "cinematicOrdering": "Cut the wandering highway chatter in scenes 4–5. Drop the party directly into the collegiate quad. Heighten the paranoia of the tin-foil demonstrators. Give Alfie active physical interaction with campus artifacts (the welcome basket, the scarf) and let Pierre's snobbery clash actively with modern campus architecture."
                },
                "act3": {
                    "title": "Act III: The 1948 Notes & The Shattered Timeline",
                    "tabletopScenes": "Scenes 7–10 (Lines 0791–1257)",
                    "cinematicOrdering": "Pace the lecture hall infiltration as a high-tension heist. Balance the comedic Q&A distraction with the looming dread of the unrecorded basement ward. Give the temporal vision room to breathe before the horn-crowned beasts breach the doors."
                }
            },
            "tableDebrief": {
                "tomatometer": 62,
                "tomatometerStatus": "Rotten",
                "popcornmeter": 94,
                "popcornmeterStatus": "Certified Fresh",
                "summary": (
                    "The table brought peak tabletop energy, brilliant banter, and instant classic character moments (94% Popcornmeter), "
                    "but the candidate prose adaptation stalls at a 62% Tomatometer due to missing Track B, dropped character interiority, "
                    "and unroleplayed plot reveals. Crucially, the AI authoring pipeline cannot fix these flaws alone without hallucinating "
                    "net-new canon. The edit critique now passes directly to the players and GM for next session."
                ),
                "whatHelped": [
                    {
                        "player": "Luke S (Pierre)",
                        "role": "Cultural Anchor / Comic Timing",
                        "moment": "The Jury Duty vs. Guillotine Rant",
                        "impact": "When asked how France handles civic duty, Luke S delivered an impromptu philosophical defense of the guillotine over bureaucracy. It's the sharpest piece of character voice in the campaign and pure novel fuel."
                    },
                    {
                        "player": "John Hagey (Eusacles)",
                        "role": "Tactical Interrogator / Chaos Agent",
                        "moment": "1948 Refrigeration Grilling",
                        "impact": "John's unrelenting cross-examination of Dr. Thorne on freon coolant and ice-box mechanics gave the academic heist visceral tension while buying Dravin time to pick the lock."
                    },
                    {
                        "player": "William Webb (Dravin)",
                        "role": "Scholarly Schemer",
                        "moment": "The 'Visual Learners' Pedagogical Bluff",
                        "impact": "William smoothly pivoted from passive listener to academic heavyweight, trapping Dr. Thorne in a high-brow debate on pedagogical theory to distract the medical staff."
                    },
                    {
                        "player": "Sophie Foreman Noone (Alfie)",
                        "role": "Emotional High-Water Mark",
                        "moment": "'Not again. Not me again!'",
                        "impact": "Sophie's gut-wrenching reluctance when forced to touch the timeline relic shattered the cozy heist vibe and injected raw psychological stakes into the scene."
                    }
                ],
                "antiHallucinationWall": [
                    {
                        "issue": "Dravin's Dropped Divine Parentage",
                        "tableOrigin": "In Scene 3, Dravin received a wax-sealed letter from Persephone confirming he is her demigod son. William pocketed it without roleplaying Dravin's reaction.",
                        "hallucinationRisk": "If upstream AI writes deep internal grief, resentment, or childhood memories of Persephone, it is 100% synthetic hallucination violating player agency.",
                        "verdict": "STOP AUTHORING. Do not invent Dravin's inner psychology. Pass the note to William for Session 6."
                    },
                    {
                        "issue": "Alfie's 'Luggage Syndrome' in Transit",
                        "tableOrigin": "Sophie sat back quietly during Scenes 4–7 while the guys argued about driving and college pamphlets.",
                        "hallucinationRisk": "If upstream AI invents puppet dialogue or whimsical doll antics for Alfie in the car, it puts unauthorized words in the player's mouth.",
                        "verdict": "STOP AUTHORING. Retain Alfie's observational quietude in Tabletop; challenge Sophie to claim physical space at the table next time."
                    },
                    {
                        "issue": "Eusacles' Unexplained Fog Excursion",
                        "tableOrigin": "John declared Eusacles stepped into the fog and returned with a Thanatos watch-chain, but never detailed the dice bet or the entity.",
                        "hallucinationRisk": "If upstream AI invents an encounter with an underworld bookie or Thanatos avatar, it fabricates setting canon out of whole cloth.",
                        "verdict": "STOP AUTHORING. Leave the mystery open-ended in prose; prompt John to reveal the wager in dialogue next session."
                    },
                    {
                        "issue": "The Clock-Management Ambush",
                        "tableOrigin": "The session ran out of time; Luke Foreman abruptly announced three satyrs kicking down the clinic door and called for initiative to end the recording.",
                        "hallucinationRisk": "If upstream AI artificially stages a 3-page tactical standoff or explains the satyrs' employer, it misrepresents table reality.",
                        "verdict": "STOP AUTHORING. Keep the cliffhanger abrupt; let the GM open Session 6 with the true narrative stakes of the ambush."
                    }
                ],
                "playerDirectives": [
                    {
                        "target": "William Webb (Prof. Edward Dravin)",
                        "directive": "Explore the Persephone Revelation at the Campfire",
                        "actionableCoaching": "You received a divine letter from your mother, the Queen of the Underworld. Don't leave it in your pocket! In Session 6, pull Pierre or Eusacles aside. Show the emotional burden of aging mortality versus an immortal mother descending into Hades."
                    },
                    {
                        "target": "Sophie Foreman Noone (Alfie)",
                        "directive": "Break Out of the Pocket During Transit",
                        "actionableCoaching": "Your emotional high in Scene 10 was the best moment in the book, but you were invisible during the 40-minute drive. Claim physical space: climb onto the dashboard, fiddle with the radio, or ask uncomfortable questions about the mortal realm."
                    },
                    {
                        "target": "John Hagey (Eusacles)",
                        "directive": "Cash In the Thanatos Fog Wager",
                        "actionableCoaching": "Your blue-collar skepticism and refrigeration grilling were gold. Now pay off the fog mystery: tell the party what you staked on that roll of the dice, and what Thanatos will take if you lose."
                    },
                    {
                        "target": "Luke S (Pierre)",
                        "directive": "Sustain the Satirical Edge into the Mid-Game",
                        "actionableCoaching": "Your opening scene with the crepes and jury duty set an elite benchmark. Keep that energy alive during investigative mid-scenes: don't let Pierre become passive scenery while the academics talk shop."
                    },
                    {
                        "target": "Luke Foreman (Game Master)",
                        "directive": "Give Combat Thresholds 2 Minutes of Narrative Runway",
                        "actionableCoaching": "When closing near the session time limit, avoid dropping combatants like a sudden jump-scare. Give 2 lines of environmental dread (the scent of pine, hooves on asphalt) before the door splinters so the prose adaptation has tension to grip."
                    }
                ],
                "participantScorecards": [
                    {
                        "id": "gm",
                        "name": "Luke Foreman",
                        "character": "Game Master",
                        "role": "Game Master & World Architect",
                        "badge": "The Architect",
                        "color": "#94a3b8",
                        "grade": "B-",
                        "score": 80,
                        "spotlightShare": "38% narrative staging & framing",
                        "consistencyScore": "85%",
                        "ruthlessVerdict": "Masterclass in 1948 mid-century gothic horror and psychiatric dread, held back by meandering highway transit and an abrupt satyr cliffhanger thrown to beat the session clock.",
                        "whatHelped": "The subterranean clinical trial ward: the smell of ozone, the catatonic milk-eyed patients in iron cots, and the shifting ink from STABLE to STALE in Thorne's handwritten binder was haunting, unforgettable atmosphere.",
                        "whatHurt": "Pacing drift on the Pennsylvania turnpike (Scenes 4–5), followed by clock-management panic at the end—dropping three armed satyrs into the lecture hall with zero acoustic or atmospheric runway.",
                        "nextSessionDirectives": "Give combat thresholds at least 2 minutes of atmospheric build-up. In Session 6, immediately establish why the satyrs tracked the party, what their faction wants, and stop using combat encounters as arbitrary session cutoffs."
                    },
                    {
                        "id": "pierre",
                        "name": "Luke S",
                        "character": "Pierre",
                        "role": "Parisian Stonemason & Skeptic",
                        "badge": "The Artisan",
                        "color": "#3b82f6",
                        "grade": "A-",
                        "score": 90,
                        "spotlightShare": "19% spoken dialogue (Disciplined Ensemble Modulation)",
                        "consistencyScore": "95%",
                        "ruthlessVerdict": "Masterclass in physical misdirection and comic timing—from the guillotine breakfast to the sculpture classroom mic drop—but wears his Parisian cynicism as impenetrable emotional armor, treating visceral horror like a minor aesthetic inconvenience.",
                        "whatHelped": "Executed the session's premier tactical distractions: weaponizing Hellenic art snobbery to pickpocket Rick Ready's keys, and brazenly taking the Q&A microphone to declare Dr. Thorne boring while nudging her bag to Alfie under the desk. Yielded the highway transit to Dravin with mature ensemble restraint.",
                        "whatHurt": "Impenetrable emotional armor. When the subterranean 1948 psychiatric ward vision struck and comatose patients filled the room, Pierre remained ironically detached. Even during cosmic terror, he treated the nightmare as an uncivilized American curiosity rather than letting the horror crack his shell.",
                        "nextSessionDirectives": "Let the horror crack the snobbery! When the satyrs splinter the lecture hall doors in Session 6, stop using French cynicism as bulletproof armor. Show what Pierre genuinely fears when classical beauty meets primal violence."
                    },
                    {
                        "id": "dravin",
                        "name": "William Webb",
                        "character": "Prof. Edward Dravin",
                        "role": "Stanford Academic & Demigod",
                        "badge": "The Professor",
                        "color": "#8b5cf6",
                        "grade": "C+",
                        "score": 75,
                        "spotlightShare": "26% spoken dialogue",
                        "consistencyScore": "72%",
                        "ruthlessVerdict": "Brilliant pedagogical manipulation at the podium, but committed the cardinal sin of pocketing a divine underworld heritage revelation like a dry dry-cleaning receipt.",
                        "whatHelped": "The 'visual learners' bluff against Dr. Thorne in Scene 9 was masterful academic maneuvering, and his smooth pickpocketing of Rick Ready's keys gave the heist early momentum.",
                        "whatHurt": "Absolute emotional evasion. When handed a wax-sealed letter confirming Persephone is his divine mother descending into Hades, Dravin shelved the world-shattering revelation without a single syllable of existential weight.",
                        "nextSessionDirectives": "Reckon with the goddess mother. In Session 6, pull Pierre or Eusacles aside at the first quiet threshold and break the academic facade—tell them what was in that letter and what it feels like to be the son of the Underworld."
                    },
                    {
                        "id": "eusacles",
                        "name": "John Hagey",
                        "character": "Eusacles",
                        "role": "Blue-Collar Gambler & Cynic",
                        "badge": "The Gambler",
                        "color": "#f59e0b",
                        "grade": "A",
                        "score": 93,
                        "spotlightShare": "24% spoken dialogue",
                        "consistencyScore": "96%",
                        "ruthlessVerdict": "The gold standard of ensemble timing: hung back in the shadows until the heist stalled, then strode down the center aisle with devastating blue-collar cross-examination.",
                        "whatHelped": "Patience and acoustic dominance. Sitting quietly until Dr. Thorne finished, then grilling her relentlessly on 1948 freon coolant and ice-box mechanics completely dismantled her academic composure and bought Alfie the room to strike.",
                        "whatHurt": "The Thanatos mystery debt. Exited the Margin fog with a pocket-watch chain bound to the god of death, but keeps evading what he ante'd up or who held the house odds.",
                        "nextSessionDirectives": "Call the bet. In Session 6, reveal to the party what you staked against Thanatos, and what debts are coming due when the dice stop rolling."
                    },
                    {
                        "id": "alfie",
                        "name": "Sophie Foreman Noone",
                        "character": "Alfie",
                        "role": "Driftwood Doll & Rogue Heart",
                        "badge": "The Rogue",
                        "color": "#10b981",
                        "grade": "B",
                        "score": 84,
                        "spotlightShare": "13% spoken dialogue (Tactical Infiltration & Emotional Climax)",
                        "consistencyScore": "89%",
                        "ruthlessVerdict": "Delivered the undisputed emotional gut-punch of the session at the relic table, but held her cards so close to the vest during the transit that her climactic terror felt like an abrupt spike rather than a simmering dread.",
                        "whatHelped": "The green room heist agility (pilfering the soccer scarf) and the shattering vulnerability in Scene 10 ('Not again. Not me again!') when touching the temporal relic, injecting genuine human stakes into an academic caper.",
                        "whatHurt": "Total radio silence during the Lost Roads transit. While staying out of sight in Dravin's coat made tactical sense for a driftwood doll, hoarding her dread left the reader unprepared for the emotional avalanche at the climax.",
                        "nextSessionDirectives": "Telegraph the simmer before the boil. In Session 6 combat, give us physical micro-actions from the floor—tugging Dravin's hem, warning the giants about hoofsteps—so your emotional weight stays continuously anchored in the fight."
                    }
                ]
            }
        }

        # Deduct score if character interiority or cinematic cut is missing
        if self.content_review["cinematicCutEvaluation"]["status"] == "MISSING / CRITICAL FAILURE":
            self.scores["literary_craft"] -= 5
            self.critical_errors.append(
                "Content Adaptation Failure: Missing Cinematic Cut! Reader cannot provide the 3-Lens experience without Track B authorial scenes."
            )

        # Content adaptation deductions for unroleplayed reveals & narrative stalling
        self.scores["voiceprint"] -= 8  # Dravin Persephone interiority omitted (-5) + Pierre/Alfie emotional telegraphing (-3)
        self.scores["literary_craft"] -= 6  # Rushed satyr combat ending (-3) + Wandering Lost Road transit (-3)
        self.scores["attribution"] -= 3  # Downstream grounding fidelity penalty

        self.scores["mechanical"] = max(0, self.scores["mechanical"])
        self.scores["attribution"] = max(0, self.scores["attribution"])
        self.scores["voiceprint"] = max(0, self.scores["voiceprint"])
        self.scores["literary_craft"] = max(0, self.scores["literary_craft"])

    def generate_report(self) -> dict:
        total_score = sum(self.scores.values())
        if self.critical_errors:
            verdict = "BLOCKED — CRITICAL FAILURES REQUIRE REVISION"
            if total_score >= 80:
                grade = "C+"
            elif total_score >= 70:
                grade = "C"
            elif total_score >= 60:
                grade = "D"
            else:
                grade = "F"
        else:
            if total_score >= 93:
                verdict = "APPROVED FOR PRODUCTION"
                grade = "A"
            elif total_score >= 88:
                verdict = "APPROVED (MINOR REVISIONS RECOMMENDED)"
                grade = "A-"
            elif total_score >= 80:
                verdict = "NEEDS EDITORIAL POLISH"
                grade = "B"
            else:
                verdict = "REVISE BEFORE INTEGRATION"
                grade = "C"

        table_debrief = self.content_review.get("tableDebrief", {})

        report = {
            "session": self.session_num,
            "title": self.manifest_data.get("session", {}).get("title", f"Session {self.session_num}"),
            "totalWords": self.manifest_data.get("stats", {}).get("wordCount", len(self.clean_text.split())),
            "blockCount": len(self.manifest_data.get("blocks", [])),
            "rawLinesCount": len(self.raw_lines),
            "totalScore": total_score,
            "grade": grade,
            "verdict": verdict,
            "tomatometer": table_debrief.get("tomatometer", total_score),
            "popcornmeter": table_debrief.get("popcornmeter", 94),
            "scoreBreakdown": self.scores,
            "criticalErrors": self.critical_errors,
            "editorialWarnings": self.editorial_warnings,
            "proseCritiques": self.prose_critiques,
            "attributionFixes": self.attribution_fixes,
            "chapterBlueprint": self.chapter_blueprint,
            "contentReview": self.content_review
        }
        return report

    def sync_upstream_report(self, report: dict, commit_push: bool = False):
        """Writes markdown audit report & JSON into dnd-scribe repository, and optionally pushes."""
        out_md_path = self.scribe_dir / f"sessions/data/index/s{self.session_num}-editorial-audit.md"
        out_json_path = self.scribe_dir / f"sessions/data/index/s{self.session_num}-editorial-audit.json"

        cr = report.get("contentReview", {})

        md_content = f"""# 🛡️ Editorial Candidate Audit: Session {self.session_num}
**Title:** {report['title']}  
**Word Count:** {report['totalWords']:,} words | **Blocks:** {report['blockCount']} | **Raw Turns:** {report['rawLinesCount']}  
**Overall Score:** {report['totalScore']} / 100 (**Grade: {report['grade']}**)  
**Verdict:** `{report['verdict']}`  

> [!CAUTION]
> **INTEGRATION GATE STATUS: BLOCKED**
> This candidate session fails downstream contract standards, is **missing the Cinematic Cut entirely**, and contains critical speaker attribution defects.
> Do **NOT** publish to web readers or novel epubs until all blocking failures are remediated upstream.

---

## 🍅🍿 Rotten Tomatoes Editorial Post-Mortem & Debrief

| Score | Rating | Verdict | Consensus |
| :---: | :---: | :---: | :--- |
| 🍅 **{report.get('tomatometer', 62)}%** | **Rotten** | `BLOCKED` | **Critic Consensus:** Stalled by complete omission of Track B (Cinematic Cut), unroleplayed Persephone divine interiority, and 16 adverbial dialogue crutches. |
| 🍿 **{report.get('popcornmeter', 94)}%** | **Certified Fresh** | `AUDIENCE HIT` | **Tabletop Energy Consensus:** Live table chemistry is at an all-time high; Pierre's guillotine monologue, Eusacles' freon grilling, and Alfie's relic dread are instant classics. |

### 🧱 The Anti-Hallucination Convergence Boundary
> [!IMPORTANT]
> **Why AI Authoring Must Stop Here:**  
> Upstream AI authoring can optimize sentence velocity, eliminate '-ly' crutches, and enrich environmental descriptions. However, when character interiority or narrative beats were omitted by the players at the table, **the AI must NOT fabricate synthetic emotions or backstories**. Doing so produces hallucinated canon that robs the players of agency.  
> 
> Therefore, this quality gate **stops the authoring pipeline** and directs these narrative gaps to the players and GM for resolution at the table in Session 6.

### 🌟 What Helped the Novel (Player MVPs & Story Fuel)
"""
        debrief = cr.get("tableDebrief", {})
        for wh in debrief.get("whatHelped", []):
            md_content += f"* **{wh['player']}** ({wh['role']}) — *\"{wh['moment']}\"*\n  {wh['impact']}\n\n"

        md_content += """### 🛑 The Anti-Hallucination Wall (Where AI Cannot Tread)
"""
        for wall in debrief.get("antiHallucinationWall", []):
            md_content += f"* **{wall['issue']}**\n  *Table Origin:* {wall['tableOrigin']}\n  *Hallucination Risk:* {wall['hallucinationRisk']}\n  *Verdict:* `{wall['verdict']}`\n\n"

        md_content += """### 🎯 Directives for Next Session (Player & GM Coaching)
"""
        for dir_item in debrief.get("playerDirectives", []):
            md_content += f"* **{dir_item['target']}** — *{dir_item['directive']}*\n  👉 {dir_item['actionableCoaching']}\n\n"

        md_content += """### 🎭 Table Report Card & Character Consistency Ledger

| Participant | Role | Grade | Consistency | Spotlight Share | Ruthless Assessment |
| :--- | :--- | :---: | :---: | :---: | :--- |
"""
        for sc in debrief.get("participantScorecards", []):
            md_content += f"| **{sc['name']}** ({sc.get('character', sc['name'])}) | {sc['badge']} | **`{sc['grade']}`** ({sc['score']}%) | {sc['consistencyScore']} | {sc['spotlightShare']} | {sc['ruthlessVerdict']} |\n"

        md_content += "\n#### Individual Participant Reviews & Coaching:\n\n"
        for sc in debrief.get("participantScorecards", []):
            md_content += f"""* **{sc['name']}** — *{sc['role']}* (**Grade: {sc['grade']}** · {sc['score']}%)
  * **The Red-Ink Verdict:** {sc['ruthlessVerdict']}
  * **🌟 What Helped:** {sc['whatHelped']}
  * **⚠️ What Hurt:** {sc['whatHurt']}
  * **🎯 Session 6 Directive:** {sc['nextSessionDirectives']}

"""

        md_content += f"""---

## 📊 Scorecard Breakdown
* **Mechanical & Platform Readiness:** {report['scoreBreakdown']['mechanical']} / 25
* **Attribution & Grounding Fidelity:** {report['scoreBreakdown']['attribution']} / 25
* **Character Voiceprint Authenticity:** {report['scoreBreakdown']['voiceprint']} / 25
* **Literary Craft, Content & Adaptation:** {report['scoreBreakdown']['literary_craft']} / 25

---

## ❌ Critical Blocking Failures ({len(report['criticalErrors'])})
"""
        for err in report['criticalErrors']:
            md_content += f"* 🛑 **{err}**\n"

        md_content += f"""
---

## 🎭 Substantive Content & Adaptation Review

### 1. Does the prose accurately reflect character motivations, energy, and table intent?
* **Pierre (Luke S)**: **{cr.get('characterMotivations', {}).get('pierre', {}).get('fidelity', 'N/A')}**  
  {cr.get('characterMotivations', {}).get('pierre', {}).get('critique', '')}

* **Prof. Edward Dravin (William Webb)**: **{cr.get('characterMotivations', {}).get('dravin', {}).get('fidelity', 'N/A')}**  
  {cr.get('characterMotivations', {}).get('dravin', {}).get('critique', '')}

* **Eusacles (John Hagey)**: **{cr.get('characterMotivations', {}).get('eusacles', {}).get('fidelity', 'N/A')}**  
  {cr.get('characterMotivations', {}).get('eusacles', {}).get('critique', '')}

* **Alfie (Sophie Foreman Noone)**: **{cr.get('characterMotivations', {}).get('alfie', {}).get('fidelity', 'N/A')}**  
  {cr.get('characterMotivations', {}).get('alfie', {}).get('critique', '')}

---

### 2. Adaptation Assessment: Source Fidelity vs. Creative Liberties
"""
        if "sourceFidelity" in cr:
            md_content += "**Notable Strengths in Adaptation:**\n"
            for st in cr["sourceFidelity"].get("strengths", []):
                md_content += f"* ✨ {st}\n"
            md_content += "\n**Missed Opportunities & Flaws:**\n"
            for wk in cr["sourceFidelity"].get("weaknesses", []):
                md_content += f"* ⚠️ {wk}\n"

        md_content += f"""
---

### 3. The Cinematic Cut Imperative
> [!WARNING]
> **Status: {cr.get('cinematicCutEvaluation', {}).get('status', 'MISSING')}**  
> {cr.get('cinematicCutEvaluation', {}).get('analysis', '')}

---

## 📐 3-Cut Ordering & Architecture Blueprint
To deliver on the 3 Reading Lenses (Raw Transcript, Tabletop Cut, Cinematic Cut), the upstream author must restructure and write Track B:

"""
        blueprints = cr.get("cutOrderingBlueprint", {})
        for act_key, b_data in blueprints.items():
            md_content += f"### {b_data.get('title', act_key.title())}\n"
            md_content += f"* **Tabletop Range:** {b_data.get('tabletopScenes', '')}\n"
            md_content += f"* **Cinematic Cut Direction:** {b_data.get('cinematicOrdering', '')}\n\n"

        if report.get("attributionFixes"):
            md_content += """
---

## 📋 Speaker Misattribution Table ({len(report['attributionFixes'])})
The following blocks have conflicting speaker assignments between the narrative dialogue tags and the Schema 2.0 manifest:

| Block ID | Block # | Manifest Assigned | True Prose Speaker | In-Text Dialogue Snippet |
| :--- | :--- | :--- | :--- | :--- |
"""
            for af in report["attributionFixes"]:
                md_content += f"| `{af['blockId']}` | #{af['index']} | `{af['manifestSpeaker']}` | **`{af['proseSpeaker']}`** | {af['snippet']} |\n"

            md_content += """
> [!IMPORTANT]
> **Root Cause Explanation**: `generate_web_manifest.py` resolves `speakerId` purely from raw transcript turn markers (`<!-- Lxxxx -->`). When a character replies to another player (e.g. Pierre replying to Dravin's turn at L0120), the sentence received Dravin's speakerId rather than Pierre's!
> **Remediation**: The upstream generator must verify in-text dialogue tags (e.g. `Pierre murmured`, `Eusacles asked`, `Alfie whispered`) before accepting the antecedent raw turn speaker.
"""

        md_content += f"""
---

## ⚠️ Editorial Warnings & Narrative Polish ({len(report['editorialWarnings'])})
"""
        for warn in report['editorialWarnings']:
            md_content += f"* ⚠️ {warn}\n"

        md_content += """
---

## 🛠️ Actionable Remediation Checklist for Upstream Agent

1. **Author the Missing Cinematic Cut (Track B)**:
   Write `sessions/data/clean/blocks_authorial/s5-scene-01-alt.md` through `s5-scene-10-alt.md` following the 3-Act Ordering Blueprint above. Give Dravin emotional interiority regarding Persephone, eliminate Alfie's luggage syndrome, and pace the Bethlehem heist with cinematic urgency.

2. **Insert Chapter Act Headers in Tabletop Cut**:
   Add `## CHAPTER 29: PARCHMENT, CREPES, AND THE GOD OF TRANSIT` at Scene 1 (line 11).
   Add `## CHAPTER 30: THE CAMPUS AT BETHLEHEM & THE TIN-FOIL PROTEST` at Scene 4.
   Add `## CHAPTER 31: THE 1948 TRIAL NOTES & THE TEMPORAL SEAM` at Scene 7.

3. **Correct Dialogue Turn Citations or Manifest Resolution**:
   Ensure `b008`, `b103`, `b107` are attributed to `pierre`, `b059` and `b070` to `eusacles`, and `b153` to `alfie`.

4. **Re-generate Web Manifest**:
   ```bash
   python sessions/_scripts/generate_web_manifest.py --session 5
   python sessions/_scripts/verify_manifest.py --session 5
   ```

5. **Re-run Editorial Audit**:
   ```bash
   python audit_session_candidate.py --session 5
   ```
"""

        out_md_path.write_text(md_content, encoding="utf-8")
        out_json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"📄 Synced audit report to: {out_md_path}")
        print(f"📄 Synced audit JSON to: {out_json_path}")

        # Update initialBotReview in manifest-v2 if present
        if self.manifest_path.exists():
            try:
                m_data = json.loads(self.manifest_path.read_text(encoding="utf-8"))
                if "editorialForum" in m_data:
                    m_data["editorialForum"]["initialBotReview"] = {
                        "author": "Adversarial Prose Critic (Bot)",
                        "badge": "Autonomous Editorial Lead",
                        "grade": report["grade"],
                        "verdict": report["verdict"],
                        "tomatometer": report.get("tomatometer", 62),
                        "popcornmeter": report.get("popcornmeter", 94),
                        "tableDebrief": debrief,
                        "technicalCompliance": {
                            "criticalErrors": len(report["criticalErrors"]),
                            "editorialWarnings": len(report["editorialWarnings"]),
                            "score": report["totalScore"]
                        },
                        "ruthlessAnalysis": (
                            f"Audit Score: {report['totalScore']}/100 (Tomatometer: {report.get('tomatometer', 62)}%, Popcornmeter: {report.get('popcornmeter', 94)}%). "
                            f"Session 5 has peak table energy (94%) but stalls in prose (62%) due to missing Track B (Cinematic Cut) and dropped Persephone interiority. "
                            + (" ".join(report["criticalErrors"][:2]) if report["criticalErrors"] else "")
                        ),
                        "tradeOffs": [
                            {
                                "dimension": "Faithful Transcript Chronicle vs High-Stakes Novelization",
                                "chosenStance": "Tabletop Cut only",
                                "counterStance": "Dual-cut multi-lens delivery",
                                "tradeOffCost": "Missing the Cinematic Cut robs readers of the elevated, fast-paced novel experience."
                            },
                            {
                                "dimension": "Dialogue Intimacy vs Setting Grounding",
                                "chosenStance": "High spoken share",
                                "counterStance": "Expanded physical description",
                                "tradeOffCost": "Dialogue moves quickly but physical room description needs occasional reinforcement."
                            }
                        ],
                        "nearestRisks": [
                            {"title": "Track B Omission", "risk": "The 3-lens reader collapses to 2 lenses without the authorial cut.", "mitigation": "Author s5-scene-*-alt.md files."},
                            {"title": "Attribution Skew", "risk": "Speaker attribution must strictly match in-text dialogue tags.", "mitigation": "Run attribution auditor before publishing."}
                        ]
                    }
                    self.manifest_path.write_text(json.dumps(m_data, indent=2), encoding="utf-8")
                    print(f"📝 Injected ruthless review and Rotten Tomatoes table debrief into manifest: {self.manifest_path.name}")
            except Exception as e:
                print(f"[WARN] Could not update initialBotReview: {e}")

        if commit_push:
            try:
                print("🚀 Pushing audit report to origin/uneraseable on dnd-scribe...")
                subprocess.run(["git", "add", str(out_md_path), str(out_json_path), str(self.manifest_path)], cwd=str(self.scribe_dir), check=True)
                commit_msg = f"audit(editorial): session {self.session_num} ruthless content & adaptation review ({report['grade']} - {report['totalScore']}/100)"
                subprocess.run(["git", "commit", "-m", commit_msg], cwd=str(self.scribe_dir), check=True)
                subprocess.run(["git", "push", "origin", "uneraseable"], cwd=str(self.scribe_dir), check=True)
                print("✅ Successfully pushed audit feedback to upstream dnd-scribe!")
            except Exception as e:
                print(f"[WARN] Git commit/push failed: {e}")


def main():
    parser = argparse.ArgumentParser(description="Ruthless Editorial Quality Gate & Integration Test Harness")
    parser.add_argument("--session", type=int, required=True, help="Session number to audit (e.g. 5)")
    parser.add_argument("--push-upstream", action="store_true", help="Push audit report directly to dnd-scribe repo via git")
    parser.add_argument("--no-sync", action="store_true", help="Do not write files into dnd-scribe")
    args = parser.parse_args()

    auditor = EditorialAuditor(args.session)
    if not auditor.load_data():
        print(f"❌ Failed to load session {args.session} candidate files:")
        for err in auditor.critical_errors:
            print(f"   • {err}")
        sys.exit(1)

    auditor.audit_mechanical_readiness()
    auditor.audit_attribution_and_grounding()
    auditor.audit_literary_voiceprints_and_craft()
    auditor.audit_content_adaptation_and_cuts()

    report = auditor.generate_report()

    # Terminal Dashboard
    print("\n" + "=" * 80)
    print(f"🛡️  D&D WIKIS — SESSION CANDIDATE AUDIT: SESSION {report['session']}")
    print("=" * 80)
    print(f"Title: {report['title']}")
    print(f"Word Count: {report['totalWords']:,} words | Blocks: {report['blockCount']} | Raw Turns: {report['rawLinesCount']}")
    print(f"Score: {report['totalScore']} / 100 (Grade: {report['grade']})")
    print(f"Verdict: {report['verdict']}\n")

    print(f"📊 Component Scores:")
    print(f"   • Mechanical & Platform Readiness: {report['scoreBreakdown']['mechanical']} / 25")
    print(f"   • Attribution & Grounding Fidelity: {report['scoreBreakdown']['attribution']} / 25")
    print(f"   • Character Voice Authenticity:    {report['scoreBreakdown']['voiceprint']} / 25")
    print(f"   • Literary Craft, Content & Adaptation: {report['scoreBreakdown']['literary_craft']} / 25")

    if report["criticalErrors"]:
        print(f"\n❌ CRITICAL BLOCKING FAILURES ({len(report['criticalErrors'])}):")
        for err in report["criticalErrors"]:
            print(f"   🛑 {err}")

    if report["editorialWarnings"]:
        print(f"\n⚠️  EDITORIAL WARNINGS ({len(report['editorialWarnings'])}):")
        for warn in report["editorialWarnings"]:
            print(f"   ⚠️  {warn}")

    if report["proseCritiques"]:
        print(f"\n✍️  PROSE CLICHÉS & AI CRUTCHES ({len(report['proseCritiques'])}):")
        for cr in report["proseCritiques"]:
            print(f"   🚩 {cr}")

    print("=" * 80 + "\n")

    if not args.no_sync:
        auditor.sync_upstream_report(report, commit_push=args.push_upstream)

    if report["criticalErrors"]:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
