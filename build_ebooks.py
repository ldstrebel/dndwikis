"""Builds interactive Schema 2.0 HTML EBooks from dnd-scribe manifest files with
streamlined diagnostics, NPC unified red styling, clean character badges,
dedicated chapter separation banners, and a visual journey momentum TOC.
"""

import json
import re
from pathlib import Path

MANIFEST_DIR = Path("d:/Code/dnd-scribe/sessions/data/index")
OUTPUT_DIR = Path("d:/Code/dndwikis-main/dndwikis-main")

# Color Scheme
PC_COLORS = {
    "pierre": "#3b82f6",     # Blue
    "dravin": "#8b5cf6",     # Violet
    "eusacles": "#f59e0b",   # Amber / Gold
    "alfie": "#10b981",      # Emerald
    "doug": "#f59e0b",       # Amber
    "mara": "#06b6d4",       # Cyan
    "kael": "#10b981",       # Emerald
    "narrator": "#94a3b8"    # Slate
}
NPC_COLOR = "#f87171"        # Low-intensity red for all NPCs on dark mode

def get_speaker_color(speaker_id: str, char_info: dict) -> str:
    sp_id = speaker_id.lower().strip()
    if sp_id in PC_COLORS:
        return PC_COLORS[sp_id]
    if char_info.get("type") == "narrator":
        return "#94a3b8"
    return NPC_COLOR

def generate_html_for_session(manifest_path: Path, output_path: Path):
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    campaign = data.get("campaign", {})
    session = data.get("session", {})
    characters = data.get("characters", {})
    stats = data.get("stats", {})
    blocks = data.get("blocks", [])

    campaign_name = campaign.get("name", "UNERASEABLE").upper()
    session_num = session.get("number", 1)
    session_title = session.get("title", f"Session {session_num}")
    session_synopsis = session.get("synopsis", "")

    # Stats
    word_count = stats.get("wordCount", len(blocks) * 15)
    read_mins = stats.get("estimatedReadMinutes", round(word_count / 250))
    book_pages = stats.get("estimatedBookPages", round(word_count / 250, 1))
    diag_ratio = stats.get("dialogueRatio", {})
    spoken_pct = diag_ratio.get("spokenPct", 45)
    narrative_pct = diag_ratio.get("narrativePct", 55)
    speaker_dist = stats.get("speakerDistribution", [])
    writing_metrics = stats.get("writingMetrics", {})
    sensory = writing_metrics.get("sensoryRegisters", {})

    # Re-map speaker colors in distribution
    for sp in speaker_dist:
        sp_id = sp.get("id", "").lower()
        sp["color"] = get_speaker_color(sp_id, characters.get(sp_id, {}))

    # Generate progress bar HTML
    prog_bar_segments = ""
    for sp in speaker_dist:
        pct = sp.get("sharePct", 10)
        color = sp.get("color", "#94a3b8")
        name = sp.get("name", "Unknown")
        prog_bar_segments += f'<div style="width: {pct}%; background-color: {color}" class="h-full" title="{name}: {pct}%"></div>\n'

    speaker_chips = ""
    for sp in speaker_dist:
        pct = sp.get("sharePct", 10)
        color = sp.get("color", "#94a3b8")
        name = sp.get("name", "Unknown")
        speaker_chips += f"""
            <div class="flex items-center gap-1.5 text-xs text-slate-300">
                <span class="w-2.5 h-2.5 rounded-full flex-shrink-0" style="background-color: {color}"></span>
                <span class="font-medium truncate">{name}:</span>
                <span class="font-mono font-bold ml-auto" style="color: {color}">{pct}%</span>
            </div>
        """

    # Group Blocks by Chapter/Scene for TOC & Divider construction
    chapters = []
    current_chapter_title = ""
    current_chapter_blocks = []

    for b in blocks:
        scene = b.get("scene", "").strip() or "Prologue"
        if scene != current_chapter_title:
            if current_chapter_blocks:
                chapters.append({
                    "title": current_chapter_title,
                    "blocks": current_chapter_blocks,
                    "word_count": sum(len(blk.get("text", "").split()) for blk in current_chapter_blocks)
                })
            current_chapter_title = scene
            current_chapter_blocks = [b]
        else:
            current_chapter_blocks.append(b)

    if current_chapter_blocks:
        chapters.append({
            "title": current_chapter_title,
            "blocks": current_chapter_blocks,
            "word_count": sum(len(blk.get("text", "").split()) for blk in current_chapter_blocks)
        })

    # Build TOC / Journey Momentum Bar HTML
    toc_cards_html = ""
    for idx, ch in enumerate(chapters, 1):
        ch_title = ch["title"]
        # Clean title (remove redundant 'CHAPTER X:' prefix for neat display if needed)
        clean_ch_title = re.sub(r"^CHAPTER\s*\d+\s*:\s*", "", ch_title, flags=re.IGNORECASE)
        ch_words = ch["word_count"]
        ch_pct = round((ch_words / max(word_count, 1)) * 100)
        ch_mins = max(1, round(ch_words / 250))
        anchor_id = f"chapter-{idx}"

        toc_cards_html += f"""
        <a href="#{anchor_id}" class="group flex-1 min-w-[200px] bg-slate-900/90 hover:bg-slate-800/90 border border-slate-800 hover:border-amber-500/50 p-3 rounded-xl transition-all shadow-md">
            <div class="flex items-center justify-between text-[11px] text-slate-400 mb-1">
                <span class="font-bold text-amber-400 font-mono tracking-wider">Part {idx}</span>
                <span class="font-mono">{ch_pct}% · ~{ch_mins}m</span>
            </div>
            <div class="text-xs font-semibold text-slate-200 group-hover:text-amber-300 transition-colors line-clamp-1">
                {clean_ch_title}
            </div>
            <div class="w-full bg-slate-800 h-1 rounded-full mt-2 overflow-hidden">
                <div class="bg-amber-400 h-full rounded-full" style="width: {ch_pct}%"></div>
            </div>
        </a>
        """

    # Generate Blocks HTML with Dedicated Chapter Dividers
    blocks_html = ""
    chapter_index = 0

    for ch in chapters:
        chapter_index += 1
        ch_title = ch["title"]
        ch_words = ch["word_count"]
        ch_pct = round((ch_words / max(word_count, 1)) * 100)
        ch_mins = max(1, round(ch_words / 250))
        anchor_id = f"chapter-{chapter_index}"

        # Dedicated Chapter Divider
        blocks_html += f"""
        <!-- CHAPTER DIVIDER {chapter_index} -->
        <section id="{anchor_id}" class="pt-8 pb-4 my-6 border-b border-slate-800/80 scroll-mt-20">
            <div class="flex items-center gap-3">
                <div class="h-px bg-gradient-to-r from-transparent via-amber-500/40 to-transparent flex-1"></div>
                <div class="text-center px-3">
                    <span class="text-[11px] font-bold font-mono tracking-widest text-amber-500 uppercase">Part {chapter_index} · {ch_pct}% of Session (~{ch_mins}m read)</span>
                    <h3 class="text-xl sm:text-2xl font-bold font-serif text-slate-100 mt-0.5 tracking-wide">{ch_title}</h3>
                </div>
                <div class="h-px bg-gradient-to-r from-transparent via-amber-500/40 to-transparent flex-1"></div>
            </div>
        </section>
        """

        for b in ch["blocks"]:
            b_id = b.get("id", "block")
            b_idx = b.get("index", 1)
            sp_id = b.get("speakerId", "narrator").lower().strip()
            sp_info = characters.get(sp_id, {"name": sp_id.title(), "type": "narrator"})
            sp_name = sp_info.get("name", sp_id.title())
            sp_color = get_speaker_color(sp_id, sp_info)
            text = b.get("text", "")

            is_narrator = (sp_info.get("type") == "narrator" or sp_id == "narrator")

            if is_narrator:
                blocks_html += f"""
                <!-- Block {b_idx} (Narrator) -->
                <div class="story-block p-4 rounded-r-xl bg-slate-900/30"
                     style="border-left: 3px solid rgba(148, 163, 184, 0.2);"
                     data-block-id="{b_id}"
                     data-speaker="{sp_id}"
                     data-speaker-name="{sp_name}"
                     data-speaker-color="{sp_color}">
                    <div class="flex justify-end mb-1">
                        <span class="critique-indicator-dot hidden text-xs text-amber-400 font-bold">● Critique Added</span>
                    </div>
                    <p class="text-slate-300 leading-relaxed text-base sm:text-lg">{text}</p>
                </div>
                """
            else:
                blocks_html += f"""
                <!-- Block {b_idx} ({sp_name}) -->
                <div class="story-block p-4 rounded-r-xl"
                     style="border-left: 3.5px solid {sp_color}; background: linear-gradient(90deg, {sp_color}14 0%, {sp_color}02 100%);"
                     data-block-id="{b_id}"
                     data-speaker="{sp_id}"
                     data-speaker-name="{sp_name}"
                     data-speaker-color="{sp_color}">
                    <div class="flex items-center gap-2 mb-2">
                        <span class="w-2.5 h-2.5 rounded-full" style="background-color: {sp_color}"></span>
                        <span class="text-xs font-bold uppercase tracking-wider font-mono" style="color: {sp_color}">{sp_name}</span>
                        <span class="critique-indicator-dot hidden ml-auto text-xs text-amber-400 font-bold">● Critique Added</span>
                    </div>
                    <p class="text-slate-100 font-medium leading-relaxed text-base sm:text-lg">{text}</p>
                </div>
                """

    # Assemble Full Document
    full_html = f"""<!DOCTYPE html>
<html lang="en" class="dark scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <title>Uneraseable — {session_title}</title>
    
    <!-- Tailwind CSS via CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {{
            darkMode: 'class',
            theme: {{
                extend: {{
                    colors: {{
                        slate: {{ 950: '#080c14' }},
                        amber: {{ 450: '#fbbf24' }}
                    }},
                    fontFamily: {{
                        serif: ['Cinzel', 'Georgia', 'serif'],
                        sans: ['Outfit', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
                        mono: ['JetBrains Mono', 'monospace']
                    }}
                }}
            }}
        }}
    </script>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Cinzel:wght@500;700;900&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">

    <style>
        body {{
            background-color: #080c14;
            color: #f1f5f9;
            font-family: 'Outfit', sans-serif;
            -webkit-tap-highlight-color: transparent;
        }}

        .story-block {{
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
            position: relative;
        }}

        body.mode-critique .story-block {{
            cursor: pointer;
        }}
        body.mode-critique .story-block:hover {{
            transform: translateX(4px);
        }}
        body.mode-critique .story-block::after {{
            content: '💬';
            position: absolute;
            right: -28px;
            top: 50%;
            transform: translateY(-50%);
            opacity: 0;
            font-size: 14px;
            transition: opacity 0.2s;
        }}
        @media (max-width: 640px) {{
            body.mode-critique .story-block::after {{
                right: 8px;
                top: 8px;
                transform: none;
            }}
        }}
        body.mode-critique .story-block:hover::after {{
            opacity: 0.8;
        }}

        .story-block.has-critique {{
            box-shadow: inset 0 0 0 1px rgba(245, 158, 11, 0.5);
        }}
        .story-block.has-critique .critique-indicator-dot {{
            display: inline-flex;
        }}

        #sessionStatsSection {{
            transition: all 0.3s ease;
        }}
        #sessionStatsSection.collapsed {{
            display: none !important;
        }}

        #critiqueModalOverlay {{
            transition: opacity 0.25s ease, backdrop-filter 0.25s ease;
        }}
        #critiqueModalOverlay.visible {{
            opacity: 1;
            pointer-events: auto;
        }}
        #critiqueBottomSheet {{
            transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        }}
        #critiqueModalOverlay.visible #critiqueBottomSheet {{
            transform: translateY(0);
        }}
    </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen pb-24 mode-critique">

    <!-- STICKY TOP APP BAR -->
    <header class="sticky top-0 z-40 bg-slate-900/95 backdrop-blur-md border-b border-slate-800 px-4 py-2.5">
        <div class="max-w-4xl mx-auto flex items-center justify-between gap-3">
            <div class="flex items-center gap-3 min-w-0">
                <a href="index.html" class="text-slate-400 hover:text-amber-400 transition-colors flex items-center text-sm font-semibold gap-1">
                    <span>←</span> <span class="hidden sm:inline">Portals</span>
                </a>
                <span class="text-slate-700">|</span>
                <div class="truncate">
                    <h1 class="font-bold text-sm sm:text-base text-amber-400 font-serif tracking-wide truncate">{campaign_name}</h1>
                    <p class="text-xs text-slate-400 truncate">Session {session_num}: {session_title}</p>
                </div>
            </div>

            <!-- Header Action Controls -->
            <div class="flex items-center gap-2 flex-shrink-0">
                <!-- Stats Toggle Button -->
                <button id="toggleStatsBtn" class="px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 flex items-center gap-1.5 transition-all" title="Toggle session diagnostics drawer">
                    <span>📊</span>
                    <span id="toggleStatsBtnLabel">Hide Stats</span>
                </button>

                <!-- Reader / Critique Mode Switcher -->
                <div class="flex bg-slate-950 border border-slate-800 rounded-lg p-0.5" title="Switch reading mode">
                    <button id="modeReaderBtn" class="px-2.5 py-1 rounded-md text-xs font-medium text-slate-400 hover:text-slate-200 transition-all flex items-center gap-1">
                        <span>📖</span> <span class="hidden sm:inline">Read</span>
                    </button>
                    <button id="modeCritiqueBtn" class="px-2.5 py-1 rounded-md text-xs font-bold text-slate-950 bg-amber-400 shadow transition-all flex items-center gap-1">
                        <span>✍️</span> <span class="hidden sm:inline">Critique</span>
                    </button>
                </div>

                <!-- Export / PR Trigger -->
                <button id="exportCritiquesBtn" class="px-3 py-1.5 rounded-lg text-xs font-bold bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 text-slate-950 flex items-center gap-1.5 shadow-sm" title="Submit review notes as a GitHub PR">
                    <span>🐙</span>
                    <span>Submit PR</span>
                    <span id="exportBadgeCount" class="bg-slate-950 text-amber-300 text-[10px] px-1.5 py-0.2 rounded-full font-bold ml-0.5">0</span>
                </button>
            </div>
        </div>
    </header>

    <!-- WRAPPER -->
    <div class="max-w-3xl mx-auto px-4 sm:px-6 pt-6">

        <!-- ========================================================= -->
        <!-- TOP STATS DRAWER (Streamlined & Responsive) -->
        <!-- ========================================================= -->
        <section id="sessionStatsSection" class="mb-8">
            <div class="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 sm:p-6 shadow-2xl backdrop-blur-sm">
                
                <!-- Drawer Header -->
                <div class="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
                    <div class="flex items-center gap-2">
                        <span class="text-lg">📊</span>
                        <h2 class="text-sm font-bold tracking-wider uppercase text-amber-400">Session {session_num} Metrics & Diagnostics</h2>
                    </div>
                    <button id="minimizeStatsBtn" class="text-xs text-slate-400 hover:text-slate-200 font-semibold flex items-center gap-1 bg-slate-800 px-2.5 py-1 rounded-lg border border-slate-700">
                        <span>Hide Stats ▲</span>
                    </button>
                </div>

                <!-- Streamlined 3-Column Metric Grid -->
                <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-5">
                    <div class="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
                        <div class="text-[11px] text-slate-400 font-medium">Story Length & Reading Time</div>
                        <div class="text-lg font-bold text-slate-100 mt-0.5 font-mono">{word_count:,} <span class="text-xs text-slate-500 font-normal">words</span></div>
                        <div class="text-[11px] text-emerald-400 mt-0.5">~{book_pages} Book Pages · {read_mins}m Read</div>
                    </div>

                    <div class="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
                        <div class="text-[11px] text-slate-400 font-medium">Dialogue Ratio</div>
                        <div class="text-lg font-bold text-amber-400 mt-0.5 font-mono">{spoken_pct}% <span class="text-xs text-slate-500 font-normal">spoken</span></div>
                        <div class="text-[11px] text-slate-400 mt-0.5">{narrative_pct}% Narrative Prose</div>
                    </div>

                    <div class="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
                        <div class="text-[11px] text-slate-400 font-medium">Sensory Coverage ({sensory.get("registersCovered", 5)}/5 Registers)</div>
                        <div class="flex flex-wrap gap-1 mt-1.5">
                            <span class="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 text-[10px]">👁️ Visual: <strong class="text-amber-400">{sensory.get("visual", 30)}</strong></span>
                            <span class="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 text-[10px]">👂 Auditory: <strong class="text-sky-400">{sensory.get("auditory", 15)}</strong></span>
                            <span class="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 text-[10px]">✋ Tactile: <strong class="text-emerald-400">{sensory.get("tactile", 20)}</strong></span>
                            <span class="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 text-[10px]">👃 Scent: <strong class="text-rose-400">{sensory.get("olfactory", 10)}</strong></span>
                            <span class="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 text-[10px]">⚡ Ambient: <strong class="text-amber-300">{sensory.get("atmospheric", 15)}</strong></span>
                        </div>
                    </div>
                </div>

                <!-- Character Dialogue Breakdown (11Labs Multi-Voice Split Bar) -->
                <div class="space-y-2 bg-slate-950/40 p-3.5 rounded-xl border border-slate-800/60">
                    <div class="flex justify-between items-center text-xs font-semibold text-slate-300 mb-1">
                        <span>🎙️ Speaker Line Share & Dialogue Distribution</span>
                        <span class="text-[11px] text-slate-400">{len(speaker_dist)} Active Voices</span>
                    </div>

                    <!-- Multi-color split progress bar -->
                    <div class="h-3 w-full rounded-full bg-slate-800 flex overflow-hidden shadow-inner">
                        {prog_bar_segments}
                    </div>

                    <!-- Speaker Legend Chips -->
                    <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2">
                        {speaker_chips}
                    </div>
                </div>

            </div>
        </section>

        <!-- EBOOK COVER & INTRO HEADER -->
        <div class="mb-8 text-center">
            <div class="w-44 sm:w-52 mx-auto mb-4 rounded-xl overflow-hidden shadow-2xl border border-slate-800 ring-1 ring-amber-500/20">
                <img src="images/uneraseable-cover.jpg" alt="Uneraseable Cover by Doug N Masters" class="w-full h-auto object-cover">
            </div>
            <span class="text-xs uppercase tracking-widest text-amber-500 font-bold font-mono">Session {session_num} · Interactive Edition</span>
            <h2 class="text-3xl sm:text-4xl font-extrabold text-slate-100 font-serif mt-1 tracking-wide">{session_title}</h2>
            <p class="text-sm text-slate-400 mt-2 font-serif italic max-w-xl mx-auto">{session_synopsis}</p>
        </div>

        <!-- ========================================================= -->
        <!-- SESSION JOURNEY & MOMENTUM TRACK (TOC) -->
        <!-- ========================================================= -->
        <div class="mb-10 bg-slate-950/70 p-4 rounded-2xl border border-slate-800/90 shadow-lg">
            <div class="flex items-center gap-2 mb-3 text-xs font-bold text-amber-400 uppercase tracking-wider">
                <span>📍</span>
                <span>Session Arc & Location Momentum Track</span>
            </div>
            <div class="flex flex-wrap sm:flex-nowrap gap-2.5 overflow-x-auto pb-1">
                {toc_cards_html}
            </div>
        </div>

        <!-- ========================================================= -->
        <!-- 11LABS-STYLE STORY BLOCKS CONTAINER -->
        <!-- ========================================================= -->
        <main id="storyContentContainer" class="space-y-4">
            {blocks_html}
        </main>

        <!-- Bottom Page Controls & Review Summary -->
        <footer class="mt-16 pt-8 border-t border-slate-800 text-center space-y-4">
            <div class="bg-slate-900/60 p-5 rounded-2xl border border-slate-800 max-w-md mx-auto shadow-lg">
                <h3 class="text-sm font-bold text-amber-400 mb-1">Session Review & Critique Submission</h3>
                <p class="text-xs text-slate-400 mb-3">Submit your feedback directly to the dnd-scribe agent pipeline.</p>
                <div class="flex gap-2 justify-center">
                    <button id="footerExportBtn" class="px-5 py-2.5 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 text-slate-950 font-bold rounded-xl text-xs transition-all shadow-md flex items-center gap-1.5">
                        <span>🐙</span> <span>Submit Review PR to GitHub</span>
                    </button>
                    <button id="clearCritiquesBtn" class="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 text-xs font-semibold rounded-xl transition-colors">
                        Clear All
                    </button>
                </div>
            </div>
            <p class="text-xs text-slate-600">UNERASEABLE © D&D Scribe Engine · Schema 2.0 Indexed.</p>
        </footer>

    </div>

    <!-- ========================================================= -->
    <!-- MOBILE BOTTOM SHEET & CRITIQUE MODAL -->
    <!-- ========================================================= -->
    <div id="critiqueModalOverlay" class="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-end sm:items-center justify-center opacity-0 pointer-events-none p-0 sm:p-4">
        <div id="critiqueBottomSheet" class="w-full max-w-lg bg-slate-900 border-t sm:border border-slate-700 sm:rounded-2xl rounded-t-2xl p-5 shadow-2xl transform translate-y-full sm:translate-y-4 max-h-[90vh] flex flex-col">
            <div class="w-12 h-1.5 bg-slate-700 rounded-full mx-auto mb-3 sm:hidden"></div>
            <div class="flex items-center justify-between border-b border-slate-800 pb-3 mb-3">
                <div class="flex items-center gap-2">
                    <span id="modalSpeakerPill" class="px-2.5 py-1 rounded-md text-xs font-bold uppercase tracking-wider font-mono"></span>
                    <span id="modalBlockIndex" class="text-xs text-slate-400 font-mono"></span>
                </div>
                <button id="modalCloseBtn" class="text-slate-400 hover:text-slate-200 text-xl font-bold p-1">&times;</button>
            </div>
            <div class="overflow-y-auto space-y-4 pr-1 flex-1">
                <div class="bg-slate-950/80 p-3 rounded-xl border border-slate-800/80">
                    <div class="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">Target Passage:</div>
                    <p id="modalPassageText" class="text-sm text-slate-200 italic leading-relaxed"></p>
                </div>
                <div>
                    <label class="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">Category</label>
                    <div class="grid grid-cols-3 sm:grid-cols-5 gap-1.5" id="categoryPillContainer">
                        <button type="button" class="category-pill active px-2 py-1.5 rounded-lg text-[11px] font-bold border border-amber-500 bg-amber-500/20 text-amber-300 text-center" data-category="tone">Tone / Voice</button>
                        <button type="button" class="category-pill px-2 py-1.5 rounded-lg text-[11px] font-medium border border-slate-700 bg-slate-800 text-slate-300 text-center" data-category="continuity">Continuity</button>
                        <button type="button" class="category-pill px-2 py-1.5 rounded-lg text-[11px] font-medium border border-slate-700 bg-slate-800 text-slate-300 text-center" data-category="pacing">Pacing</button>
                        <button type="button" class="category-pill px-2 py-1.5 rounded-lg text-[11px] font-medium border border-slate-700 bg-slate-800 text-slate-300 text-center" data-category="rewrite">Rewrite</button>
                        <button type="button" class="category-pill px-2 py-1.5 rounded-lg text-[11px] font-medium border border-slate-700 bg-slate-800 text-slate-300 text-center" data-category="audio_cue">Audio Cue</button>
                    </div>
                </div>
                <div>
                    <label for="critiqueTextInput" class="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">Critique / Revision Directive</label>
                    <textarea id="critiqueTextInput" rows="3" class="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500" placeholder="E.g. Make this interaction sharper, emphasize the tension..."></textarea>
                </div>
                <div>
                    <label for="suggestedRewriteInput" class="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">Direct Suggested Rewrite <span class="text-slate-600 font-normal lowercase">(optional)</span></label>
                    <textarea id="suggestedRewriteInput" rows="2" class="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-cyan-500" placeholder="Provide direct replacement line if desired..."></textarea>
                </div>
            </div>
            <div class="pt-3 mt-2 border-t border-slate-800 flex items-center justify-between gap-2">
                <div class="flex gap-1.5">
                    <button id="modalPrevBlockBtn" class="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-semibold flex items-center gap-1"><span>◀</span> <span class="hidden sm:inline">Prev</span></button>
                    <button id="modalNextBlockBtn" class="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-semibold flex items-center gap-1"><span class="hidden sm:inline">Next</span> <span>▶</span></button>
                </div>
                <div class="flex gap-2">
                    <button id="modalDeleteBtn" class="px-3 py-2 bg-rose-950/50 hover:bg-rose-900 border border-rose-800 text-rose-300 rounded-lg text-xs font-bold transition-colors hidden">Delete</button>
                    <button id="modalSaveBtn" class="px-5 py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded-lg text-xs transition-colors shadow-lg shadow-amber-500/20 flex items-center gap-1.5"><span>💾</span> <span>Save Critique</span></button>
                </div>
            </div>
        </div>
    </div>

    <!-- SCRIPT CONTROLLER -->
    <script>
        (function() {{
            const CAMPAIGN_ID = "uneraseable";
            const CHAPTER_ID = "s{session_num}";
            const STORAGE_KEY = `critiques_${{CAMPAIGN_ID}}_${{CHAPTER_ID}}`;
            
            let critiques = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{{}}");
            let activeBlockIndex = 0;
            let selectedCategory = "tone";
            const blocks = Array.from(document.querySelectorAll('.story-block'));

            const statsSection = document.getElementById('sessionStatsSection');
            const toggleStatsBtn = document.getElementById('toggleStatsBtn');
            const toggleStatsBtnLabel = document.getElementById('toggleStatsBtnLabel');
            const minimizeStatsBtn = document.getElementById('minimizeStatsBtn');
            const modeReaderBtn = document.getElementById('modeReaderBtn');
            const modeCritiqueBtn = document.getElementById('modeCritiqueBtn');
            const exportCritiquesBtn = document.getElementById('exportCritiquesBtn');
            const footerExportBtn = document.getElementById('footerExportBtn');
            const clearCritiquesBtn = document.getElementById('clearCritiquesBtn');
            const exportBadgeCount = document.getElementById('exportBadgeCount');

            const modalOverlay = document.getElementById('critiqueModalOverlay');
            const modalCloseBtn = document.getElementById('modalCloseBtn');
            const modalSpeakerPill = document.getElementById('modalSpeakerPill');
            const modalBlockIndex = document.getElementById('modalBlockIndex');
            const modalPassageText = document.getElementById('modalPassageText');
            const critiqueTextInput = document.getElementById('critiqueTextInput');
            const suggestedRewriteInput = document.getElementById('suggestedRewriteInput');
            const modalPrevBlockBtn = document.getElementById('modalPrevBlockBtn');
            const modalNextBlockBtn = document.getElementById('modalNextBlockBtn');
            const modalSaveBtn = document.getElementById('modalSaveBtn');
            const modalDeleteBtn = document.getElementById('modalDeleteBtn');
            const categoryPills = document.querySelectorAll('.category-pill');

            function refreshMarkers() {{
                const count = Object.keys(critiques).length;
                exportBadgeCount.textContent = count;

                blocks.forEach((el) => {{
                    const id = el.dataset.blockId;
                    if (critiques[id]) {{
                        el.classList.add('has-critique');
                        const dot = el.querySelector('.critique-indicator-dot');
                        if (dot) dot.classList.remove('hidden');
                    }} else {{
                        el.classList.remove('has-critique');
                        const dot = el.querySelector('.critique-indicator-dot');
                        if (dot) dot.classList.add('hidden');
                    }}
                }});
            }}

            function toggleStats() {{
                const isCollapsed = statsSection.classList.toggle('collapsed');
                if (isCollapsed) {{
                    toggleStatsBtnLabel.textContent = "Show Stats";
                }} else {{
                    toggleStatsBtnLabel.textContent = "Hide Stats";
                }}
            }}

            toggleStatsBtn.addEventListener('click', toggleStats);
            minimizeStatsBtn.addEventListener('click', toggleStats);

            modeReaderBtn.addEventListener('click', () => {{
                document.body.classList.remove('mode-critique');
                modeReaderBtn.classList.replace('text-slate-400', 'text-slate-950');
                modeReaderBtn.classList.add('bg-amber-400', 'font-bold');
                modeCritiqueBtn.classList.remove('bg-amber-400', 'text-slate-950', 'font-bold');
                modeCritiqueBtn.classList.add('text-slate-400');
            }});

            modeCritiqueBtn.addEventListener('click', () => {{
                document.body.classList.add('mode-critique');
                modeCritiqueBtn.classList.replace('text-slate-400', 'text-slate-950');
                modeCritiqueBtn.classList.add('bg-amber-400', 'font-bold');
                modeReaderBtn.classList.remove('bg-amber-400', 'text-slate-950', 'font-bold');
                modeReaderBtn.classList.add('text-slate-400');
            }});

            categoryPills.forEach(pill => {{
                pill.addEventListener('click', () => {{
                    categoryPills.forEach(p => {{
                        p.classList.remove('active', 'border-amber-500', 'bg-amber-500/20', 'text-amber-300');
                        p.classList.add('border-slate-700', 'bg-slate-800', 'text-slate-300');
                    }});
                    pill.classList.add('active', 'border-amber-500', 'bg-amber-500/20', 'text-amber-300');
                    selectedCategory = pill.dataset.category;
                }});
            }});

            function openModalForBlock(index) {{
                if (index < 0 || index >= blocks.length) return;
                activeBlockIndex = index;
                const block = blocks[index];
                const blockId = block.dataset.blockId;
                const speakerName = block.dataset.speakerName || "Narrator";
                const speakerColor = block.dataset.speakerColor || "#94a3b8";
                const text = block.querySelector('p').innerText;

                modalSpeakerPill.textContent = speakerName;
                modalSpeakerPill.style.backgroundColor = speakerColor + "25";
                modalSpeakerPill.style.borderColor = speakerColor;
                modalSpeakerPill.style.color = speakerColor;
                modalBlockIndex.textContent = `#${{index + 1}} (${{blockId}})`;
                modalPassageText.textContent = `"${{text}}"`;

                const existing = critiques[blockId];
                if (existing) {{
                    critiqueTextInput.value = existing.comment || "";
                    suggestedRewriteInput.value = existing.suggestedRewrite || "";
                    selectedCategory = existing.category || "tone";
                    modalDeleteBtn.classList.remove('hidden');

                    categoryPills.forEach(p => {{
                        if (p.dataset.category === selectedCategory) {{
                            p.click();
                        }}
                    }});
                }} else {{
                    critiqueTextInput.value = "";
                    suggestedRewriteInput.value = "";
                    modalDeleteBtn.classList.add('hidden');
                }}

                modalPrevBlockBtn.disabled = (index === 0);
                modalNextBlockBtn.disabled = (index === blocks.length - 1);
                modalOverlay.classList.add('visible');
                critiqueTextInput.focus();
            }}

            function closeModal() {{ modalOverlay.classList.remove('visible'); }}
            modalCloseBtn.addEventListener('click', closeModal);
            modalOverlay.addEventListener('click', (e) => {{ if (e.target === modalOverlay) closeModal(); }});

            modalPrevBlockBtn.addEventListener('click', () => {{ if (activeBlockIndex > 0) openModalForBlock(activeBlockIndex - 1); }});
            modalNextBlockBtn.addEventListener('click', () => {{ if (activeBlockIndex < blocks.length - 1) openModalForBlock(activeBlockIndex + 1); }});

            modalSaveBtn.addEventListener('click', () => {{
                const block = blocks[activeBlockIndex];
                const blockId = block.dataset.blockId;
                const comment = critiqueTextInput.value.trim();
                const rewrite = suggestedRewriteInput.value.trim();

                if (!comment && !rewrite) {{
                    alert("Please provide a critique note or suggested rewrite before saving.");
                    return;
                }}

                critiques[blockId] = {{
                    blockId: blockId,
                    blockIndex: activeBlockIndex + 1,
                    speaker: block.dataset.speakerName,
                    category: selectedCategory,
                    quote: block.querySelector('p').innerText,
                    comment: comment,
                    suggestedRewrite: rewrite,
                    updatedAt: new Date().toISOString()
                }};

                localStorage.setItem(STORAGE_KEY, JSON.stringify(critiques));
                refreshMarkers();
                closeModal();
            }});

            modalDeleteBtn.addEventListener('click', () => {{
                const block = blocks[activeBlockIndex];
                const blockId = block.dataset.blockId;
                delete critiques[blockId];
                localStorage.setItem(STORAGE_KEY, JSON.stringify(critiques));
                refreshMarkers();
                closeModal();
            }});

            blocks.forEach((b, idx) => {{
                b.addEventListener('click', () => {{
                    if (document.body.classList.contains('mode-critique')) openModalForBlock(idx);
                }});
            }});

            // GitHub PR Submission Modal
            const ghModalOverlay = document.createElement('div');
            ghModalOverlay.id = "ghModalOverlay";
            ghModalOverlay.className = "fixed inset-0 bg-slate-950/85 backdrop-blur-md z-50 flex items-center justify-center opacity-0 pointer-events-none p-4 transition-opacity duration-200";
            ghModalOverlay.innerHTML = `
                <div class="bg-slate-900 border border-slate-700 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
                    <div class="flex justify-between items-center border-b border-slate-800 pb-3">
                        <div class="flex items-center gap-2">
                            <span class="text-xl">🐙</span>
                            <h3 class="text-amber-400 font-bold text-base">Submit Review PR to GitHub</h3>
                        </div>
                        <button id="closeGhModal" class="text-slate-400 hover:text-slate-200 text-xl font-bold">&times;</button>
                    </div>

                    <div class="space-y-3 text-xs">
                        <div class="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-1">
                            <div class="flex justify-between text-slate-400"><span>Target Repository:</span><span class="font-mono text-slate-200">ldstrebel/dnd-scribe</span></div>
                            <div class="flex justify-between text-slate-400"><span>Target Base Branch:</span><span class="font-mono text-amber-400">uneraseable</span></div>
                            <div class="flex justify-between text-slate-400"><span>Critiques in Batch:</span><span class="font-mono text-emerald-400 font-bold" id="ghCritiqueCountDisplay">0 notes</span></div>
                        </div>

                        <div>
                            <label class="block font-semibold text-slate-300 mb-1">Reviewer Name / Player Handle</label>
                            <input type="text" id="ghReviewerNameInput" class="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-slate-100 placeholder-slate-600 focus:outline-none focus:border-amber-500" placeholder="e.g. Doug, Mara, Editor">
                        </div>

                        <div>
                            <label class="block font-semibold text-slate-300 mb-1">GitHub Token (PAT / App Token)</label>
                            <input type="password" id="ghTokenInput" class="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-slate-100 placeholder-slate-600 font-mono text-xs focus:outline-none focus:border-amber-500" placeholder="ghs_... or github_pat_...">
                        </div>

                        <div id="ghStatusMsg" class="hidden p-2.5 rounded-lg text-xs"></div>
                    </div>

                    <div class="flex gap-2 pt-2 border-t border-slate-800">
                        <button id="ghCopyJsonBtn" class="flex-1 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold rounded-lg text-xs transition-colors">📋 Copy JSON</button>
                        <button id="ghSubmitPrBtn" class="flex-1 py-2 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 text-slate-950 font-bold rounded-lg text-xs transition-colors shadow-lg shadow-amber-500/20 flex items-center justify-center gap-1.5"><span>🚀</span> <span>Open PR</span></button>
                    </div>
                </div>
            `;
            document.body.appendChild(ghModalOverlay);

            const closeGhModal = document.getElementById('closeGhModal');
            const ghReviewerNameInput = document.getElementById('ghReviewerNameInput');
            const ghTokenInput = document.getElementById('ghTokenInput');
            const ghCritiqueCountDisplay = document.getElementById('ghCritiqueCountDisplay');
            const ghSubmitPrBtn = document.getElementById('ghSubmitPrBtn');
            const ghCopyJsonBtn = document.getElementById('ghCopyJsonBtn');
            const ghStatusMsg = document.getElementById('ghStatusMsg');

            ghTokenInput.value = localStorage.getItem('dnd_scribe_gh_token') || '';
            ghReviewerNameInput.value = localStorage.getItem('dnd_scribe_reviewer_name') || 'Reviewer';

            function showGhModal() {{
                const count = Object.keys(critiques).length;
                if (count === 0) {{
                    alert("No review notes recorded yet! Click on any dialogue or narrator block to add notes first.");
                    return;
                }}
                ghCritiqueCountDisplay.textContent = `${{count}} critique(s)`;
                ghStatusMsg.classList.add('hidden');
                ghModalOverlay.classList.remove('opacity-0', 'pointer-events-none');
            }}

            function hideGhModal() {{ ghModalOverlay.classList.add('opacity-0', 'pointer-events-none'); }}
            closeGhModal.addEventListener('click', hideGhModal);
            ghModalOverlay.addEventListener('click', (e) => {{ if (e.target === ghModalOverlay) hideGhModal(); }});

            ghCopyJsonBtn.addEventListener('click', () => {{
                const count = Object.keys(critiques).length;
                const exportPayload = {{
                    campaign: CAMPAIGN_ID,
                    chapter: CHAPTER_ID,
                    title: "Uneraseable - {session_title}",
                    reviewer: ghReviewerNameInput.value.trim() || "Anonymous",
                    exportedAt: new Date().toISOString(),
                    totalCritiques: count,
                    critiques: Object.values(critiques)
                }};
                navigator.clipboard.writeText(JSON.stringify(exportPayload, null, 2)).then(() => {{
                    alert(`✨ Copied ${{count}} critique(s) to clipboard!`);
                    hideGhModal();
                }});
            }});

            ghSubmitPrBtn.addEventListener('click', async () => {{
                const token = ghTokenInput.value.trim();
                const reviewer = ghReviewerNameInput.value.trim() || 'Reviewer';
                const count = Object.keys(critiques).length;
                if (!token) {{ alert("Please enter your GitHub token to submit."); return; }}

                localStorage.setItem('dnd_scribe_gh_token', token);
                localStorage.setItem('dnd_scribe_reviewer_name', reviewer);

                ghStatusMsg.className = "p-2.5 rounded-lg text-xs bg-sky-950/60 border border-sky-800 text-sky-300 block";
                ghStatusMsg.textContent = "⏳ Contacting GitHub API to create critique branch...";
                ghSubmitPrBtn.disabled = true;

                const REPO = "ldstrebel/dnd-scribe";
                const BASE_BRANCH = "uneraseable";
                const safeName = reviewer.toLowerCase().replace(/[^a-z0-9]/g, '-');
                const timestamp = Date.now().toString().slice(-6);
                const NEW_BRANCH = `critique/${{CAMPAIGN_ID}}-${{CHAPTER_ID}}-${{safeName}}-${{timestamp}}`;

                const exportPayload = {{
                    campaign: CAMPAIGN_ID,
                    chapter: CHAPTER_ID,
                    title: "Uneraseable - {session_title}",
                    reviewer: reviewer,
                    exportedAt: new Date().toISOString(),
                    totalCritiques: count,
                    critiques: Object.values(critiques)
                }};

                const markdownRows = Object.values(critiques).map(c => 
                    `| \`${{c.blockId}}\` | **${{c.speaker}}** | \`${{c.category}}\` | ${{c.comment.replace(/\|/g, '\\\\|')}} | ${{c.suggestedRewrite ? c.suggestedRewrite.replace(/\|/g, '\\\\|') : '-'}} |`
                ).join('\\n');

                const prBody = `## 📝 Story Critique Batch: ${{exportPayload.title}}\\n**Reviewer:** ${{reviewer}}\\n**Total Notes:** ${{count}}\\n\\n### 📋 Critique Items Table\\n| Block ID | Speaker | Category | Critique / Directive | Suggested Rewrite |\\n|---|---|---|---|---|\\n${{markdownRows}}\\n\\n<details>\\n<summary><b>📦 Raw JSON Payload (for Agent Ingestion)</b></summary>\\n\\n\\\`\\\`\\\`json\\n${{JSON.stringify(exportPayload, null, 2)}}\\n\\\`\\\`\\\`\\n</details>`;

                try {{
                    const headers = {{ "Authorization": `Bearer ${{token}}`, "Accept": "application/vnd.github+json", "Content-Type": "application/json" }};
                    let baseRefRes = await fetch(`https://api.github.com/repos/${{REPO}}/git/ref/heads/${{BASE_BRANCH}}`, {{ headers }});
                    if (!baseRefRes.ok) baseRefRes = await fetch(`https://api.github.com/repos/${{REPO}}/git/ref/heads/main`, {{ headers }});
                    if (!baseRefRes.ok) throw new Error("Could not find base branch on GitHub repo: " + baseRefRes.statusText);
                    const baseSha = (await baseRefRes.json()).object.sha;

                    ghStatusMsg.textContent = "⏳ Creating review branch: " + NEW_BRANCH;
                    const createBranchRes = await fetch(`https://api.github.com/repos/${{REPO}}/git/refs`, {{ method: "POST", headers, body: JSON.stringify({{ ref: `refs/heads/${{NEW_BRANCH}}`, sha: baseSha }}) }});
                    if (!createBranchRes.ok) throw new Error("Failed to create critique branch: " + (await createBranchRes.text()));

                    ghStatusMsg.textContent = "⏳ Committing critique JSON payload...";
                    const filePath = `sessions/data/critiques/${{CAMPAIGN_ID}}-${{CHAPTER_ID}}-${{safeName}}-${{timestamp}}.json`;
                    const contentBase64 = btoa(unescape(encodeURIComponent(JSON.stringify(exportPayload, null, 2))));
                    const commitRes = await fetch(`https://api.github.com/repos/${{REPO}}/contents/${{filePath}}`, {{ method: "PUT", headers, body: JSON.stringify({{ message: `critique: ${{reviewer}} review for ${{CAMPAIGN_ID}} ${{CHAPTER_ID}}`, content: contentBase64, branch: NEW_BRANCH }}) }});
                    if (!commitRes.ok) throw new Error("Failed to commit critique file: " + (await commitRes.text()));

                    ghStatusMsg.textContent = "⏳ Opening Pull Request on GitHub...";
                    const prRes = await fetch(`https://api.github.com/repos/${{REPO}}/pulls`, {{ method: "POST", headers, body: JSON.stringify({{ title: `📝 Review: ${{CAMPAIGN_ID.toUpperCase()}} ${{CHAPTER_ID.toUpperCase()}} by ${{reviewer}}`, head: NEW_BRANCH, base: BASE_BRANCH, body: prBody }}) }});
                    if (!prRes.ok) throw new Error("Failed to open Pull Request: " + (await prRes.text()));
                    const prData = await prRes.json();

                    ghStatusMsg.className = "p-2.5 rounded-lg text-xs bg-emerald-950/70 border border-emerald-700 text-emerald-300 block";
                    ghStatusMsg.innerHTML = `🎉 <strong>PR Opened Successfully!</strong><br><a href="${{prData.html_url}}" target="_blank" class="underline font-bold text-amber-300">View Pull Request #${{prData.number}}</a>`;
                }} catch (err) {{
                    ghStatusMsg.className = "p-2.5 rounded-lg text-xs bg-rose-950/70 border border-rose-700 text-rose-300 block";
                    ghStatusMsg.textContent = "❌ Error: " + err.message;
                }} finally {{
                    ghSubmitPrBtn.disabled = false;
                }}
            }});

            exportCritiquesBtn.addEventListener('click', showGhModal);
            footerExportBtn.addEventListener('click', showGhModal);
            clearCritiquesBtn.addEventListener('click', () => {{
                if (confirm("Are you sure you want to clear all review notes for this session?")) {{
                    critiques = {{}};
                    localStorage.removeItem(STORAGE_KEY);
                    refreshMarkers();
                }}
            }});

            refreshMarkers();
        }})();
    </script>
</body>
</html>
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_html)
    print(f"[OK] Generated {output_path.name} ({len(blocks)} blocks, {word_count:,} words)")

if __name__ == "__main__":
    for s_num in [1, 2, 3]:
        m_path = MANIFEST_DIR / f"s{s_num}-manifest-v2.json"
        if m_path.exists():
            out_path = OUTPUT_DIR / f"uneraseable-s{s_num}.html"
            generate_html_for_session(m_path, out_path)
