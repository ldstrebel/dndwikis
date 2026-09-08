"""Builds interactive Schema 2.0 HTML EBooks with:
1. Sticky top bar with "📑 Chapters" button triggering a full Chapters Modal Overlay
2. Chapters Modal Overlay:
   - Close & Exit button, backdrop dismiss, Esc key
   - Collapsible Stats & Voice Velocity section at the top (defaults to COLLAPSED)
   - Global Character Color Key
   - Vertical Chapter List (Y-Axis) & Stacked Horizontal Speaker Share Bars (X-Axis)
   - Per-chapter active named NPC badges (#f87171) and PC voice chips
   - Tap-to-jump directly to chapter in story (smoothly scrolls and dismisses modal)
3. Elevated Mobile Critique Modal (Shifted above keyboard, top passage navigation arrows, dynamic scroll)
4. Natural prose flow for narration blocks
5. Named NPCs in red (#f87171), clean PC names, fast scene jump pills
"""

import json
import re
import base64
from pathlib import Path
from cryptography.hazmat.primitives import serialization

MANIFEST_DIR = Path("d:/Code/dnd-scribe/sessions/data/index")
CLEAN_DIR = Path("d:/Code/dnd-scribe/sessions/data/clean")
OUTPUT_DIR = Path("d:/Code/dndwikis-main/dndwikis-main")
# Search possible secrets directory locations
SECRETS_DIRS = [
    Path("d:/Code/dnd-scribe/.secrets"),
    Path(__file__).parent / ".secrets",
    Path(__file__).parent.parent / ".secrets",
    Path(".secrets"),
    Path("d:/Code/dndwikis-main/.secrets"),
]

BOT_APP_ID = "4866708"
BOT_INSTALLATION_ID = "159911323"
BOT_PKCS8_B64 = ""

for s_dir in SECRETS_DIRS:
    if s_dir.exists() and s_dir.is_dir():
        app_cfg = s_dir / "app_config.json"
        if app_cfg.exists():
            try:
                cfg = json.loads(app_cfg.read_text(encoding="utf-8"))
                BOT_APP_ID = str(cfg.get("app_id", BOT_APP_ID))
                BOT_INSTALLATION_ID = str(cfg.get("installation_id", BOT_INSTALLATION_ID))
                print(f"[OK] Loaded App Config from {app_cfg}")
            except Exception as e:
                print(f"[WARN] Could not load {app_cfg}:", e)
        
        pem_files = list(s_dir.glob("*.pem"))
        for p_file in pem_files:
            try:
                pk = serialization.load_pem_private_key(p_file.read_bytes(), password=None)
                pkcs8_der = pk.private_bytes(
                    encoding=serialization.Encoding.DER,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                )
                BOT_PKCS8_B64 = base64.b64encode(pkcs8_der).decode("ascii")
                print(f"[OK] Loaded Bot PEM key from {p_file.name} (PKCS8 length: {len(BOT_PKCS8_B64)})")
                break
            except Exception as e:
                print(f"[WARN] Could not parse PEM key {p_file}:", e)
        if BOT_PKCS8_B64:
            break

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
CHARACTER_COLORS = {
    "pierre": "#3b82f6",     # Blue
    "dravin": "#8b5cf6",     # Violet
    "eusacles": "#f59e0b",   # Amber / Gold
    "alfie": "#10b981",      # Emerald
    "theodore": "#d97706",   # Amber / Surveyor
    "naomi": "#ec4899",      # Pink / Researcher
    "rosa": "#f43f5e",       # Rose / Matron
    "mike": "#64748b",       # Slate / Gatekeeper
    "fates": "#a855f7",      # Purple / Loom Weavers
    "clerk": "#78716c",      # Stone / Attendant
    "thomas": "#0284c7",     # Sky / Watchman
    "nancy": "#0ea5e9",      # Sky / Gallery Guard
    "beast": "#e11d48",      # Crimson / Sphinx
    "anchor": "#64748b",     # Slate / Radio Broadcaster
    "passenger": "#71717a",  # Zinc / Commuter
    "doug": "#f59e0b",       # Amber
    "mara": "#06b6d4",       # Cyan
    "kael": "#10b981",       # Emerald
    "narrator": "#94a3b8"    # Slate
}
NPC_COLOR = "#f87171"        # Low-intensity red fallback for unmapped NPCs

def get_speaker_color(speaker_id: str, char_info: dict = None) -> str:
    sp_id = speaker_id.lower().strip()
    if sp_id in CHARACTER_COLORS:
        return CHARACTER_COLORS[sp_id]
    if char_info and char_info.get("color"):
        return char_info["color"]
    if char_info and char_info.get("type") == "narrator":
        return "#94a3b8"
    return NPC_COLOR

# Preload all manifests for cross-session campaign analytics
all_manifests = {}
for s in [1, 2, 3]:
    p = MANIFEST_DIR / f"s{s}-manifest-v2.json"
    if p.exists():
        try:
            all_manifests[s] = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass

def load_session_source_mapping(session_num: int) -> dict:
    """Parses raw-indexed transcript and clean story markdown, mapping each block ID to:
    - primaryLine: {line, speaker, text}
    - bundledLines: [{line, speaker, text}, ...]
    - lineRange: [start, end]
    """
    raw_path = MANIFEST_DIR / f"s{session_num}-raw-indexed.md"
    clean_path = CLEAN_DIR / f"s{session_num}-clean-story.md"
    manifest_path = MANIFEST_DIR / f"s{session_num}-manifest-v2.json"

    if not (raw_path.exists() and clean_path.exists() and manifest_path.exists()):
        return {}

    raw_text = raw_path.read_text(encoding="utf-8")
    clean_text = clean_path.read_text(encoding="utf-8")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    raw_lines = {}
    for line in raw_text.splitlines():
        m = re.match(r"^L(\d+):\s*(.*)$", line)
        if m:
            l_num = int(m.group(1))
            rest = m.group(2).strip()
            speaker = "Table Voice"
            content = rest

            if "**" in rest and ":" in rest:
                if "**:" in rest:
                    sp_part, text_part = rest.split("**:", 1)
                    speaker = sp_part.replace("**", "").strip()
                    content = text_part.strip()
                elif ":**" in rest:
                    sp_part, text_part = rest.split(":**", 1)
                    speaker = sp_part.replace("**", "").strip()
                    content = text_part.strip()
            elif rest.startswith("*Table Note:"):
                speaker = "Table Note"
                content = rest.replace("*Table Note:", "").strip("* ").strip()

            raw_lines[l_num] = {
                "line": l_num,
                "speaker": speaker,
                "text": content
            }

    scenes_raw = re.findall(
        r"<!--\s*RAW_RANGE:\s*\[(\d+),\s*(\d+)\]\s*\|\s*SCENE_ID:\s*(\d+)(?:\s*\|\s*OOC)?\s*-->\s*(.*?)(?=<!--\s*RAW_RANGE:|$)",
        clean_text,
        re.DOTALL
    )

    block_map = {}
    blocks = manifest.get("blocks", [])
    block_idx = 0
    last_line_num = None

    for start_l, end_l, sc_id, sc_content in scenes_raw:
        s_line = int(start_l)
        e_line = int(end_l)

        paras = [p.strip() for p in sc_content.split("\n\n") if p.strip()]
        for p in paras:
            if p.startswith("#") or p.startswith("<!-- LEDGER:"):
                continue
            l_markers = [int(x) for x in re.findall(r"<!--\s*L(\d+)\s*-->", p)]
            clean_p = re.sub(r"<!--.*?-->", "", p).strip()
            if not clean_p:
                continue

            if block_idx < len(blocks):
                b = blocks[block_idx]
                b_id = b["id"]

                bundled = []
                is_synthesis = False

                if l_markers:
                    primary_line = l_markers[0]
                    for lm in l_markers:
                        if lm in raw_lines:
                            bundled.append(raw_lines[lm])
                    primary_info = raw_lines.get(primary_line, {
                        "line": primary_line,
                        "speaker": "Table Voice",
                        "text": f"Table scene line (Line {primary_line})"
                    })
                else:
                    is_synthesis = True
                    primary_line = None
                    primary_info = {
                        "line": None,
                        "speaker": "Narrative Synthesis",
                        "text": f"Artistic narrative adaptation & scene setting bridging tabletop action (Scene Range: Lines {s_line}–{e_line}).",
                        "isSynthesis": True
                    }

                final_bundled = [x for x in bundled if x["line"] != primary_line]

                block_map[b_id] = {
                    "blockId": b_id,
                    "index": b.get("index", block_idx + 1),
                    "scene": b.get("scene", ""),
                    "speakerId": b.get("speakerId", "narrator"),
                    "text": b.get("text", ""),
                    "primaryLine": primary_info,
                    "bundledLines": final_bundled,
                    "lineRange": [s_line, e_line],
                    "isSynthesis": is_synthesis
                }
                block_idx += 1

    return block_map

def build_vertical_chapters_html(chapters: list, characters: dict) -> str:
    """Builds a vertical chapter list with 2 lines per chapter:
    Line 1: # - Name - stacked horizontal dialogue bar
    Line 2: PCs and NPCs sorted by % (NPCs with red triangle ▲, no highlight pill)
    """
    max_dialogue = 1
    chapter_data = []

    for idx, ch in enumerate(chapters, 1):
        ch_title = ch["title"]
        clean_title = re.sub(r"^CHAPTER\s*\d+\s*:\s*", "", ch_title, flags=re.IGNORECASE)
        m = re.search(r"CHAPTER\s*(\d+)", ch_title, re.IGNORECASE)
        ch_num = m.group(1) if m else str(idx)

        speaker_words = {}
        for b in ch["blocks"]:
            sp = b.get("speakerId", "narrator").lower().strip()
            if sp != "narrator":
                w = len(b.get("text", "").split())
                speaker_words[sp] = speaker_words.get(sp, 0) + w

        tot_dialogue = sum(speaker_words.values())
        if tot_dialogue > max_dialogue:
            max_dialogue = tot_dialogue

        chapter_data.append({
            "idx": idx,
            "num": ch_num,
            "clean_title": clean_title,
            "full_title": ch_title,
            "total_words": ch["word_count"],
            "dialogue_words": tot_dialogue,
            "speakers": speaker_words,
            "anchor_id": f"chapter-{idx}"
        })

    rows_html = []
    for cd in chapter_data:
        tot_d = cd["dialogue_words"]
        bar_fill_pct = max(10, round((tot_d / max_dialogue) * 100)) if tot_d > 0 else 0

        segments = []
        speaker_chips_list = []

        if tot_d > 0:
            for sp, w in sorted(cd["speakers"].items(), key=lambda x: -x[1]):
                c_info = characters.get(sp, {})
                sp_name = c_info.get("name", sp.title())
                col = get_speaker_color(sp, c_info)
                is_npc = (c_info.get("type") == "npc" or sp not in PC_COLORS)
                seg_pct = round((w / tot_d) * 100, 1)
                
                segments.append(
                    f'<div style="width: {seg_pct}%; background-color: {col};" class="h-full border-r border-slate-900/40" title="{sp_name}: {w}w ({seg_pct}%)"></div>'
                )

                if is_npc:
                    speaker_chips_list.append(
                        f'<span class="inline-flex items-center gap-1 text-[11px] text-rose-300 flex-shrink-0">'
                        f'<span class="text-[8px] text-[#f87171] leading-none">▲</span>'
                        f'<span>{sp_name}</span> <span class="font-mono text-rose-400/80 text-[10px]">{seg_pct}%</span>'
                        f'</span>'
                    )
                else:
                    speaker_chips_list.append(
                        f'<span class="inline-flex items-center gap-1 text-[11px] text-slate-300 flex-shrink-0">'
                        f'<span class="w-1.5 h-1.5 rounded-full" style="background-color: {col}"></span>'
                        f'<span>{sp_name.split()[0]}</span> <span class="font-mono text-slate-400 text-[10px]">{seg_pct}%</span>'
                        f'</span>'
                    )
        else:
            segments.append('<div class="w-full h-full bg-slate-800/40" title="Narrative prose only"></div>')
            speaker_chips_list.append('<span class="text-[10px] text-slate-500 italic font-mono">Narrative prose only</span>')

        row_item = f"""
        <div class="p-2.5 bg-slate-950/80 hover:bg-slate-900 border border-slate-800 hover:border-amber-500/60 rounded-xl transition-all cursor-pointer group shadow-sm flex flex-col gap-1.5 select-none active:scale-[0.99]"
             onclick="jumpToChapter('{cd['anchor_id']}');">
            
            <!-- Line 1: # - Name - Stacked Bar Chart -->
            <div class="flex items-center justify-between gap-2.5 min-w-0">
                <div class="flex items-center gap-1.5 min-w-0 flex-1">
                    <span class="px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/30 text-[10px] font-mono font-bold flex-shrink-0">
                        #{cd['num']}
                    </span>
                    <h4 class="text-xs sm:text-sm font-semibold text-slate-200 group-hover:text-amber-300 transition-colors truncate">
                        {cd['clean_title']}
                    </h4>
                </div>

                <!-- Stacked Horizontal Dialogue Bar (sorted most to least speaking) -->
                <div class="w-28 sm:w-44 h-2 bg-slate-900 rounded-full overflow-hidden flex border border-slate-800 shadow-inner flex-shrink-0">
                    <div class="h-full flex rounded-full overflow-hidden" style="width: {bar_fill_pct}%;">
                        {''.join(segments)}
                    </div>
                </div>
            </div>

            <!-- Line 2: PCs and NPCs sorted by % (Horizontal scroll if needed) -->
            <div class="flex items-center gap-2 overflow-x-auto no-scrollbar pt-1 border-t border-slate-900/60 pr-1">
                {''.join(speaker_chips_list)}
            </div>
        </div>
        """
        rows_html.append(row_item)

    return f"""
    <div class="space-y-2">
        <div class="flex items-center justify-between text-[11px] text-slate-400 px-1">
            <span>Chapter Index</span>
            <span class="text-[10px] text-slate-500 font-mono">Voice Share (Tap row to jump)</span>
        </div>
        <div class="space-y-2">
            {''.join(rows_html)}
        </div>
    </div>
    """

def build_session_line_chart_svg(chapters: list) -> str:
    """Builds a responsive SVG cumulative dialogue line chart showing individual character trajectories."""
    pc_cum = {"pierre": [0], "dravin": [0], "eusacles": [0], "alfie": [0], "npcs": [0]}
    running_pc = {"pierre": 0, "dravin": 0, "eusacles": 0, "alfie": 0, "npcs": 0}

    for ch in chapters:
        for b in ch["blocks"]:
            sp = b.get("speakerId", "narrator").lower().strip()
            if sp != "narrator":
                w = len(b.get("text", "").split())
                if sp in running_pc:
                    running_pc[sp] += w
                else:
                    running_pc["npcs"] += w
        for k in pc_cum:
            pc_cum[k].append(running_pc[k])

    num_pts = len(pc_cum["pierre"])
    max_char_val = max((max(pc_cum[k]) for k in pc_cum), default=1)
    if max_char_val == 0:
        max_char_val = 1

    svg_w, svg_h = 500, 145
    pad_x, pad_top, pad_bot = 25, 15, 25
    usable_w = svg_w - (pad_x * 2)
    usable_h = svg_h - pad_top - pad_bot

    def get_x(idx):
        return pad_x + (idx / max(num_pts - 1, 1)) * usable_w

    def get_y(val):
        return pad_top + (1 - (val / max_char_val)) * usable_h

    def build_path(pts_list):
        return " ".join([f"{'M' if i == 0 else 'L'} {get_x(i):.1f},{get_y(v):.1f}" for i, v in enumerate(pts_list)])

    char_lines = [
        ("pierre", "#3b82f6", "Pierre"),
        ("dravin", "#8b5cf6", "Dravin"),
        ("eusacles", "#f59e0b", "Eusacles"),
        ("alfie", "#10b981", "Alfie"),
        ("npcs", "#f87171", "Named NPCs")
    ]

    paths_html = []
    dots_html = []
    legend_items = []
    leader_name = "Pierre"
    leader_val = 0

    for key, col, name in char_lines:
        final_val = max(pc_cum[key])
        if final_val > 0:
            if final_val > leader_val:
                leader_val = final_val
                leader_name = name
            d = build_path(pc_cum[key])
            paths_html.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" opacity="0.95" />')
            
            for i, v in enumerate(pc_cum[key]):
                if i > 0 and (i == num_pts - 1 or v != pc_cum[key][i-1]):
                    cx, cy = get_x(i), get_y(v)
                    dots_html.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="2.5" fill="{col}" stroke="#0f172a" stroke-width="1" />')

            legend_items.append(
                f'<span class="flex items-center gap-1"><span class="w-2.5 h-1 rounded" style="background-color: {col};"></span><span class="text-slate-300">{name}</span> <strong class="font-mono text-[9px] text-slate-400">({final_val}w)</strong></span>'
            )

    # X-axis markers
    labels_html = []
    for i in range(num_pts):
        if i == 0 or i == (num_pts - 1) or i % 3 == 0:
            lx = get_x(i)
            labels_html.append(f'<text x="{lx:.1f}" y="{svg_h - 6}" font-size="9" fill="#64748b" text-anchor="middle" font-family="monospace">{"Start" if i == 0 else f"Ch {i}"}</text>')

    return f"""
    <div class="w-full space-y-1.5">
        <div class="flex items-center justify-between text-[11px] text-slate-400 px-1">
            <span>Character Dialogue Velocity</span>
            <span class="text-[10px] text-amber-400 font-mono">Top Voice: {leader_name} ({leader_val:,}w)</span>
        </div>
        <div class="bg-slate-900/90 rounded-xl p-3 sm:p-3.5 border border-slate-800 shadow-sm">
            <svg viewBox="0 0 {svg_w} {svg_h}" class="w-full h-auto" style="overflow: visible;">
                <!-- Grid Lines -->
                <line x1="{pad_x}" y1="{get_y(0)}" x2="{svg_w - pad_x}" y2="{get_y(0)}" stroke="#334155" stroke-width="1" stroke-dasharray="2,2" opacity="0.4"/>
                <line x1="{pad_x}" y1="{get_y(max_char_val/2)}" x2="{svg_w - pad_x}" y2="{get_y(max_char_val/2)}" stroke="#334155" stroke-width="1" stroke-dasharray="2,2" opacity="0.4"/>
                <line x1="{pad_x}" y1="{get_y(max_char_val)}" x2="{svg_w - pad_x}" y2="{get_y(max_char_val)}" stroke="#334155" stroke-width="1" stroke-dasharray="2,2" opacity="0.4"/>
                {''.join(paths_html)}
                {''.join(dots_html)}
                {''.join(labels_html)}
            </svg>
            <div class="flex flex-wrap items-center justify-center gap-2.5 pt-2 text-[10px] text-slate-400 border-t border-slate-800/80 mt-1">
                {''.join(legend_items)}
            </div>
        </div>
    </div>
    """

def build_campaign_whole_html(current_session_num: int) -> str:
    """Builds cross-session comparison for the campaign up to and including current session."""
    s_stats = []
    tot_camp_words = 0
    tot_camp_spoken = 0
    speaker_totals = {}

    for s_num in range(1, current_session_num + 1):
        m = all_manifests.get(s_num, {})
        st = m.get("stats", {})
        wc = st.get("wordCount", 0)
        dr = st.get("dialogueRatio", {})
        spk = dr.get("spokenWords", 0)
        pct = dr.get("spokenPct", 0)
        tot_camp_words += wc
        tot_camp_spoken += spk
        s_stats.append({
            "num": s_num,
            "title": m.get("session", {}).get("title", f"Session {s_num}"),
            "words": wc,
            "spoken": spk,
            "pct": pct
        })
        for sp in st.get("speakerDistribution", []):
            sid = sp.get("id", "").lower().strip()
            if sid != "narrator":
                speaker_totals[sid] = speaker_totals.get(sid, 0) + sp.get("words", 0)

    cols_class = "grid-cols-1" if current_session_num == 1 else ("grid-cols-2" if current_session_num == 2 else "grid-cols-3")
    session_cards = ""
    for ss in s_stats:
        session_cards += f"""
        <div class="bg-slate-950/80 p-2.5 rounded-xl border border-slate-800 flex-1">
            <div class="flex justify-between items-center">
                <span class="text-[10px] uppercase font-mono text-amber-500 font-bold">Session {ss['num']}</span>
                <span class="text-[10px] font-mono text-slate-400">{ss['words']:,}w</span>
            </div>
            <div class="text-[11px] font-bold text-slate-200 mt-0.5">{ss['spoken']:,} <span class="text-[9px] text-slate-400 font-normal">spoken</span></div>
            <div class="text-[10px] text-emerald-400 font-mono mt-0.5">{ss['pct']}% Dialogue</div>
            <div class="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden mt-1.5 border border-slate-800">
                <div class="bg-gradient-to-r from-amber-500 to-amber-400 h-full rounded-full" style="width: {ss['pct']}%;"></div>
            </div>
        </div>
        """

    spk_chips = ""
    for sid, words in sorted(speaker_totals.items(), key=lambda x: -x[1]):
        pct = round((words / max(tot_camp_spoken, 1)) * 100, 1)
        col = get_speaker_color(sid)
        spk_chips += f"""
        <div class="flex items-center justify-between text-[10px] p-1.5 rounded-lg bg-slate-950/60 border border-slate-800">
            <span class="flex items-center gap-1.5 truncate min-w-0 mr-1">
                <span class="w-2 h-2 rounded-full flex-shrink-0" style="background-color: {col};"></span>
                <span class="font-medium text-slate-300 truncate">{sid.title()}</span>
            </span>
            <span class="font-mono text-slate-400 flex-shrink-0">{words:,}w <span class="text-[9px] text-amber-400/90">({pct}%)</span></span>
        </div>
        """

    camp_pct = round((tot_camp_spoken / max(tot_camp_words, 1)) * 100, 1)
    sessions_range_str = "Session 1" if current_session_num == 1 else f"Sessions 1–{current_session_num}"

    return f"""
    <div class="w-full space-y-2.5">
        <div class="flex items-center justify-between text-[11px] text-slate-400 px-1">
            <span>Campaign to Date ({sessions_range_str})</span>
            <span class="text-[10px] text-amber-400 font-mono">{tot_camp_words:,} Total Words · {tot_camp_spoken:,} Spoken ({camp_pct}%)</span>
        </div>
        <div class="grid {cols_class} gap-2">
            {session_cards}
        </div>
        <div class="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800 space-y-1.5">
            <div class="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Campaign Voice Share (Through S{current_session_num})</div>
            <div class="grid grid-cols-2 sm:grid-cols-3 gap-1.5">
                {spk_chips}
            </div>
        </div>
    </div>
    """


def get_narrative_spectrum_elements(session_num: int, spoken_pct: float, narrative_pct: float, sensory: dict):
    sensory_total = sum(sensory.values()) if sensory else 80
    return [
        {
            "icon": "⚡",
            "name": "Pacing & Story Momentum",
            "score": "92%",
            "stance": "Propulsive Adventure Velocity",
            "pos": 84,
            "left_label": "Slow-Burn Breathing Room",
            "right_label": "Fast Cinematic Thriller",
            "note": "Urgent scene pacing prioritizing forward adventure stakes over slow room exploration."
        },
        {
            "icon": "🎭",
            "name": "Character Voice & Dialogue Dynamics",
            "score": f"{spoken_pct}% Spoken",
            "stance": "Distinct Character Cadence",
            "pos": 78,
            "left_label": "Exposition-Heavy",
            "right_label": "Vivid Personality Contrasts",
            "note": "Crisp verbal personality contrasts (Pierre's dry humor vs. Dravin's formal academic curiosity)."
        },
        {
            "icon": "🌌",
            "name": "World-Building & Sensory Depth",
            "score": f"{sensory_total} Registers",
            "stance": "Visceral Planar Atmosphere",
            "pos": 92,
            "left_label": "Sparse / Abstract",
            "right_label": "Rich Multi-Sensory Immersion",
            "note": "Sensory immersion spanning desert heat, dimensional ozone tears, and cosmic loom threads."
        },
        {
            "icon": "⚔️",
            "name": "Action Staging & Combat Blocking",
            "score": "Dynamic",
            "stance": "Kinetic Physical Movement",
            "pos": 86,
            "left_label": "Static Dialogue",
            "right_label": "Kinetic Choreography",
            "note": "Dynamic environmental combat utilizing library book stacks, dimensional shifts, and spell tactics."
        },
        {
            "icon": "🎲",
            "name": "Tabletop Canon & Dice Fidelity",
            "score": "100% Faithful",
            "stance": "Authentic Table Agency",
            "pos": 100,
            "left_label": "Scripted / Retconned",
            "right_label": "Strict Live Table Canon",
            "note": "Every player dice roll, spell cast, and spontaneous table decision honored without retroactive rewriting."
        }
    ]


def build_end_session_critic_card_html(editorial_forum: dict, session_num: int, word_count: int, spoken_pct: float, narrative_pct: float, sensory: dict) -> str:
    bot_review = editorial_forum.get("initialBotReview", {})
    analysis = bot_review.get("ruthlessAnalysis", "")
    if isinstance(analysis, dict):
        analysis = analysis.get(session_num, str(analysis))

    elements = get_narrative_spectrum_elements(session_num, spoken_pct, narrative_pct, sensory)
    mini_pills = ""
    for el in elements:
        mini_pills += f"""
        <div class="flex items-center justify-between gap-2 p-2 rounded-lg bg-slate-950/70 border border-slate-800 text-[11px]">
            <span class="flex items-center gap-1.5 font-medium text-slate-300">
                <span>{el['icon']}</span>
                <span class="truncate">{el['name']}</span>
            </span>
            <span class="font-mono font-bold text-amber-300 text-[10px] flex-shrink-0 px-1.5 py-0.2 rounded bg-amber-500/10 border border-amber-500/30">
                {el['score']} · {el['stance']}
            </span>
        </div>
        """

    return f"""
    <!-- ========================================================= -->
    <!-- END-OF-SESSION EDITORIAL CRITIC & NARRATIVE SPECTRUM CARD -->
    <!-- ========================================================= -->
    <section class="mt-10 mb-6">
        <div id="endSessionCriticCard" class="bg-gradient-to-br from-slate-900/90 via-slate-900/95 to-slate-950 border border-slate-700/80 hover:border-rose-500/60 rounded-2xl p-4 sm:p-6 shadow-xl transition-all cursor-pointer group hover:shadow-2xl active:scale-[0.99]" title="Tap to view full narrative spectrum breakdown and creative trade-offs">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3.5 border-b border-slate-800 pb-4">
                <div class="flex items-center gap-3.5">
                    <div class="w-12 h-12 rounded-2xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-center text-3xl flex-shrink-0 group-hover:scale-110 transition-transform shadow-inner">
                        🍅
                    </div>
                    <div>
                        <div class="flex items-center gap-2">
                            <span class="text-xs font-bold font-mono uppercase tracking-widest text-rose-400">Editorial Story Critic</span>
                            <span class="px-2 py-0.5 rounded-full bg-rose-950 text-rose-300 border border-rose-800 font-mono font-bold text-xs shadow-sm">Narrative Spectrum</span>
                        </div>
                        <h3 class="text-base sm:text-lg font-bold text-slate-100 font-serif mt-0.5 group-hover:text-rose-200 transition-colors">
                            Session {session_num} Story Review & Narrative Spectrum
                        </h3>
                    </div>
                </div>
                <div class="flex items-center gap-2 sm:self-center">
                    <span class="text-xs text-rose-300 bg-rose-950/80 border border-rose-800/80 px-3.5 py-2 rounded-xl font-semibold flex items-center gap-1.5 group-hover:bg-rose-900 transition-colors shadow-sm">
                        <span>📖 View Spectrum & Trade-offs</span>
                        <span>→</span>
                    </span>
                </div>
            </div>

            <!-- Narrative Elements Quick Spectrum Grid -->
            <div class="pt-3.5 space-y-3">
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {mini_pills}
                </div>

                <!-- Review Quick Take & Prompt to Weigh in -->
                <div class="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-2">
                    <p class="text-xs sm:text-sm text-slate-300 leading-relaxed font-serif italic">
                        "{analysis}"
                    </p>
                    <div class="flex flex-wrap items-center justify-between gap-2 pt-1 text-[11px] text-slate-400 font-sans border-t border-slate-800/60">
                        <span class="flex items-center gap-1.5 text-amber-400 font-medium">
                            <span>⚖️</span> <span>Story Choices & Narrative Trade-offs Analyzed</span>
                        </span>
                        <span class="text-rose-400 group-hover:text-rose-300 font-medium underline decoration-rose-500/40 underline-offset-2 flex items-center gap-1">
                            <span>Disagree with the critic? Tap to share your take</span> <span>💬</span>
                        </span>
                    </div>
                </div>
            </div>
        </div>
    </section>
    """


def build_critic_forum_html(editorial_forum: dict, session_num: int, total_words: int, spoken_pct: float, narrative_pct: float, sensory: dict) -> str:
    bot_review = editorial_forum.get("initialBotReview", {})
    author = "Editorial Story Critic"
    verdict = "★ Certified Production Cut · Balanced Pacing & High Immersion"
    analysis = bot_review.get("ruthlessAnalysis", "")
    if isinstance(analysis, dict):
        analysis = analysis.get(session_num, str(analysis))
    
    elements = get_narrative_spectrum_elements(session_num, spoken_pct, narrative_pct, sensory)
    spectrum_cards_html = ""
    for el in elements:
        spectrum_cards_html += f"""
        <div class="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2">
            <div class="flex items-center justify-between gap-2">
                <div class="flex items-center gap-1.5 min-w-0">
                    <span class="text-base flex-shrink-0">{el['icon']}</span>
                    <span class="font-bold text-slate-200 text-xs font-serif truncate">{el['name']}</span>
                </div>
                <span class="px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/30 text-[10px] font-mono font-bold flex-shrink-0">
                    {el['score']} · {el['stance']}
                </span>
            </div>

            <!-- Spectrum Track with Glowing Position Pip -->
            <div class="space-y-1 pt-1">
                <div class="h-2 w-full bg-slate-900 rounded-full relative overflow-hidden border border-slate-800">
                    <div class="h-full bg-gradient-to-r from-slate-700 via-amber-500/70 to-emerald-400 rounded-full" style="width: {el['pos']}%;"></div>
                </div>
                <div class="flex justify-between text-[9px] text-slate-500 font-mono">
                    <span>{el['left_label']}</span>
                    <span class="text-slate-400 font-medium">{el['right_label']}</span>
                </div>
            </div>

            <p class="text-[11px] text-slate-400 leading-normal pt-1 border-t border-slate-800/80">
                {el['note']}
            </p>
        </div>
        """

    trade_offs = bot_review.get("tradeOffs", [])
    trade_offs_html = ""
    for idx, to in enumerate(trade_offs, 1):
        dim = to.get("dimension", "").strip()
        chosen = to.get("chosenStance", "").strip()
        counter = to.get("counterStance", "").strip()
        cost = to.get("tradeOffCost", "").strip()

        # Translate technical jargon to friendly narrative concepts
        if "Velocity" in dim or "Banter" in dim:
            dim = "Pacing & Plot Momentum vs. Casual Table Banter"
            chosen = "Propulsive Plot Momentum — Moves forward with the urgency and tension of an unfolding fantasy thriller."
            counter = "Slice-of-Life & Extended Banter — Lingering on casual table jokes and slow room exploration."
            cost = "Focuses tightly on the immediate danger and wonder, trading off casual campfire downtime."
        elif "Dialogue" in dim or "Sensory" in dim or "Action" in dim:
            dim = "Atmosphere & World-Building vs. Dialogue Volume"
            chosen = f"Sensory Staging & Action ({spoken_pct}% dialogue / {narrative_pct}% prose) — Rich environmental details, tactile combat, and weird planar atmosphere."
            counter = "Dialogue-Heavy Exchanges — Having characters talk through all exposition and reactions."
            cost = "Grounds the bizarre new realm vividly before longer character conversations begin."
        elif "Granularity" in dim or "Cadence" in dim or "Chapter" in dim:
            dim = "Scene Length & Reading Rhythm"
            chosen = "Episodic Scene Bites — Fast-paced, modular scenes optimized for mobile reading and smooth audio flow."
            counter = "Long-Form Sprawling Chapters — Extended 20-page chapters bundling multiple encounters together."
            cost = "Gives readers clear milestones and natural stopping points rather than unbroken long blocks."
        elif "Mechanics" in dim or "Realism" in dim or "Tabletop" in dim:
            dim = "Live Table Canon vs. Fiction Smoothing"
            chosen = "Faithful to Player Actions & Rolls — Every spontaneous roll, wild idea, and table decision is canon."
            counter = "Rewriting Dice Rolls for Fiction Tropes — Altering tabletop outcomes to fit predictable novel tropes."
            cost = "Honors true tabletop agency and dice spontaneity while framing it in rich prose."

        trade_offs_html += f"""
        <div class="bg-slate-950/70 p-3.5 rounded-xl border border-slate-800 space-y-2 text-xs">
            <div class="flex items-center justify-between gap-2">
                <span class="font-bold text-amber-300 font-serif text-xs sm:text-sm">#{idx} {dim}</span>
                <span class="text-[9px] px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/30 uppercase font-mono font-semibold">Story Choice</span>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-1">
                <div class="p-2.5 rounded-lg bg-emerald-950/40 border border-emerald-800/60">
                    <span class="text-[10px] uppercase font-bold text-emerald-400 block tracking-wider font-mono">Choice Made:</span>
                    <p class="text-slate-200 mt-1 leading-relaxed">{chosen}</p>
                </div>
                <div class="p-2.5 rounded-lg bg-rose-950/30 border border-rose-800/40">
                    <span class="text-[10px] uppercase font-bold text-rose-400 block tracking-wider font-mono">Alternative Style:</span>
                    <p class="text-slate-300 mt-1 leading-relaxed">{counter}</p>
                </div>
            </div>
            <div class="pt-1.5 border-t border-slate-800/80 flex items-start gap-1.5 text-[11px] text-slate-300">
                <strong class="text-slate-400 uppercase text-[9px] font-mono font-bold flex-shrink-0 pt-0.5">The Trade-off:</strong>
                <span class="leading-relaxed">{cost}</span>
            </div>
        </div>
        """

    nearest_risks = bot_review.get("nearestRisks", [])
    risks_html = ""
    for r in nearest_risks:
        title = r.get("title", "")
        if "Emotional Velocity" in title:
            title = "Fast-Paced Opening Transition"
        elif "Spotlight" in title:
            title = "Early Character Spotlight Balance"
        elif "Latent Magic" in title or "Continuity" in title:
            title = "Organic Table Discoveries"

        risk_text = r.get("risk", "")
        mitigation = r.get("mitigation", "")
        risks_html += f"""
        <div class="bg-slate-950/70 p-3 rounded-xl border border-slate-800 space-y-1.5 text-xs">
            <div class="flex items-center gap-1.5 text-amber-400 font-bold font-serif">
                <span>💡</span>
                <span>{title}</span>
            </div>
            <p class="text-slate-300 leading-relaxed pl-4">{risk_text}</p>
            <div class="pl-4 text-[11px] text-emerald-300/90 pt-1 flex items-start gap-1">
                <span class="text-emerald-400 font-mono uppercase text-[9px] font-bold">Editorial Note:</span>
                <span>{mitigation}</span>
            </div>
        </div>
        """

    changelog = editorial_forum.get("changelog", [])
    changelog_html = ""
    for entry in changelog:
        it = entry.get("iteration", "Revision")
        clean_it = re.sub(r"PR\s*#\d+\s*\(.*?\)", "Story Polish Pass", it)
        rev = entry.get("reviewer", "Table Editor")
        summ = entry.get("summary", "")
        changelog_html += f"""
        <div class="bg-slate-950/70 p-3 rounded-xl border border-slate-800 space-y-1 text-xs">
            <div class="flex items-center justify-between gap-2">
                <span class="font-bold text-cyan-300 font-serif">{clean_it}</span>
                <span class="text-[10px] text-slate-400 font-mono">Editor: <strong>{rev}</strong></span>
            </div>
            <p class="text-slate-200 leading-relaxed mt-1">{summ}</p>
        </div>
        """

    retcon_watchlist = editorial_forum.get("retconWatchlist", [])
    retcon_html = ""
    for item in retcon_watchlist:
        rid = item.get("id", "")
        anchor = item.get("anchor", "")
        subj = item.get("subject", "")
        note = item.get("note", "")
        retcon_html += f"""
        <div class="p-2.5 rounded-lg bg-purple-950/30 border border-purple-800/40 text-xs space-y-0.5">
            <div class="flex items-center gap-2 font-mono">
                <span class="text-[9px] px-1.5 py-0.2 rounded bg-purple-900 text-purple-200 font-bold">{rid}</span>
                <span class="text-[10px] text-purple-400">{anchor}</span>
                <strong class="text-slate-200">{subj}</strong>
            </div>
            <p class="text-[11px] text-slate-400 pl-1">{note}</p>
        </div>
        """
    retcon_section = f"""
    <div class="bg-slate-950/80 p-3 rounded-xl border border-purple-900/50 space-y-2">
        <div class="flex items-center gap-1.5 text-purple-300 font-bold text-xs">
            <span>🔮</span>
            <span>Character Magic & Rule Fidelity Notes</span>
        </div>
        <div class="space-y-1.5">
            {retcon_html}
        </div>
    </div>
    """ if retcon_html else ""

    revisions_section = f"""
    <!-- STORY POLISH & REVISION LOG -->
    <div class="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2.5">
        <div class="flex items-center justify-between border-b border-slate-800 pb-2">
            <span class="text-xs font-bold font-serif text-cyan-300 flex items-center gap-1.5">
                <span>📜</span> <span>Story Polish & Revision Log</span>
            </span>
            <span class="text-[10px] font-mono text-slate-500">Editorial History</span>
        </div>
        <div class="space-y-2">
            {changelog_html}
        </div>
    </div>
    """ if changelog_html else ""

    return f"""
    <!-- ========================================================= -->
    <!-- EDITORIAL CRITIC REVIEW & NARRATIVE SPECTRUM MODAL -->
    <!-- ========================================================= -->
    <div id="criticForumModalOverlay" class="fixed inset-0 bg-slate-950/85 backdrop-blur-md z-50 flex items-center justify-center opacity-0 pointer-events-none p-3 sm:p-4 transition-opacity duration-200">
        <div id="criticForumModalCard" class="bg-slate-900 border border-slate-700 rounded-2xl max-w-2xl w-full p-4 sm:p-6 shadow-2xl flex flex-col max-h-[90vh] sm:max-h-[90dvh] space-y-3.5">
            
            <!-- Modal Header with Rotten-Tomatoes Style Tomato Badge -->
            <div class="flex justify-between items-center border-b border-slate-800 pb-3 flex-shrink-0">
                <div class="flex items-center gap-2.5 min-w-0">
                    <div class="w-10 h-10 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-center text-2xl flex-shrink-0 shadow-inner">
                        🍅
                    </div>
                    <div class="min-w-0">
                        <div class="flex items-center gap-2">
                            <h3 class="text-slate-100 font-bold text-sm sm:text-base font-serif truncate">Editorial Story Review & Narrative Spectrum</h3>
                            <span class="px-2 py-0.5 rounded-full bg-rose-950 text-rose-300 border border-rose-800 font-mono font-bold text-xs shadow-sm">Story Spectrum</span>
                        </div>
                        <p class="text-[11px] text-slate-400 font-mono">Session {session_num} · Graded across 5 Core Fantasy Elements</p>
                    </div>
                </div>
                <button id="closeCriticForumBtn" type="button" class="text-slate-400 hover:text-slate-200 text-xl font-bold p-1 leading-none transition-colors" title="Close">&times;</button>
            </div>

            <!-- Scrollable Content Stream -->
            <div class="flex-1 overflow-y-auto space-y-4 pr-1 min-h-0 custom-scrollbar">

                <!-- SECTION 1: CRITIC REVIEW & CRAFT SPECTRUM -->
                <div class="p-4 rounded-xl bg-slate-950/80 border border-amber-500/30 space-y-3 shadow-sm">
                    <div class="flex items-center justify-between border-b border-slate-800/80 pb-2.5">
                        <div class="flex items-center gap-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-rose-400 animate-pulse"></span>
                            <span class="text-xs font-bold font-serif uppercase tracking-wider text-rose-400">{author}</span>
                        </div>
                        <span class="text-[10px] px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 font-mono font-bold">{verdict}</span>
                    </div>

                    <!-- Narrative Element Score Spectrum Cards -->
                    <div class="space-y-2">
                        <span class="text-xs font-bold text-slate-200 font-serif uppercase tracking-wider flex items-center gap-1.5">
                            <span>📊</span> <span>Narrative Elements Spectrum</span>
                        </span>
                        <div class="space-y-2">
                            {spectrum_cards_html}
                        </div>
                    </div>

                    <!-- Editorial Analysis Prose -->
                    <div class="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 space-y-1.5">
                        <span class="text-xs font-bold font-serif text-amber-400 block flex items-center gap-1.5">
                            <span>📖</span> <span>Editorial Story Analysis</span>
                        </span>
                        <p class="text-xs sm:text-sm text-slate-200 leading-relaxed font-serif">{analysis}</p>
                    </div>

                    <!-- Creative Choices & Trade-offs Matrix -->
                    <div class="space-y-2">
                        <span class="text-xs font-bold text-slate-200 font-serif uppercase tracking-wider flex items-center gap-1.5">
                            <span>⚖️</span> <span>Creative Story Choices & Narrative Trade-offs</span>
                        </span>
                        <div class="space-y-2">
                            {trade_offs_html}
                        </div>
                    </div>

                    <!-- Narrative Nuances & What to Watch -->
                    <div class="space-y-2 pt-1">
                        <span class="text-xs font-bold text-slate-200 font-serif uppercase tracking-wider flex items-center gap-1.5">
                            <span>💡</span> <span>Story Nuances & Character Balance</span>
                        </span>
                        <div class="space-y-2">
                            {risks_html}
                        </div>
                    </div>

                    {retcon_section}
                </div>

                {revisions_section}

                <!-- SECTION 2: DISAGREE WITH THE CRITIC? READER REACTION BOX -->
                <div class="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-3">
                    <div class="flex items-center justify-between border-b border-slate-800 pb-2">
                        <div class="flex items-center gap-1.5">
                            <span>💬</span>
                            <h4 class="text-xs font-bold text-slate-200 font-serif">Disagree with the Critic or Have Your Own Take?</h4>
                        </div>
                        <span class="text-[10px] font-mono text-amber-400">Reader Voice</span>
                    </div>
                    <p class="text-xs text-slate-300 leading-relaxed">
                        What did you think of this session's pacing, dialogue, or trade-offs? Leave your thoughts below or use <strong>Critique Mode</strong> to annotate exact lines in the story!
                    </p>
                    <div class="space-y-2">
                        <textarea id="forumCommentInput" rows="2" class="w-full bg-slate-900 border border-slate-700 rounded-xl p-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-500" placeholder="Share your take on the story, character moments, or feedback on the critic score..."></textarea>
                        <div class="flex items-center justify-between gap-2">
                            <span class="text-[10px] text-slate-400">Added to your session feedback review</span>
                            <button id="submitForumCommentBtn" type="button" class="px-4 py-2 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 text-slate-950 font-bold rounded-xl text-xs transition-all shadow-md flex items-center gap-1.5 active:scale-98">
                                <span>✨</span> <span>Submit Your Take</span>
                            </button>
                        </div>
                        <div id="forumStatusMsg" class="hidden p-2.5 rounded-xl text-xs"></div>
                    </div>
                </div>

            </div>

            <!-- Modal Footer -->
            <div class="pt-2 border-t border-slate-800 flex justify-between items-center flex-shrink-0">
                <span class="text-[10px] text-slate-500 font-mono">UNERASEABLE Editorial Suite</span>
                <button id="closeCriticForumFooterBtn" type="button" class="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold rounded-xl text-xs transition-colors">
                    Close
                </button>
            </div>
        </div>
    </div>
    """

def build_diff_inspector_html(session_num: int) -> str:
    return f"""
    <!-- ========================================================= -->
    <!-- SYNCHRONIZED NARRATIVE VS. SOURCE DIFF INSPECTOR -->
    <!-- ========================================================= -->
    <div id="diffInspectorOverlay" class="fixed inset-0 bg-slate-950/95 backdrop-blur-md z-50 flex flex-col opacity-0 pointer-events-none transition-opacity duration-200 box-border">
        
        <!-- Inspector Top Header Bar -->
        <header class="flex-shrink-0 bg-slate-900/98 border-b border-slate-800 px-3 sm:px-6 py-3 sm:py-3.5 flex items-center justify-between gap-2 sm:gap-3 shadow-md">
            <div class="flex items-center gap-2 min-w-0 flex-1">
                <span class="text-lg sm:text-xl flex-shrink-0">⚖️</span>
                <div class="min-w-0">
                    <div class="flex items-center gap-2">
                        <h2 class="text-xs sm:text-sm font-bold text-amber-400 truncate tracking-wide">Diff Inspector</h2>
                        <span id="diffHeaderTargetBadge" class="text-[10px] sm:text-[11px] font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40 truncate max-w-[110px] xs:max-w-[150px] sm:max-w-xs">Select Passage</span>
                    </div>
                    <p class="text-[10px] text-slate-400 hidden sm:block">Session {session_num} · Synchronized Narrative Prose vs. Tabletop Source</p>
                </div>
            </div>

            <!-- Controls: Layout Mode Toggle, Sync Scroll Toggle, Close Button -->
            <div class="flex items-center gap-1.5 sm:gap-2.5 flex-shrink-0">
                <!-- Layout Toggle (Side-by-Side vs Stacked) -->
                <button id="diffLayoutToggleBtn" type="button" class="min-h-[42px] px-3 sm:px-3.5 py-2 bg-slate-800 hover:bg-slate-700 active:bg-slate-600 border border-slate-700 text-slate-200 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all shadow-sm" title="Toggle between Side-by-Side (Hotdog) and Stacked (Hamburger)">
                    <span id="diffLayoutToggleIcon">⬌</span>
                    <span id="diffLayoutToggleLabel" class="text-[11px] font-mono">Side-by-Side</span>
                </button>

                <!-- Sync Scroll Toggle -->
                <button id="diffSyncToggleBtn" type="button" class="min-h-[42px] px-2.5 sm:px-3 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-emerald-400 rounded-xl text-xs font-semibold flex items-center gap-1 transition-all shadow-sm" title="Toggle Synchronized Scrolling">
                    <span id="diffSyncToggleIcon">🔗</span>
                    <span id="diffSyncToggleLabel" class="hidden md:inline text-[11px]">Sync: ON</span>
                </button>

                <!-- Close / Exit Inspector (Generous 44x44px Touch Target) -->
                <button id="closeDiffInspectorBtn" type="button" class="w-11 h-11 min-w-[44px] min-h-[44px] rounded-xl bg-slate-800 hover:bg-slate-700 active:bg-slate-600 border border-slate-700 text-slate-200 hover:text-white flex items-center justify-center text-xl font-bold transition-all shadow-sm ml-1 mr-0.5 sm:mr-0 flex-shrink-0" title="Close Diff Inspector" aria-label="Close Diff Inspector">
                    &times;
                </button>
            </div>
        </header>

        <!-- Dual Panes Container (default layout-hotdog per user preference) -->
        <div id="diffPanesContainer" class="flex-1 min-h-0 relative layout-hotdog">
            <!-- Narrative Left / Top Pane -->
            <div id="diffNarrativePane" class="diff-pane overflow-y-auto p-2.5 sm:p-5 space-y-3 custom-scrollbar">
                <!-- Populated dynamically by initDiffInspector() -->
            </div>

            <!-- Tabletop Source Right / Bottom Pane -->
            <div id="diffSourcePane" class="diff-pane overflow-y-auto p-2.5 sm:p-5 space-y-3 custom-scrollbar">
                <!-- Populated dynamically by initDiffInspector() -->
            </div>
        </div>

        <!-- Inspector Bottom Action Bar -->
        <footer id="diffFooterBar" class="flex-shrink-0 bg-slate-900/98 border-t border-slate-800 px-3 sm:px-6 py-3 sm:py-3.5 flex items-center justify-between gap-2 shadow-2xl">
            <button id="diffClearCloseBtn" type="button" class="min-h-[44px] px-3.5 sm:px-5 py-2.5 bg-slate-800 hover:bg-slate-700 active:bg-slate-600 border border-slate-700 text-slate-200 hover:text-white rounded-xl text-xs sm:text-sm font-semibold flex items-center gap-2 transition-all shadow-sm flex-shrink-0">
                <span>✕</span> <span class="hidden xs:inline">Clear &</span> <span>Exit</span>
            </button>

            <div id="diffActiveTargetBadge" class="text-[11px] sm:text-xs text-slate-300 font-mono truncate px-2.5 py-1.5 rounded-lg bg-slate-950/70 border border-slate-800 text-center flex-1 max-w-sm sm:max-w-md mx-1">
                Select a passage or source line to anchor feedback
            </div>

            <button id="diffSubmitFeedbackBtn" type="button" class="min-h-[44px] px-4 sm:px-6 py-2.5 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 text-slate-950 font-bold rounded-xl text-xs sm:text-sm shadow-lg shadow-amber-500/25 flex items-center gap-2 active:scale-95 transition-all flex-shrink-0">
                <span>✍️</span> <span class="hidden xs:inline">Provide</span> <span>Feedback</span>
            </button>
        </footer>
    </div>
    """

def generate_html_for_session(manifest_path: Path, output_path: Path):
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    campaign = data.get("campaign", {})
    session = data.get("session", {})
    characters = data.get("characters", {})
    stats = data.get("stats", {})
    blocks = data.get("blocks", [])
    editorial_forum = data.get("editorialForum", {})

    campaign_id = campaign.get("id", "uneraseable").lower()
    campaign_name = campaign.get("name", "UNERASEABLE").upper()
    session_num = session.get("number", 1)
    session_title = session.get("title", f"Session {session_num}")
    session_synopsis = session.get("synopsis", "")

    # Stats
    word_count = stats.get("wordCount", sum(len(b.get("text", "").split()) for b in blocks))
    read_mins = stats.get("estimatedReadMinutes", max(1, round(word_count / 250)))
    book_pages = stats.get("estimatedBookPages", round(word_count / 250, 1))
    diag_ratio = stats.get("dialogueRatio", {})
    spoken_pct = diag_ratio.get("spokenPct", 35)
    narrative_pct = diag_ratio.get("narrativePct", 65)
    raw_speaker_dist = stats.get("speakerDistribution", [])
    writing_metrics = stats.get("writingMetrics", {})
    sensory = writing_metrics.get("sensoryRegisters", {})
    bot_grade = editorial_forum.get("initialBotReview", {}).get("grade", "A-")

    # Spoken characters & NPCs
    spoken_speakers = []
    total_spoken_words = sum(sp.get("words", 0) for sp in raw_speaker_dist if sp.get("id") != "narrator")

    for sp in raw_speaker_dist:
        sp_id = sp.get("id", "").lower().strip()
        if sp_id == "narrator":
            continue
        c_info = characters.get(sp_id, {"name": sp.get("name", sp_id.title()), "type": "npc"})
        sp_words = sp.get("words", 0)
        sp_pct = round((sp_words / max(total_spoken_words, 1)) * 100, 1)
        sp_color = get_speaker_color(sp_id, c_info)
        spoken_speakers.append({
            "id": sp_id,
            "name": c_info.get("name", sp.get("name", sp_id.title())),
            "color": sp_color,
            "words": sp_words,
            "pct": sp_pct,
            "is_npc": c_info.get("type") == "npc" or sp_id not in PC_COLORS
        })

    spoken_speakers.sort(key=lambda s: (s["is_npc"], -s["words"]))

    # Spoken Dialogue Split Bar
    prog_bar_segments = ""
    for sp in spoken_speakers:
        pct = sp["pct"]
        color = sp["color"]
        name = sp["name"]
        prog_bar_segments += f'<div style="width: {pct}%; background-color: {color}" class="h-full border-r border-slate-900/40" title="{name}: {pct}% ({sp["words"]} words)"></div>\n'

    # Legend Chips for 2-Column KPI Card
    speaker_chips = ""
    for sp in spoken_speakers:
        pct = sp["pct"]
        color = sp["color"]
        name = sp["name"]
        short_name = name.split()[0] if not sp["is_npc"] else name
        npc_badge = '<span class="text-[8px] px-1 py-0.2 rounded bg-rose-950/80 text-rose-300 border border-rose-800/80 font-mono ml-0.5">NPC</span>' if sp["is_npc"] else ""
        speaker_chips += f"""
            <div class="flex items-center gap-1.5 text-[11px] text-slate-300 py-0.5 px-1.5 rounded bg-slate-900/70 border border-slate-800/80">
                <span class="w-2 h-2 rounded-full flex-shrink-0" style="background-color: {color}"></span>
                <span class="font-medium truncate">{short_name}</span>
                {npc_badge}
                <span class="font-mono font-bold ml-auto text-[10px]" style="color: {color}">{pct}%</span>
            </div>
        """

    # Group Blocks by Chapter/Scene
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

    # Quick Jump Chapter Pills
    chapter_pills_html = ""
    for idx, ch in enumerate(chapters, 1):
        ch_title = ch["title"]
        clean_ch_title = re.sub(r"^CHAPTER\s*\d+\s*:\s*", "", ch_title, flags=re.IGNORECASE)
        anchor_id = f"chapter-{idx}"
        chapter_pills_html += f"""
        <a href="#{anchor_id}" class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-900/90 hover:bg-slate-800 border border-slate-800 hover:border-amber-500 text-slate-300 hover:text-amber-300 transition-all flex items-center gap-1.5 flex-shrink-0">
            <span class="text-amber-500 font-mono text-[10px]">#{idx}</span>
            <span>{clean_ch_title}</span>
        </a>
        """

    # Analytics Elements
    vertical_chapters_html = build_vertical_chapters_html(chapters, characters)
    session_line_chart_svg = build_session_line_chart_svg(chapters)
    campaign_whole_html = build_campaign_whole_html(session_num)
    camp_tab_label = "Campaign (S1)" if session_num == 1 else f"Campaign (S1–S{session_num})"
    critic_forum_html = build_critic_forum_html(editorial_forum, session_num, word_count, spoken_pct, narrative_pct, sensory)
    end_session_critic_card_html = build_end_session_critic_card_html(editorial_forum, session_num, word_count, spoken_pct, narrative_pct, sensory)
    source_mapping = load_session_source_mapping(session_num)
    source_mapping_json = json.dumps(source_mapping)
    session_characters_json = json.dumps(characters)
    diff_inspector_html = build_diff_inspector_html(session_num)

    # Generate Story Blocks & Chapter Dividers
    blocks_html = ""
    chapter_index = 0

    for ch in chapters:
        chapter_index += 1
        ch_title = ch["title"]
        ch_words = ch["word_count"]
        ch_mins = max(1, round(ch_words / 250))
        anchor_id = f"chapter-{chapter_index}"

        blocks_html += f"""
        <!-- CHAPTER DIVIDER {chapter_index} -->
        <section id="{anchor_id}" class="pt-8 pb-4 my-6 border-b border-slate-800/80 scroll-mt-20">
            <div class="flex items-center gap-3">
                <div class="h-px bg-gradient-to-r from-transparent via-amber-500/40 to-transparent flex-1"></div>
                <div class="text-center px-3">
                    <span class="text-[11px] font-bold font-mono tracking-widest text-amber-500 uppercase">Part {chapter_index}</span>
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
                <div class="story-block story-block-narrator py-1.5 px-3 rounded-lg hover:bg-slate-900/40 transition-colors my-1"
                     id="{b_id}"
                     data-block-id="{b_id}"
                     data-speaker="{sp_id}"
                     data-speaker-name="{sp_name}"
                     data-speaker-color="{sp_color}">
                    <div class="flex justify-end">
                        <span class="critique-indicator-dot hidden text-xs text-amber-400 font-bold">● Critique Added</span>
                    </div>
                    <p class="text-slate-300 leading-relaxed text-base sm:text-lg">{text}</p>
                </div>
                """
            else:
                blocks_html += f"""
                <!-- Block {b_idx} ({sp_name}) -->
                <div class="story-block story-block-dialogue p-4 rounded-r-xl my-3.5 shadow-sm"
                     id="{b_id}"
                     style="border-left: 3.5px solid {sp_color}; background: linear-gradient(90deg, {sp_color}14 0%, {sp_color}02 100%);"
                     data-block-id="{b_id}"
                     data-speaker="{sp_id}"
                     data-speaker-name="{sp_name}"
                     data-speaker-color="{sp_color}">
                    <div class="flex items-center gap-2 mb-2">
                        <span class="w-2.5 h-2.5 rounded-full flex-shrink-0" style="background-color: {sp_color}"></span>
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
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover, interactive-widget=resizes-content">
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
        :root {{
            --story-font-scale: 1;
            --story-font-family: 'Outfit', sans-serif;
        }}

        body {{
            background-color: #080c14;
            color: #f1f5f9;
            font-family: var(--story-font-family);
            -webkit-tap-highlight-color: transparent;
            transition: background-color 0.2s ease, color 0.2s ease;
        }}

        .story-block {{
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
            position: relative;
        }}

        /* Responsive & Customizable Story Prose Scaling */
        .story-block p {{
            font-size: calc(1.0625rem * var(--story-font-scale, 1));
            line-height: calc(1.75 * var(--story-font-scale, 1));
            transition: font-size 0.15s ease, line-height 0.15s ease;
        }}
        @media (min-width: 640px) {{
            .story-block p {{
                font-size: calc(1.125rem * var(--story-font-scale, 1));
            }}
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

        /* ========================================================= */
        /* COMPREHENSIVE THEME SYSTEM (Light, Sepia, Dark) */
        /* ========================================================= */
        html.theme-light body {{
            background-color: #f8fafc;
            color: #0f172a;
        }}
        html.theme-light header {{
            background-color: rgba(255, 255, 255, 0.95) !important;
            border-color: #e2e8f0 !important;
        }}
        html.theme-light header h1 {{
            color: #d97706 !important;
        }}
        html.theme-light header p,
        html.theme-light header a {{
            color: #64748b !important;
        }}
        html.theme-light header a:hover {{
            color: #d97706 !important;
            background-color: #f1f5f9 !important;
        }}
        html.theme-light .story-block-narrator,
        html.theme-light .story-block-narrator p {{
            color: #0f172a !important;
        }}
        html.theme-light .story-block-narrator:hover {{
            background-color: rgba(226, 232, 240, 0.6) !important;
        }}
        html.theme-light .story-block-dialogue {{
            background: #ffffff !important;
            box-shadow: 0 1px 4px rgba(0,0,0,0.06) !important;
            border-color: #e2e8f0;
        }}
        html.theme-light .story-block-dialogue p {{
            color: #020617 !important;
        }}
        html.theme-light #chaptersModalCard,
        html.theme-light #critiqueBottomSheet,
        html.theme-light #criticForumModalCard,
        html.theme-light #onboardingModalCard,
        html.theme-light #settingsModalCard,
        html.theme-light #ghModalCard {{
            background-color: #ffffff !important;
            border-color: #cbd5e1 !important;
            color: #0f172a !important;
        }}
        html.theme-light #chaptersModalCard h2,
        html.theme-light #chaptersModalCard h3,
        html.theme-light #chaptersModalCard p,
        html.theme-light #criticForumModalCard h3,
        html.theme-light #criticForumModalCard p,
        html.theme-light #onboardingModalCard h3,
        html.theme-light #onboardingModalCard p,
        html.theme-light #settingsModalCard h3,
        html.theme-light #settingsModalCard p {{
            color: #0f172a;
        }}
        html.theme-light .text-slate-400,
        html.theme-light .text-slate-300,
        html.theme-light .text-slate-200 {{
            color: #475569 !important;
        }}
        html.theme-light .text-slate-500 {{
            color: #64748b !important;
        }}
        html.theme-light .text-slate-100 {{
            color: #0f172a !important;
        }}
        html.theme-light [class*="bg-slate-950"],
        html.theme-light [class*="bg-slate-900"] {{
            background-color: #f1f5f9 !important;
            border-color: #e2e8f0 !important;
        }}
        html.theme-light .border-slate-800,
        html.theme-light .border-slate-700 {{
            border-color: #e2e8f0 !important;
        }}
        html.theme-light textarea,
        html.theme-light input[type="text"],
        html.theme-light select {{
            background-color: #ffffff !important;
            border-color: #cbd5e1 !important;
            color: #0f172a !important;
        }}
        html.theme-light textarea::placeholder,
        html.theme-light input::placeholder {{
            color: #94a3b8 !important;
        }}
        html.theme-light .category-pill:not(.active) {{
            background-color: #f1f5f9 !important;
            border-color: #cbd5e1 !important;
            color: #334155 !important;
        }}
        html.theme-light a[href^="#chapter-"] {{
            background-color: #ffffff !important;
            border-color: #cbd5e1 !important;
            color: #334155 !important;
        }}
        html.theme-light a[href^="#chapter-"]:hover {{
            background-color: #f1f5f9 !important;
            border-color: #d97706 !important;
            color: #d97706 !important;
        }}
        html.theme-light #footerCriticForumBtn {{
            background: #ffe4e6 !important;
            border-color: #f43f5e !important;
            color: #9f1239 !important;
        }}
        html.theme-light #footerCriticForumBtn:hover {{
            background: #fecdd3 !important;
        }}
        html.theme-light .custom-scrollbar::-webkit-scrollbar-track {{
            background: #f1f5f9 !important;
        }}
        html.theme-light .custom-scrollbar::-webkit-scrollbar-thumb {{
            background: #cbd5e1 !important;
        }}
        html.theme-light #diffInspectorOverlay {{
            background-color: rgba(248, 250, 252, 0.98) !important;
            color: #0f172a !important;
        }}
        html.theme-light #diffInspectorOverlay header,
        html.theme-light #diffInspectorOverlay footer {{
            background-color: #ffffff !important;
            border-color: #cbd5e1 !important;
            color: #0f172a !important;
        }}
        html.theme-light #diffNarrativePane,
        html.theme-light #diffSourcePane {{
            background-color: #f8fafc !important;
        }}
        html.theme-light .diff-card {{
            background-color: #ffffff !important;
            border-color: #cbd5e1 !important;
            color: #0f172a !important;
        }}
        html.theme-light .diff-card p {{
            color: #0f172a !important;
        }}
        html.theme-light .diff-narrative-card.active-diff-card,
        html.theme-light .diff-source-card.active-diff-card {{
            background-color: rgba(254, 243, 199, 0.75) !important;
            border-color: #d97706 !important;
        }}
        html.theme-light .diff-source-line {{
            background-color: #f1f5f9 !important;
            border-color: #e2e8f0 !important;
            color: #1e293b !important;
        }}
        html.theme-light .diff-source-line.active-diff-line {{
            background-color: rgba(254, 243, 199, 0.95) !important;
            border-color: #d97706 !important;
        }}
        html.theme-light .diff-bundled-toggle {{
            background-color: #f1f5f9 !important;
            border-color: #cbd5e1 !important;
            color: #92400e !important;
        }}

        html.theme-sepia body {{
            background-color: #f6f0e2;
            color: #2c221e;
        }}
        html.theme-sepia header {{
            background-color: rgba(246, 240, 226, 0.95) !important;
            border-color: #e3d7bf !important;
        }}
        html.theme-sepia header h1 {{
            color: #b45309 !important;
        }}
        html.theme-sepia header p,
        html.theme-sepia header a {{
            color: #786450 !important;
        }}
        html.theme-sepia header a:hover {{
            color: #b45309 !important;
            background-color: #ede3cb !important;
        }}
        html.theme-sepia .story-block-narrator,
        html.theme-sepia .story-block-narrator p {{
            color: #241a15 !important;
        }}
        html.theme-sepia .story-block-narrator:hover {{
            background-color: rgba(216, 199, 166, 0.45) !important;
        }}
        html.theme-sepia .story-block-dialogue {{
            background: #fffdf8 !important;
            box-shadow: 0 1px 4px rgba(60,40,20,0.06) !important;
        }}
        html.theme-sepia .story-block-dialogue p {{
            color: #1a120c !important;
        }}
        html.theme-sepia #chaptersModalCard,
        html.theme-sepia #critiqueBottomSheet,
        html.theme-sepia #criticForumModalCard,
        html.theme-sepia #onboardingModalCard,
        html.theme-sepia #settingsModalCard,
        html.theme-sepia #ghModalCard {{
            background-color: #fdfbf7 !important;
            border-color: #ded1b8 !important;
            color: #2c221e !important;
        }}
        html.theme-sepia .text-slate-400,
        html.theme-sepia .text-slate-300,
        html.theme-sepia .text-slate-200 {{
            color: #5c4b3c !important;
        }}
        html.theme-sepia .text-slate-500 {{
            color: #7d6855 !important;
        }}
        html.theme-sepia .text-slate-100 {{
            color: #2c221e !important;
        }}
        html.theme-sepia [class*="bg-slate-950"],
        html.theme-sepia [class*="bg-slate-900"] {{
            background-color: #ede3cb !important;
            border-color: #ded1b8 !important;
        }}
        html.theme-sepia .border-slate-800,
        html.theme-sepia .border-slate-700 {{
            border-color: #ded1b8 !important;
        }}
        html.theme-sepia textarea,
        html.theme-sepia input[type="text"],
        html.theme-sepia select {{
            background-color: #fffdf8 !important;
            border-color: #d8c7a6 !important;
            color: #2c221e !important;
        }}
        html.theme-sepia textarea::placeholder,
        html.theme-sepia input::placeholder {{
            color: #a08c76 !important;
        }}
        html.theme-sepia .category-pill:not(.active) {{
            background-color: #ede3cb !important;
            border-color: #d8c7a6 !important;
            color: #4a3d35 !important;
        }}
        html.theme-sepia a[href^="#chapter-"] {{
            background-color: #fffdf8 !important;
            border-color: #d8c7a6 !important;
            color: #4a3d35 !important;
        }}
        html.theme-sepia a[href^="#chapter-"]:hover {{
            background-color: #ede3cb !important;
            border-color: #b45309 !important;
            color: #b45309 !important;
        }}
        html.theme-sepia #footerCriticForumBtn {{
            background: #fce7f3 !important;
            border-color: #e11d48 !important;
            color: #881337 !important;
        }}
        html.theme-sepia #footerCriticForumBtn:hover {{
            background: #fbcfe8 !important;
        }}
        html.theme-sepia .custom-scrollbar::-webkit-scrollbar-track {{
            background: #ede3cb !important;
        }}
        html.theme-sepia .custom-scrollbar::-webkit-scrollbar-thumb {{
            background: #d8c7a6 !important;
        }}
        html.theme-sepia #diffInspectorOverlay {{
            background-color: rgba(245, 239, 226, 0.98) !important;
            color: #2c221e !important;
        }}
        html.theme-sepia #diffInspectorOverlay header,
        html.theme-sepia #diffInspectorOverlay footer {{
            background-color: #fdfbf7 !important;
            border-color: #ded1b8 !important;
            color: #2c221e !important;
        }}
        html.theme-sepia #diffNarrativePane,
        html.theme-sepia #diffSourcePane {{
            background-color: #f5efe2 !important;
        }}
        html.theme-sepia .diff-card {{
            background-color: #fffdf8 !important;
            border-color: #ded1b8 !important;
            color: #2c221e !important;
        }}
        html.theme-sepia .diff-card p {{
            color: #2c221e !important;
        }}
        html.theme-sepia .diff-narrative-card.active-diff-card,
        html.theme-sepia .diff-source-card.active-diff-card {{
            background-color: rgba(217, 119, 6, 0.14) !important;
            border-color: #b45309 !important;
        }}
        html.theme-sepia .diff-source-line {{
            background-color: #ede3cb !important;
            border-color: #ded1b8 !important;
            color: #2c221e !important;
        }}
        html.theme-sepia .diff-source-line.active-diff-line {{
            background-color: rgba(217, 119, 6, 0.22) !important;
            border-color: #b45309 !important;
        }}
        html.theme-sepia .diff-bundled-toggle {{
            background-color: #ede3cb !important;
            border-color: #ded1b8 !important;
            color: #78350f !important;
        }}

        /* Overlay Transitions & Viewport Sizing */
        #chaptersModalOverlay, #critiqueModalOverlay, #ghModalOverlay, #onboardingModalOverlay, #criticForumModalOverlay, #settingsModalOverlay, #diffInspectorOverlay {{
            transition: opacity 0.25s ease, backdrop-filter 0.25s ease;
            height: 100vh;
            height: 100dvh;
            box-sizing: border-box !important;
            padding: 1rem !important;
            max-width: 100vw !important;
            overflow-x: hidden !important;
        }}
        #chaptersModalOverlay.visible, #critiqueModalOverlay.visible, #criticForumModalOverlay.visible, #settingsModalOverlay.visible, #diffInspectorOverlay.visible {{
            opacity: 1;
            pointer-events: auto;
        }}

        #chaptersModalCard, #critiqueBottomSheet, #criticForumModalCard, #settingsModalCard, #onboardingModalCard {{
            transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.2s ease, max-height 0.2s ease;
            transform: scale(0.96) translateY(-10px);
            opacity: 0;
            max-height: min(88vh, 88dvh);
            box-sizing: border-box !important;
            margin-left: auto !important;
            margin-right: auto !important;
        }}
        #chaptersModalOverlay.visible #chaptersModalCard,
        #critiqueModalOverlay.visible #critiqueBottomSheet,
        #criticForumModalOverlay.visible #criticForumModalCard,
        #settingsModalOverlay.visible #settingsModalCard,
        #onboardingModalOverlay.visible #onboardingModalCard {{
            transform: scale(1) translateY(0);
            opacity: 1;
        }}

        @media (max-width: 640px) {{
            #chaptersModalOverlay, #critiqueModalOverlay, #ghModalOverlay, #onboardingModalOverlay, #criticForumModalOverlay, #settingsModalOverlay {{
                padding: 0.75rem !important;
                box-sizing: border-box !important;
            }}
            #critiqueModalOverlay {{
                align-items: flex-start !important;
                padding: 0.75rem !important;
            }}
            #chaptersModalCard, #critiqueBottomSheet, #criticForumModalCard, #settingsModalCard, #onboardingModalCard {{
                width: 100% !important;
                max-width: 100% !important;
                box-sizing: border-box !important;
                margin-left: auto !important;
                margin-right: auto !important;
            }}
            #critiqueBottomSheet {{
                max-height: calc(100dvh - 1.5rem) !important;
                margin-top: 0 !important;
                margin-bottom: auto !important;
            }}
        }}

        .custom-scrollbar::-webkit-scrollbar {{
            height: 5px;
            width: 5px;
        }}
        .custom-scrollbar::-webkit-scrollbar-track {{
            background: rgba(15, 23, 42, 0.6);
            border-radius: 999px;
        }}
        .custom-scrollbar::-webkit-scrollbar-thumb {{
            background: rgba(100, 116, 139, 0.5);
            border-radius: 999px;
        }}

        /* ========================================================= */
        /* SYNCHRONIZED NARRATIVE VS. SOURCE DIFF INSPECTOR STYLES   */
        /* ========================================================= */
        #diffInspectorOverlay {{
            padding: 0 !important;
            margin: 0 !important;
            border-radius: 0 !important;
        }}
        #diffInspectorOverlay.visible {{
            opacity: 1;
            pointer-events: auto;
        }}

        /* Layout Hotdog (Side-by-Side Left/Right 50/50) */
        #diffPanesContainer.layout-hotdog {{
            display: flex;
            flex-direction: row;
            height: 100%;
            overflow: hidden;
        }}
        #diffPanesContainer.layout-hotdog #diffNarrativePane {{
            width: 50%;
            height: 100%;
            border-right: 1px solid rgba(51, 65, 85, 0.7);
        }}
        #diffPanesContainer.layout-hotdog #diffSourcePane {{
            width: 50%;
            height: 100%;
        }}

        /* Layout Hamburger (Stacked Top/Bottom 50/50 - Mobile Ergonomics) */
        #diffPanesContainer.layout-hamburger {{
            display: flex;
            flex-direction: column;
            height: 100%;
            overflow: hidden;
        }}
        #diffPanesContainer.layout-hamburger #diffNarrativePane {{
            width: 100%;
            height: 50%;
            border-bottom: 1px solid rgba(51, 65, 85, 0.7);
        }}
        #diffPanesContainer.layout-hamburger #diffSourcePane {{
            width: 100%;
            height: 50%;
        }}

        .diff-card {{
            transition: border-color 0.15s ease, background-color 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease;
        }}
        .diff-narrative-card.active-diff-card,
        .diff-source-card.active-diff-card {{
            border-color: #f59e0b !important;
            background-color: rgba(245, 158, 11, 0.12) !important;
            box-shadow: 0 0 0 1px rgba(245, 158, 11, 0.4), 0 4px 14px rgba(0, 0, 0, 0.3) !important;
        }}
        .diff-source-line {{
            transition: border-color 0.15s ease, background-color 0.15s ease, box-shadow 0.15s ease;
        }}
        .diff-source-line.active-diff-line {{
            border-color: #f59e0b !important;
            background-color: rgba(245, 158, 11, 0.22) !important;
            box-shadow: 0 0 0 1.5px rgba(245, 158, 11, 0.6) !important;
        }}
    </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen pb-24 mode-critique">

    <!-- STICKY TOP APP BAR (Clean & Content-Focused with Minimal Reading Progress) -->
    <header class="sticky top-0 z-40 bg-slate-900/95 backdrop-blur-md border-b border-slate-800">
        <div class="max-w-4xl mx-auto flex items-center justify-between gap-2.5 px-3 sm:px-4 py-2.5">
            <div class="flex items-center gap-2 min-w-0">
                <a href="index.html?c={campaign_id}" class="text-slate-400 hover:text-amber-400 transition-colors flex items-center justify-center w-8 h-8 -ml-1 rounded-lg hover:bg-slate-800/60 active:scale-95 flex-shrink-0" title="Back to {campaign_name} Sessions" aria-label="Back to Sessions">
                    <span class="text-lg leading-none font-bold">←</span>
                </a>
                <span class="text-slate-700 select-none hidden xs:inline">|</span>
                <div class="truncate">
                    <h1 class="font-bold text-sm sm:text-base text-amber-400 font-serif tracking-wide truncate">{campaign_name}</h1>
                    <p class="text-xs text-slate-400 truncate">Session {session_num}: {session_title}</p>
                </div>
            </div>

            <!-- Header Controls: Chapters Button, Mode Toggle & Settings Cog -->
            <div class="flex items-center gap-1.5 sm:gap-2 flex-shrink-0">
                <button id="toggleChaptersBtn" type="button" class="px-2.5 sm:px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 border border-slate-700 text-amber-300 flex items-center gap-1.5 transition-all shadow-sm active:scale-95" title="View Table of Contents & Chapter Breakdown" aria-label="Open Chapters Table of Contents">
                    <svg class="w-3.5 h-3.5 flex-shrink-0 text-amber-400" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24" aria-hidden="true">
                        <line x1="9" y1="6" x2="20" y2="6"></line>
                        <line x1="9" y1="12" x2="20" y2="12"></line>
                        <line x1="9" y1="18" x2="20" y2="18"></line>
                        <circle cx="4" cy="6" r="1.5" fill="currentColor"></circle>
                        <circle cx="4" cy="12" r="1.5" fill="currentColor"></circle>
                        <circle cx="4" cy="18" r="1.5" fill="currentColor"></circle>
                    </svg>
                    <span>Chapters</span>
                </button>

                <!-- Combined Single Mode Toggle: Switches dynamically between Read Mode and Critique Mode -->
                <button id="modeToggleBtn" type="button" class="px-2.5 sm:px-3 py-1.5 rounded-lg text-xs font-bold bg-gradient-to-r from-amber-400 to-amber-500 hover:from-amber-300 text-slate-950 border border-amber-300 shadow-md ring-2 ring-amber-400/30 transition-all flex items-center gap-1.5 active:scale-95" title="Critique Mode Active — tap to toggle to Read Mode">
                    <span id="modeToggleIcon">✍️</span>
                    <span id="modeToggleLabel" class="hidden sm:inline">Critique</span>
                </button>

                <!-- Reading Settings Cog -->
                <button id="toggleSettingsBtn" type="button" class="px-2 sm:px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 hover:text-white flex items-center gap-1 transition-all shadow-sm active:scale-95" title="Reading Preferences (Font Size, Theme, Font Family)">
                    <span class="text-sm">⚙️</span>
                </button>
            </div>
        </div>
        <!-- Minimal Top Reading Progress Bar with Dynamic Chapter Breadcrumbs & Finished Pip -->
        <div class="w-full bg-slate-950/90 h-[3px] relative overflow-hidden">
            <!-- Active Scroll Progress Bar -->
            <div id="readingProgressBar" class="h-full transition-[width] duration-100 ease-out" style="width: 0%; background: linear-gradient(90deg, #2563eb 0%, #38bdf8 50%, #67e8f9 100%);"></div>
            
            <!-- Chapter Breadcrumb Trail Container (Generated dynamically per chapter) -->
            <div id="readingProgressBreadcrumbs" class="absolute inset-0 pointer-events-none"></div>

            <!-- Completion Pip on Far Right (Matches 100% Cyan-Green tip) -->
            <div id="readingProgressFinishedPip" class="absolute right-0 top-0 bottom-0 w-2.5 shadow-[0_0_8px_rgba(6,182,212,1)] hidden" style="background-color: #06b6d4;" title="Session Completed"></div>
        </div>
    </header>

    <!-- WRAPPER -->
    <div class="max-w-3xl mx-auto px-4 sm:px-6 pt-6">

        <!-- EBOOK COVER & INTRO HEADER -->
        <div class="mb-5 text-center">
            <div class="w-36 sm:w-44 mx-auto mb-3 rounded-xl overflow-hidden shadow-2xl border border-slate-800 ring-1 ring-amber-500/20">
                <img src="images/uneraseable-cover.jpg" alt="Uneraseable Cover by Doug N Masters" class="w-full h-auto object-cover">
            </div>
            <span class="text-xs uppercase tracking-widest text-amber-500 font-bold font-mono">Session {session_num} · Interactive Edition</span>
            <h2 class="text-2xl sm:text-3xl font-extrabold text-slate-100 font-serif mt-1 tracking-wide">{session_title}</h2>
            <p class="text-xs sm:text-sm text-slate-400 mt-1.5 font-serif italic max-w-xl mx-auto">{session_synopsis}</p>
        </div>

        <!-- FAST SCENE JUMP PILLS -->
        <div class="mb-6 flex items-center gap-1.5 overflow-x-auto pb-1 custom-scrollbar">
            <span class="text-[10px] font-bold uppercase text-slate-500 flex-shrink-0 mr-1">Jump to Scene:</span>
            {chapter_pills_html}
        </div>

        <!-- ========================================================= -->
        <!-- 11LABS-STYLE STORY BLOCKS CONTAINER -->
        <!-- ========================================================= -->
        <main id="storyContentContainer" class="space-y-1">
            {blocks_html}
        </main>

        <!-- Story End Sentinel for Reading Completion Tracking -->
        <div id="storyEndSentinel" class="h-8 w-full flex items-center justify-center text-xs text-slate-500 font-mono py-6">
            <span>✦ End of Session {session_num} ✦</span>
        </div>

        <!-- Bottom Controls: Reader Feedback & Editorial Review -->
        <footer class="mt-12 pt-8 border-t border-slate-800 text-center space-y-4">
            <div class="bg-slate-900/60 p-5 rounded-2xl border border-slate-800 max-w-lg mx-auto shadow-lg space-y-3.5">
                <div class="space-y-1">
                    <div class="flex items-center justify-center gap-2 text-amber-400">
                        <span class="text-base">📝</span>
                        <h3 class="text-sm font-bold tracking-wide">Reader Feedback & Notes</h3>
                    </div>
                    <p class="text-xs text-slate-400">Review your inline critique notes or explore the bot's editorial review of the session.</p>
                </div>

                <div class="flex flex-wrap gap-2.5 justify-center items-center pt-1">
                    <button id="footerExportBtn" type="button" class="px-4 sm:px-5 py-2.5 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 text-slate-950 font-bold rounded-xl text-xs transition-all shadow-md flex items-center gap-1.5 active:scale-95">
                        <span>📝</span> <span>Review Feedback</span>
                        <span id="exportBadgeCount" class="bg-slate-950 text-amber-300 text-[10px] px-1.5 py-0.2 rounded-full font-bold ml-1">0</span>
                    </button>
                    <button id="footerCriticForumBtn" type="button" class="px-4 sm:px-5 py-2.5 bg-slate-800 hover:bg-slate-700 border border-rose-800/80 hover:border-rose-600 text-rose-300 hover:text-rose-200 font-bold rounded-xl text-xs transition-all shadow-md flex items-center gap-1.5 active:scale-95" title="View the editorial story critique and narrative spectrum for this session">
                        <span>🍅</span> <span>Read the Critique</span>
                    </button>
                    <button id="clearCritiquesBtn" type="button" class="px-3 py-2 bg-slate-800/60 hover:bg-slate-700 text-slate-400 hover:text-slate-200 text-xs font-semibold rounded-xl transition-colors active:scale-95">
                        Clear Notes
                    </button>
                </div>
            </div>
            <p class="text-[11px] text-slate-600 font-mono">UNERASEABLE © D&D Scribe Engine · Schema 2.0 Indexed.</p>
        </footer>

    </div>

    <!-- ========================================================= -->
    <!-- CHAPTERS & STATS MODAL OVERLAY (Header-Triggered Modal) -->
    <!-- ========================================================= -->
    <div id="chaptersModalOverlay" class="fixed inset-0 bg-slate-950/85 backdrop-blur-md z-50 flex items-start sm:items-center justify-center opacity-0 pointer-events-none p-3 sm:p-4 overflow-y-auto pt-6 sm:pt-4">
        <div id="chaptersModalCard" class="w-full max-w-2xl bg-slate-900 border border-slate-700 rounded-2xl p-4 sm:p-5 shadow-2xl flex flex-col my-auto max-h-[88vh] sm:max-h-[85vh]">
            
            <!-- Modal Header with Title & Exit Button -->
            <div class="flex items-center justify-between border-b border-slate-800 pb-3 mb-3 gap-2 flex-shrink-0">
                <div class="flex items-center gap-2 min-w-0">
                    <span class="text-xl">📑</span>
                    <div class="truncate">
                        <h3 class="text-sm sm:text-base font-bold text-amber-400 uppercase tracking-wider font-serif truncate">Chapters & Story Breakdown</h3>
                        <p class="text-[11px] text-slate-400 font-mono truncate">Session {session_num} · {len(chapters)} Chapters · {word_count:,}w (~{read_mins}m)</p>
                    </div>
                </div>
                <button id="closeChaptersModalBtn" type="button" class="text-slate-400 hover:text-slate-100 text-2xl font-bold p-1 leading-none transition-colors ml-2" title="Close (Esc)">&times;</button>
            </div>

            <!-- Scrollable Content Body -->
            <div class="overflow-y-auto space-y-3.5 pr-1 flex-1 min-h-0 custom-scrollbar">
                
                <!-- 1. STATS ACCORDION (Clean Elevated Dark Panel) -->
                <div class="bg-slate-950/80 border border-slate-800 rounded-xl overflow-hidden shadow-md">
                    <button id="toggleStatsAccordionBtn" type="button" class="w-full p-3 flex items-center justify-between text-left bg-slate-950/90 hover:bg-slate-900 transition-colors select-none">
                        <div class="flex items-center gap-2.5">
                            <span class="px-2 py-0.5 rounded bg-indigo-500/15 text-indigo-300 border border-indigo-500/40 text-[10px] font-mono font-bold">Stats</span>
                            <div>
                                <h4 class="text-xs sm:text-sm font-semibold text-slate-100">Session Stats & Voice Velocity</h4>
                                <p class="text-[10px] text-slate-400 font-mono">Sensory registers, voice velocity curve & campaign stats</p>
                            </div>
                        </div>
                        <span id="statsAccordionChevron" class="text-[11px] font-mono font-bold text-amber-400 px-2.5 py-1 rounded bg-slate-900 border border-slate-700 flex items-center gap-1">
                            <span>▼</span> <span>Expand</span>
                        </span>
                    </button>

                    <!-- Collapsed Body Content -->
                    <div id="statsAccordionBody" class="hidden p-3 sm:p-3.5 pt-2 border-t border-slate-800/80 bg-slate-950/60 space-y-3">
                        
                        <!-- Mode Switcher for Analytics Tabs -->
                        <div class="flex flex-wrap items-center justify-between gap-2 pt-1">
                            <span class="text-[11px] font-bold text-slate-400 uppercase tracking-wider font-mono">Analytics Views</span>
                            <div class="flex bg-slate-900 border border-slate-800 rounded-lg p-0.5 shadow-inner">
                                <button id="chartTabStatsBtn" type="button" class="px-2.5 py-1 rounded-md text-[11px] font-bold text-slate-950 bg-amber-400 shadow transition-all flex items-center gap-1" onclick="switchChartTab('session')">
                                    <span>📊</span> <span>Session Engagement & KPIs</span>
                                </button>
                                <button id="chartTabCampaignBtn" type="button" class="px-2.5 py-1 rounded-md text-[11px] font-medium text-slate-400 hover:text-slate-200 transition-all flex items-center gap-1" onclick="switchChartTab('campaign')">
                                    <span>🌐</span> <span>{camp_tab_label}</span>
                                </button>
                            </div>
                        </div>

                        <!-- View 1: Default Session KPIs (Leads with Telemetry & Comparative Journey, followed by 2-Column KPIs & Velocity) -->
                        <div id="chartViewSession" class="w-full space-y-3">
                            
                            <!-- 1. READERSHIP & ENGAGEMENT TELEMETRY (Leads the Session Stats) -->
                            <div class="bg-slate-900/80 p-3.5 sm:p-4 rounded-xl border border-slate-800/90 shadow-sm space-y-3">
                                <div class="flex items-center justify-between text-xs font-semibold text-slate-300 border-b border-slate-800/80 pb-2">
                                    <span class="flex items-center gap-2 text-indigo-300">
                                        <span class="p-1 rounded-md bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 text-xs">👥</span>
                                        <span class="uppercase tracking-wider font-mono text-[11px] font-bold text-slate-200">Reader Engagement & Progress Journey</span>
                                    </span>
                                </div>

                                <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center">
                                    <!-- 1. Unique Readers -->
                                    <div class="bg-slate-950/70 p-2 sm:p-2.5 rounded-lg border border-slate-800/80">
                                        <div class="text-[10px] text-slate-400 font-medium truncate">Unique Readers</div>
                                        <div class="text-base sm:text-xl font-bold font-mono text-indigo-300 mt-0.5" id="telemetryUniqueReaders">--</div>
                                        <div class="text-[9px] text-slate-500 font-mono">distinct devices</div>
                                    </div>

                                    <!-- 2. Total Opens -->
                                    <div class="bg-slate-950/70 p-2 sm:p-2.5 rounded-lg border border-slate-800/80">
                                        <div class="text-[10px] text-slate-400 font-medium truncate">Total Opens</div>
                                        <div class="text-base sm:text-xl font-bold font-mono text-amber-400 mt-0.5" id="telemetryTotalOpens">--</div>
                                        <div class="text-[9px] text-slate-500 font-mono">sessions</div>
                                    </div>

                                    <!-- 3. Finisher Circle (2-Column Component: #/# | X%) -->
                                    <div class="bg-slate-950/70 p-2 sm:p-2.5 rounded-lg border border-slate-800/80 flex flex-col justify-between">
                                        <div class="text-[10px] text-slate-400 font-medium truncate">Finisher Circle</div>
                                        <div class="flex items-baseline justify-center gap-1.5 mt-0.5 font-mono">
                                            <span class="text-xs font-bold text-slate-300" id="telemetryFinisherRatio">0/0</span>
                                            <span class="text-slate-600 text-xs font-normal">|</span>
                                            <span class="text-base sm:text-lg font-bold text-emerald-400" id="telemetryCompletionRate">0%</span>
                                        </div>
                                        <div class="text-[9px] text-slate-500 font-mono">100% completed</div>
                                    </div>

                                    <!-- 4. Avg Drop-off Depth (subtext: attention span) -->
                                    <div class="bg-slate-950/70 p-2 sm:p-2.5 rounded-lg border border-slate-800/80">
                                        <div class="text-[10px] text-slate-400 font-medium truncate">Avg Drop-Off</div>
                                        <div class="text-base sm:text-xl font-bold font-mono text-rose-300 mt-0.5" id="telemetryDropoffDepth">--%</div>
                                        <div class="text-[9px] text-slate-500 font-mono">attention span</div>
                                    </div>
                                </div>

                                <!-- Comparative Reading Journey & Benchmark Visualizer -->
                                <div class="bg-slate-950/80 p-3 rounded-xl border border-slate-800/80 space-y-2.5">
                                    <div class="flex items-center justify-between text-[11px] text-slate-300 font-medium">
                                        <span class="flex items-center gap-1.5 font-mono text-[10px] uppercase text-slate-400 tracking-wider">
                                            <span>📍</span> <span>Your Position vs. Reader Base</span>
                                        </span>
                                        <span class="text-[10px] font-mono text-slate-500">Milestone Track</span>
                                    </div>

                                    <!-- Milestone Visual Track -->
                                    <div class="relative pt-5 pb-5 px-1">
                                        <!-- Background track -->
                                        <div class="h-3 w-full rounded-full bg-slate-900 border border-slate-800 overflow-hidden relative shadow-inner">
                                            <!-- User's progress fill -->
                                            <div id="telemetryPersonalProgressFill" class="h-full bg-gradient-to-r from-indigo-500 via-sky-400 to-amber-400 transition-all duration-300 rounded-full" style="width: 0%;"></div>
                                        </div>

                                        <!-- Average Drop-off Vertical Guideline & Marker -->
                                        <div id="telemetryDropoffMarker" class="absolute top-0 transition-all duration-300 flex flex-col items-center -translate-x-1/2 pointer-events-none" style="left: 45%;">
                                            <span class="text-[9px] font-mono font-bold text-rose-400 bg-rose-950/90 px-1.5 py-0.2 rounded border border-rose-800 shadow whitespace-nowrap" id="telemetryDropoffMarkerText">Avg Exit ~45%</span>
                                            <div class="w-0.5 h-6 bg-rose-500/80 mt-0.5 border-dashed"></div>
                                        </div>

                                        <!-- User's Live Pin Marker -->
                                        <div id="telemetryUserPin" class="absolute bottom-0 transition-all duration-300 flex flex-col items-center -translate-x-1/2 pointer-events-none" style="left: 0%;">
                                            <div class="w-2.5 h-2.5 rounded-full bg-amber-400 border-2 border-slate-950 shadow-md"></div>
                                            <span class="text-[9px] font-mono font-bold text-amber-300 bg-slate-900 px-1.5 py-0.2 rounded border border-amber-500/50 shadow whitespace-nowrap mt-0.5" id="telemetryUserPinText">You: 0%</span>
                                        </div>

                                        <!-- Target Goal Finish Flag (at 100%) -->
                                        <div class="absolute right-0 top-1/2 -translate-y-1/2 translate-x-1 flex items-center pointer-events-none">
                                            <span class="text-xs bg-slate-900 border border-emerald-500/40 rounded-full p-0.5 shadow" title="100% Completion Goal">🏁</span>
                                        </div>
                                    </div>

                                    <!-- Motivational Guidance Subtext -->
                                    <div id="telemetryMotivationBanner" class="text-[11px] p-2.5 rounded-lg bg-slate-900/90 border border-slate-800 text-slate-300 leading-normal flex items-center gap-2">
                                        <span>✨</span> <span id="telemetryMotivationText">Scroll to read and advance your progress toward the 100% finisher mark!</span>
                                    </div>
                                </div>
                            </div>

                            <!-- 2. 2-COLUMN KPI GRID (Story Length & Dialogue Ratio) -->
                            <div class="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                                
                                <!-- Column 1: Overall Story Length & Reading Overview -->
                                <div class="bg-slate-900/80 p-3 sm:p-3.5 rounded-xl border border-slate-800/90 flex flex-col justify-between gap-2.5 shadow-sm">
                                    <div>
                                        <div class="flex items-center justify-between text-[11px] text-slate-400 font-medium">
                                            <span class="uppercase font-mono text-[10px] tracking-wider text-slate-400">📖 Story Length & Reading Time</span>
                                            <span class="text-[10px] text-emerald-400 font-mono font-semibold">~{read_mins}m Read</span>
                                        </div>
                                        <div class="text-xl sm:text-2xl font-bold text-slate-100 font-mono mt-1">
                                            {word_count:,} <span class="text-xs text-slate-400 font-sans font-normal">words</span>
                                        </div>
                                        <div class="text-xs text-slate-400 mt-0.5">
                                            ~{book_pages} Book Pages
                                        </div>
                                    </div>

                                    <!-- Sensory Palette Registers -->
                                    <div class="pt-2 border-t border-slate-800">
                                        <div class="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                                            Sensory Palette Registers
                                        </div>
                                        <div class="grid grid-cols-2 gap-1.5">
                                            <span class="px-2 py-1 rounded bg-slate-950/80 text-slate-300 border border-slate-800 text-[10px] flex justify-between">
                                                <span>👁️ Visual</span> <strong class="text-amber-400 font-mono">{sensory.get("visual", 30)}</strong>
                                            </span>
                                            <span class="px-2 py-1 rounded bg-slate-950/80 text-slate-300 border border-slate-800 text-[10px] flex justify-between">
                                                <span>👂 Auditory</span> <strong class="text-sky-400 font-mono">{sensory.get("auditory", 15)}</strong>
                                            </span>
                                            <span class="px-2 py-1 rounded bg-slate-950/80 text-slate-300 border border-slate-800 text-[10px] flex justify-between">
                                                <span>✋ Tactile</span> <strong class="text-emerald-400 font-mono">{sensory.get("tactile", 20)}</strong>
                                            </span>
                                            <span class="px-2 py-1 rounded bg-slate-950/80 text-slate-300 border border-slate-800 text-[10px] flex justify-between">
                                                <span>⚡ Atmosphere</span> <strong class="text-amber-300 font-mono">{sensory.get("atmospheric", 15)}</strong>
                                            </span>
                                        </div>
                                    </div>
                                </div>

                                <!-- Column 2: Dialogue Ratio Connected to Spoken Line Share -->
                                <div class="bg-slate-900/80 p-3 sm:p-3.5 rounded-xl border border-slate-800/90 flex flex-col justify-between gap-2.5 shadow-sm">
                                    <div>
                                        <div class="flex items-center justify-between text-[11px] text-slate-400 font-medium">
                                            <span class="uppercase font-mono text-[10px] tracking-wider text-amber-400">🎙️ Dialogue Ratio & Voice Share</span>
                                            <span class="text-[10px] text-slate-400 font-mono">{total_spoken_words:,}w spoken</span>
                                        </div>
                                        <div class="text-xl sm:text-2xl font-bold text-amber-400 font-mono mt-1">
                                            {spoken_pct}% <span class="text-xs text-slate-400 font-sans font-normal">spoken dialogue ({narrative_pct}% prose)</span>
                                        </div>
                                        
                                        <!-- Connected Spoken Line Share Multi-Segment Progress Bar -->
                                        <div class="mt-2 space-y-1">
                                            <div class="h-2.5 w-full rounded-full bg-slate-950 flex overflow-hidden border border-slate-800 shadow-inner">
                                                {prog_bar_segments}
                                            </div>
                                        </div>
                                    </div>

                                    <!-- Connected Speaker Share Breakdown Grid -->
                                    <div class="pt-2 border-t border-slate-800">
                                        <div class="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                                            Spoken Line Breakdown ({len(spoken_speakers)} active voices)
                                        </div>
                                        <div class="grid grid-cols-2 gap-1.5 max-h-32 overflow-y-auto custom-scrollbar pr-0.5">
                                            {speaker_chips}
                                        </div>
                                    </div>
                                </div>

                            </div>

                            <!-- 3. Voice Velocity Line Chart in that subsection -->
                            <div class="w-full">
                                {session_line_chart_svg}
                            </div>

                        </div>

                        <!-- View 2: Campaign Whole Comparison -->
                        <div id="chartViewCampaign" class="w-full hidden">
                            {campaign_whole_html}
                        </div>

                    </div>
                </div>

                <!-- 2. GLOBAL CHARACTER COLOR KEY -->
                <div class="flex flex-wrap items-center justify-between gap-2 p-2.5 bg-slate-950/80 rounded-xl border border-slate-800 text-[10px] text-slate-300">
                    <span class="font-semibold text-slate-400 uppercase tracking-wider font-mono">Voices Key:</span>
                    <div class="flex flex-wrap items-center gap-2 sm:gap-3">
                        <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-[#3b82f6]"></span><span>Pierre</span></span>
                        <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-[#8b5cf6]"></span><span>Prof. Dravin</span></span>
                        <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-[#f59e0b]"></span><span>Eusacles</span></span>
                        <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-[#10b981]"></span><span>Alfie</span></span>
                        <span class="flex items-center gap-1"><span class="text-rose-400 font-mono text-[9px] leading-none">▲</span><span class="text-rose-300 font-semibold">Named NPCs</span></span>
                    </div>
                </div>

                <!-- 3. VERTICAL CHAPTER LIST WITH STACKED HORIZONTAL SPEAKER BARS -->
                <div class="w-full">
                    {vertical_chapters_html}
                </div>

            </div>

        </div>
    </div>

    {diff_inspector_html}

    <!-- ========================================================= -->
    <!-- MOBILE CRITIQUE MODAL / PASSAGE EDITOR -->
    <!-- ========================================================= -->
    <div id="critiqueModalOverlay" class="fixed inset-0 bg-slate-950/85 backdrop-blur-sm z-50 flex items-start sm:items-center justify-center opacity-0 pointer-events-none p-3 sm:p-4 overflow-y-auto box-border">
        <div id="critiqueBottomSheet" class="w-full max-w-lg bg-slate-900 border border-slate-700 rounded-2xl p-3.5 sm:p-5 shadow-2xl flex flex-col my-auto max-h-[85vh] sm:max-h-[82vh] box-border">
            
            <!-- Top Header with Speaker, Block ID, and Prev/Next Passage Navigation -->
            <div class="flex items-center justify-between border-b border-slate-800 pb-2.5 mb-3 gap-2 flex-shrink-0">
                <div class="flex items-center gap-1.5 min-w-0 flex-1">
                    <span id="modalSpeakerPill" class="px-2 py-0.5 rounded-md text-[11px] sm:text-xs font-bold uppercase tracking-wider font-mono truncate max-w-[130px] sm:max-w-none"></span>
                    <span id="modalBlockIndex" class="text-xs text-slate-400 font-mono flex-shrink-0"></span>
                </div>
                <div class="flex items-center gap-1 flex-shrink-0">
                    <!-- Shifted Arrow Keys to Top for rapid passage jumping -->
                    <button id="modalPrevBlockBtn" type="button" class="px-2 sm:px-2.5 py-1 bg-slate-800 hover:bg-slate-700 active:bg-slate-600 border border-slate-700 text-slate-200 rounded-lg text-xs font-semibold flex items-center gap-1 transition-all" title="Previous passage">
                        <span>◀</span> <span class="hidden sm:inline text-[11px]">Prev</span>
                    </button>
                    <button id="modalNextBlockBtn" type="button" class="px-2 sm:px-2.5 py-1 bg-slate-800 hover:bg-slate-700 active:bg-slate-600 border border-slate-700 text-slate-200 rounded-lg text-xs font-semibold flex items-center gap-1 transition-all" title="Next passage">
                        <span class="hidden sm:inline text-[11px]">Next</span> <span>▶</span>
                    </button>
                    <button id="modalCloseBtn" type="button" class="text-slate-400 hover:text-slate-200 text-xl font-bold p-1 ml-0.5 leading-none transition-colors" title="Close" aria-label="Close modal">&times;</button>
                </div>
            </div>

            <!-- Scrollable Content Body (Expands & Scrolls Gracefully) -->
            <div class="overflow-y-auto space-y-3 pr-1 flex-1 min-h-0 custom-scrollbar box-border">
                <div class="bg-slate-950/80 p-3 rounded-xl border border-slate-800/80 box-border">
                    <div class="flex items-center justify-between text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                        <span>Target Passage:</span>
                        <span id="modalSourceProvenance" class="font-mono text-amber-400 normal-case"></span>
                    </div>
                    <p id="modalPassageText" class="text-xs sm:text-sm text-slate-200 italic leading-relaxed max-h-28 overflow-y-auto custom-scrollbar"></p>
                </div>

                <!-- Speaker Attribution & Voice Model Selector -->
                <div class="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800/80 box-border">
                    <div class="flex items-center justify-between gap-2 mb-1.5">
                        <label for="modalSpeakerSelect" class="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1">
                            <span>🎙️</span> <span>Speaker Attribution</span>
                        </label>
                        <span id="modalSpeakerChangedBadge" class="text-[10px] text-amber-400 font-mono hidden font-semibold">● Attribution Changed</span>
                    </div>
                    <div class="flex items-center gap-2">
                        <select id="modalSpeakerSelect" class="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-amber-500 font-mono box-border">
                            <!-- Populated dynamically via openModalForBlock() -->
                        </select>
                        <button id="modalResetSpeakerBtn" type="button" class="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 text-[10px] font-bold rounded-lg font-mono hidden transition-colors" title="Reset to original speaker">
                            Reset
                        </button>
                    </div>
                </div>

                <div>
                    <label class="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">Category</label>
                    <div class="grid grid-cols-3 sm:grid-cols-6 gap-1.5" id="categoryPillContainer">
                        <button type="button" class="category-pill active px-1.5 py-1.5 rounded-lg text-[10px] sm:text-[11px] font-bold border border-amber-500 bg-amber-500/20 text-amber-300 text-center truncate" data-category="general">General</button>
                        <button type="button" class="category-pill px-1.5 py-1.5 rounded-lg text-[10px] sm:text-[11px] font-medium border border-slate-700 bg-slate-800 text-slate-300 text-center truncate" data-category="tone">Tone / Voice</button>
                        <button type="button" class="category-pill px-1.5 py-1.5 rounded-lg text-[10px] sm:text-[11px] font-medium border border-slate-700 bg-slate-800 text-slate-300 text-center truncate" data-category="continuity">Continuity</button>
                        <button type="button" class="category-pill px-1.5 py-1.5 rounded-lg text-[10px] sm:text-[11px] font-medium border border-slate-700 bg-slate-800 text-slate-300 text-center truncate" data-category="pacing">Pacing</button>
                        <button type="button" class="category-pill px-1.5 py-1.5 rounded-lg text-[10px] sm:text-[11px] font-medium border border-slate-700 bg-slate-800 text-slate-300 text-center truncate" data-category="rewrite">Rewrite</button>
                        <button type="button" class="category-pill px-1.5 py-1.5 rounded-lg text-[10px] sm:text-[11px] font-medium border border-slate-700 bg-slate-800 text-slate-300 text-center truncate" data-category="audio_cue">Audio Cue</button>
                    </div>
                </div>
                <div>
                    <label for="critiqueTextInput" class="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">Critique / Revision Directive</label>
                    <textarea id="critiqueTextInput" rows="2" class="w-full bg-slate-950 border border-slate-700 rounded-xl p-2.5 text-xs sm:text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500 box-border" placeholder="E.g. Make this interaction sharper, emphasize the tension..."></textarea>
                </div>
                <div>
                    <label for="suggestedRewriteInput" class="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">Direct Suggested Rewrite <span class="text-slate-600 font-normal lowercase">(optional)</span></label>
                    <textarea id="suggestedRewriteInput" rows="2" class="w-full bg-slate-950 border border-slate-800 rounded-xl p-2 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-cyan-500 box-border" placeholder="Provide direct replacement line if desired..."></textarea>
                </div>
            </div>

            <!-- Action Footer with Delete and Save Changes -->
            <div class="pt-3 mt-2 border-t border-slate-800 flex items-center justify-between gap-2 flex-shrink-0">
                <button id="modalDeleteBtn" type="button" class="px-3 py-2 bg-rose-950/50 hover:bg-rose-900 border border-rose-800 text-rose-300 rounded-xl text-xs font-bold transition-colors hidden">
                    🗑️ Delete Note
                </button>
                <div class="flex-1"></div>
                <button id="modalSaveBtn" type="button" class="w-full sm:w-auto px-6 py-2.5 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 text-slate-950 font-bold rounded-xl text-xs transition-all shadow-lg shadow-amber-500/20 flex items-center justify-center gap-1.5 active:scale-98">
                    <span>💾</span> <span>Save Changes</span>
                </button>
            </div>
        </div>
    </div>

    <!-- ========================================================= -->
    <!-- FIRST-TIME SESSION WELCOME & FEATURE TOUR MODAL -->
    <!-- ========================================================= -->
    <div id="onboardingModalOverlay" class="fixed inset-0 bg-slate-950/85 backdrop-blur-md z-50 flex items-center justify-center opacity-0 pointer-events-none p-4 transition-opacity duration-200">
        <div id="onboardingModalCard" class="bg-slate-900 border border-amber-500/40 rounded-2xl max-w-lg w-full p-5 sm:p-7 shadow-2xl space-y-4 text-left">
            <div class="flex items-center gap-3 border-b border-slate-800 pb-3.5">
                <div class="w-11 h-11 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-2xl flex-shrink-0">
                    ✨
                </div>
                <div>
                    <h3 class="text-lg sm:text-xl font-bold text-slate-100 font-serif">Welcome to Session {session_num}</h3>
                    <p class="text-xs sm:text-sm text-amber-400 font-mono font-medium">Interactive Reader & Critique Engine</p>
                </div>
            </div>

            <p class="text-sm sm:text-base text-slate-200 leading-relaxed">
                Experience this chronicle with rich interactive controls, character diagnostics, custom reading themes, and inline feedback:
            </p>

            <div class="space-y-3 text-sm text-slate-300">
                <!-- 1. Critique Mode & Single Toggle Matching Header -->
                <div class="bg-slate-950/70 p-3.5 rounded-xl border border-slate-800 space-y-2">
                    <div class="flex items-center justify-between gap-2">
                        <span class="font-bold text-amber-300 flex items-center gap-1.5 text-sm">
                            <span>✍️</span> <span>Reading & Critique Mode</span>
                        </span>
                        <!-- Combined Single Mode Toggle -->
                        <button id="onboardingModeToggleBtn" type="button" class="px-3 py-1.5 rounded-lg text-xs font-bold bg-gradient-to-r from-amber-400 to-amber-500 text-slate-950 border border-amber-300 shadow-md flex items-center gap-1.5 transition-all active:scale-95">
                            <span id="onboardingModeToggleIcon">✍️</span>
                            <span id="onboardingModeToggleLabel">Critique Mode</span>
                        </button>
                    </div>
                    <p id="onboardingModeDesc" class="text-xs sm:text-sm text-slate-300 leading-normal bg-slate-900/70 p-2.5 rounded-lg border border-slate-800/80">
                        <strong>Critique Mode Active:</strong> Click or tap any passage to inspect it side-by-side (or stacked) against the raw tabletop source transcript and leave editorial directives.
                    </p>
                </div>

                <!-- 2. Chapters & Diagnostics -->
                <div class="bg-slate-950/70 p-3.5 rounded-xl border border-slate-800 space-y-1.5">
                    <div class="flex items-center justify-between">
                        <span class="font-bold text-indigo-300 flex items-center gap-1.5 text-sm">
                            <span>📑</span> <span>Chapters & Session Stats</span>
                        </span>
                        <span class="text-xs text-slate-400 font-mono">Top Header</span>
                    </div>
                    <p class="text-xs sm:text-sm text-slate-300 leading-relaxed">
                        Tap <strong>📑 Chapters</strong> anytime to jump to scenes, view dialogue shares per chapter, character voice curves, sensory registers, and campaign analytics.
                    </p>
                </div>

                <!-- 3. Reading Preferences & Font Scaling -->
                <div class="bg-slate-950/70 p-3.5 rounded-xl border border-slate-800 space-y-1.5">
                    <div class="flex items-center justify-between">
                        <span class="font-bold text-emerald-300 flex items-center gap-1.5 text-sm">
                            <span>⚙️</span> <span>Font Sizing & Reading Themes</span>
                        </span>
                        <span class="text-xs text-slate-400 font-mono">Top Header</span>
                    </div>
                    <p class="text-xs sm:text-sm text-slate-300 leading-relaxed">
                        Tap the <strong>⚙️ Settings cog</strong> to adjust story font size (A− / A+) and switch between Dark 🌙, Light ☀️, and Sepia 📜 reading palettes.
                    </p>
                </div>
            </div>

            <button id="closeOnboardingBtn" type="button" class="w-full py-3.5 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 text-slate-950 font-bold rounded-xl text-sm sm:text-base transition-all shadow-lg shadow-amber-500/20 active:scale-98 flex items-center justify-center gap-2">
                <span>Start Reading Session {session_num}</span> <span>🚀</span>
            </button>
        </div>
    </div>

    <!-- ========================================================= -->
    <!-- READING SETTINGS & PREFERENCES MODAL -->
    <!-- ========================================================= -->
    <div id="settingsModalOverlay" class="fixed inset-0 bg-slate-950/80 backdrop-blur-md z-50 flex items-center justify-center opacity-0 pointer-events-none p-3 sm:p-4 transition-opacity duration-200">
        <div id="settingsModalCard" class="bg-slate-900 border border-slate-700 rounded-2xl max-w-md w-full p-5 sm:p-6 shadow-2xl flex flex-col max-h-[90vh] space-y-4 text-left">
            
            <!-- Modal Header -->
            <div class="flex justify-between items-center border-b border-slate-800 pb-3 flex-shrink-0">
                <div class="flex items-center gap-2.5">
                    <div class="w-9 h-9 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-xl">
                        ⚙️
                    </div>
                    <div>
                        <h3 class="text-slate-100 font-bold text-base font-serif">Reading Preferences</h3>
                        <p class="text-xs text-slate-400 font-mono">Font Size, Color Themes & Typography</p>
                    </div>
                </div>
                <button id="closeSettingsModalBtn" type="button" class="text-slate-400 hover:text-slate-200 text-2xl font-bold p-1 leading-none transition-colors" title="Close">&times;</button>
            </div>

            <div class="space-y-4 flex-1 overflow-y-auto pr-1 custom-scrollbar">
                
                <!-- 1. Font Size Section -->
                <div class="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2.5">
                    <div class="flex items-center justify-between">
                        <span class="text-xs font-bold uppercase tracking-wider text-amber-400 flex items-center gap-1.5 font-mono">
                            <span>🔤</span> <span>Story Font Size</span>
                        </span>
                        <span id="fontSizeDisplay" class="text-xs font-mono font-bold px-2 py-0.5 rounded bg-slate-900 border border-slate-700 text-amber-300">100%</span>
                    </div>
                    
                    <div class="flex items-center justify-between gap-2">
                        <button id="fontSizeMinusBtn" type="button" class="flex-1 py-2.5 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 active:scale-95 text-slate-200 font-bold text-sm border border-slate-700 transition-all flex items-center justify-center gap-1" title="Decrease Font Size">
                            <span>A−</span> <span class="text-[11px] text-slate-400 font-normal">Smaller</span>
                        </button>
                        <button id="fontSizeResetBtn" type="button" class="py-2.5 px-3 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-slate-200 text-xs font-semibold border border-slate-800 transition-colors" title="Reset to 100%">
                            Reset
                        </button>
                        <button id="fontSizePlusBtn" type="button" class="flex-1 py-2.5 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 active:scale-95 text-slate-200 font-bold text-sm border border-slate-700 transition-all flex items-center justify-center gap-1" title="Increase Font Size">
                            <span>A+</span> <span class="text-[11px] text-slate-400 font-normal">Larger</span>
                        </button>
                    </div>

                    <!-- Live Font Preview -->
                    <div class="p-2.5 rounded-lg bg-slate-900 border border-slate-800/80">
                        <p id="settingsFontPreview" class="text-slate-300 italic transition-all leading-normal" style="font-size: 1.0625rem;">
                            "The threads of the Weave hum softly across the pages of history..."
                        </p>
                    </div>
                </div>

                <!-- 2. Reading Theme Switcher -->
                <div class="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2.5">
                    <span class="text-xs font-bold uppercase tracking-wider text-amber-400 flex items-center gap-1.5 font-mono">
                        <span>🎨</span> <span>Color Palette Theme</span>
                    </span>
                    
                    <div class="grid grid-cols-3 gap-2 text-xs font-medium">
                        <button id="themeDarkBtn" type="button" class="p-2.5 rounded-xl border-2 border-amber-400 bg-slate-950 text-slate-100 flex flex-col items-center gap-1 transition-all shadow-sm">
                            <span class="text-base">🌙</span>
                            <span class="font-bold">Dark</span>
                        </button>
                        <button id="themeLightBtn" type="button" class="p-2.5 rounded-xl border border-slate-700 hover:border-slate-500 bg-slate-100 text-slate-900 flex flex-col items-center gap-1 transition-all">
                            <span class="text-base">☀️</span>
                            <span class="font-bold">Light</span>
                        </button>
                        <button id="themeSepiaBtn" type="button" class="p-2.5 rounded-xl border border-slate-700 hover:border-slate-500 bg-[#f6f0e2] text-[#2c221e] flex flex-col items-center gap-1 transition-all">
                            <span class="text-base">📜</span>
                            <span class="font-bold">Sepia</span>
                        </button>
                    </div>
                </div>

                <!-- 3. Reading Typography / Font Family -->
                <div class="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2.5">
                    <span class="text-xs font-bold uppercase tracking-wider text-amber-400 flex items-center gap-1.5 font-mono">
                        <span>📖</span> <span>Reading Typography</span>
                    </span>
                    
                    <div class="grid grid-cols-3 gap-2 text-xs">
                        <button id="fontSansBtn" type="button" class="p-2 rounded-xl border-2 border-amber-400 bg-slate-900 text-slate-100 font-sans text-center transition-all">
                            <span class="block font-bold">Sans</span>
                            <span class="text-[10px] text-slate-400">Outfit</span>
                        </button>
                        <button id="fontSerifBtn" type="button" class="p-2 rounded-xl border border-slate-700 bg-slate-900 text-slate-300 font-serif text-center transition-all">
                            <span class="block font-bold">Serif</span>
                            <span class="text-[10px] text-slate-400">Cinzel</span>
                        </button>
                        <button id="fontMonoBtn" type="button" class="p-2 rounded-xl border border-slate-700 bg-slate-900 text-slate-300 font-mono text-center transition-all">
                            <span class="block font-bold">Mono</span>
                            <span class="text-[10px] text-slate-400">JetBrains</span>
                        </button>
                    </div>
                </div>

            </div>

            <!-- Modal Footer -->
            <div class="pt-2 border-t border-slate-800 flex justify-end flex-shrink-0">
                <button id="closeSettingsFooterBtn" type="button" class="w-full py-2.5 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 text-slate-950 font-bold rounded-xl text-xs sm:text-sm transition-all shadow-md">
                    Done
                </button>
            </div>
        </div>
    </div>

    {critic_forum_html}

    <!-- JAVASCRIPT CONTROLLER -->
    <script>
        window.SOURCE_TRANSCRIPT_MAP = {source_mapping_json};
        window.SESSION_CHARACTERS = {session_characters_json};
        (function() {{
            const CAMPAIGN_ID = "uneraseable";
            const CHAPTER_ID = "s{session_num}";
            const STORAGE_KEY = "critiques_" + CAMPAIGN_ID + "_" + CHAPTER_ID;
            
            let critiques = {{}};
            try {{
                critiques = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{{}}");
            }} catch(e) {{
                critiques = {{}};
            }}

            let activeBlockIndex = 0;
            let selectedCategory = "general";
            const blocks = Array.from(document.querySelectorAll('.story-block'));

            const chaptersModalOverlay = document.getElementById('chaptersModalOverlay');
            const toggleChaptersBtn = document.getElementById('toggleChaptersBtn');
            const closeChaptersModalBtn = document.getElementById('closeChaptersModalBtn');
            const toggleStatsAccordionBtn = document.getElementById('toggleStatsAccordionBtn');
            const statsAccordionBody = document.getElementById('statsAccordionBody');
            const statsAccordionChevron = document.getElementById('statsAccordionChevron');

            const endSessionCriticCard = document.getElementById('endSessionCriticCard');
            const footerCriticForumBtn = document.getElementById('footerCriticForumBtn');
            const criticForumModalOverlay = document.getElementById('criticForumModalOverlay');
            const closeCriticForumBtn = document.getElementById('closeCriticForumBtn');
            const closeCriticForumFooterBtn = document.getElementById('closeCriticForumFooterBtn');
            const submitForumCommentBtn = document.getElementById('submitForumCommentBtn');
            const forumCommentInput = document.getElementById('forumCommentInput');
            const forumStatusMsg = document.getElementById('forumStatusMsg');

            // Combined Mode Toggle & Settings Elements
            const modeToggleBtn = document.getElementById('modeToggleBtn');
            const modeToggleIcon = document.getElementById('modeToggleIcon');
            const modeToggleLabel = document.getElementById('modeToggleLabel');
            const onboardingModeToggleBtn = document.getElementById('onboardingModeToggleBtn');
            const onboardingModeToggleIcon = document.getElementById('onboardingModeToggleIcon');
            const onboardingModeToggleLabel = document.getElementById('onboardingModeToggleLabel');

            const toggleSettingsBtn = document.getElementById('toggleSettingsBtn');
            const settingsModalOverlay = document.getElementById('settingsModalOverlay');
            const closeSettingsModalBtn = document.getElementById('closeSettingsModalBtn');
            const closeSettingsFooterBtn = document.getElementById('closeSettingsFooterBtn');
            const fontSizeMinusBtn = document.getElementById('fontSizeMinusBtn');
            const fontSizePlusBtn = document.getElementById('fontSizePlusBtn');
            const fontSizeResetBtn = document.getElementById('fontSizeResetBtn');
            const fontSizeDisplay = document.getElementById('fontSizeDisplay');
            const settingsFontPreview = document.getElementById('settingsFontPreview');
            const themeDarkBtn = document.getElementById('themeDarkBtn');
            const themeLightBtn = document.getElementById('themeLightBtn');
            const themeSepiaBtn = document.getElementById('themeSepiaBtn');
            const fontSansBtn = document.getElementById('fontSansBtn');
            const fontSerifBtn = document.getElementById('fontSerifBtn');
            const fontMonoBtn = document.getElementById('fontMonoBtn');

            const footerExportBtn = document.getElementById('footerExportBtn');
            const clearCritiquesBtn = document.getElementById('clearCritiquesBtn');
            const exportBadgeCount = document.getElementById('exportBadgeCount');

            const modalOverlay = document.getElementById('critiqueModalOverlay');
            const modalCloseBtn = document.getElementById('modalCloseBtn');
            const modalSpeakerPill = document.getElementById('modalSpeakerPill');
            const modalSpeakerSelect = document.getElementById('modalSpeakerSelect');
            const modalSpeakerChangedBadge = document.getElementById('modalSpeakerChangedBadge');
            const modalResetSpeakerBtn = document.getElementById('modalResetSpeakerBtn');
            const modalBlockIndex = document.getElementById('modalBlockIndex');
            const modalPassageText = document.getElementById('modalPassageText');
            const modalSourceProvenance = document.getElementById('modalSourceProvenance');
            const critiqueTextInput = document.getElementById('critiqueTextInput');
            const suggestedRewriteInput = document.getElementById('suggestedRewriteInput');
            const modalPrevBlockBtn = document.getElementById('modalPrevBlockBtn');
            const modalNextBlockBtn = document.getElementById('modalNextBlockBtn');
            const modalSaveBtn = document.getElementById('modalSaveBtn');
            const modalDeleteBtn = document.getElementById('modalDeleteBtn');
            const categoryPills = Array.from(document.querySelectorAll('.category-pill'));

            const onboardingOverlay = document.getElementById('onboardingModalOverlay');
            const closeOnboardingBtn = document.getElementById('closeOnboardingBtn');

            // =========================================================
            // DIFF INSPECTOR (Synchronized Narrative vs Source) ELEMENTS
            // =========================================================
            const diffInspectorOverlay = document.getElementById('diffInspectorOverlay');
            const diffPanesContainer = document.getElementById('diffPanesContainer');
            const diffNarrativePane = document.getElementById('diffNarrativePane');
            const diffSourcePane = document.getElementById('diffSourcePane');
            const diffLayoutToggleBtn = document.getElementById('diffLayoutToggleBtn');
            const diffLayoutToggleIcon = document.getElementById('diffLayoutToggleIcon');
            const diffLayoutToggleLabel = document.getElementById('diffLayoutToggleLabel');
            const diffSyncToggleBtn = document.getElementById('diffSyncToggleBtn');
            const diffSyncToggleIcon = document.getElementById('diffSyncToggleIcon');
            const diffSyncToggleLabel = document.getElementById('diffSyncToggleLabel');
            const closeDiffInspectorBtn = document.getElementById('closeDiffInspectorBtn');
            const diffClearCloseBtn = document.getElementById('diffClearCloseBtn');
            const diffActiveTargetBadge = document.getElementById('diffActiveTargetBadge');
            const diffHeaderTargetBadge = document.getElementById('diffHeaderTargetBadge');
            const diffSubmitFeedbackBtn = document.getElementById('diffSubmitFeedbackBtn');

            let currentDiffLayout = "hotdog";
            let syncScrollEnabled = true;
            let isProgrammaticScroll = false;
            let selectedSourceLine = null;
            let diffInspectorInitialized = false;

            function escapeHtml(str) {{
                if (!str) return "";
                return String(str)
                    .replace(/&/g, "&amp;")
                    .replace(/</g, "&lt;")
                    .replace(/>/g, "&gt;")
                    .replace(/"/g, "&quot;")
                    .replace(/'/g, "&#039;");
            }}

            // Modal Background Scroll Lock Helper
            function setBodyScrollLock(locked) {{
                if (locked) {{
                    document.body.style.overflow = 'hidden';
                }} else {{
                    const isAnyModalOpen = (
                        (diffInspectorOverlay && diffInspectorOverlay.classList.contains('visible')) ||
                        (chaptersModalOverlay && chaptersModalOverlay.classList.contains('visible')) ||
                        (modalOverlay && modalOverlay.classList.contains('visible')) ||
                        (onboardingOverlay && onboardingOverlay.classList.contains('visible')) ||
                        (criticForumModalOverlay && criticForumModalOverlay.classList.contains('visible')) ||
                        (settingsModalOverlay && settingsModalOverlay.classList.contains('visible')) ||
                        (typeof ghModalOverlay !== 'undefined' && ghModalOverlay && !ghModalOverlay.classList.contains('opacity-0'))
                    );
                    if (!isAnyModalOpen) {{
                        document.body.style.overflow = '';
                    }}
                }}
            }}

            // Diff Inspector Layout Controller (Hotdog vs Hamburger)
            function applyDiffLayout(layout) {{
                currentDiffLayout = layout;
                if (!diffPanesContainer) return;
                if (layout === 'hamburger') {{
                    diffPanesContainer.classList.remove('layout-hotdog');
                    diffPanesContainer.classList.add('layout-hamburger');
                    if (diffLayoutToggleIcon) diffLayoutToggleIcon.textContent = '⬍';
                    if (diffLayoutToggleLabel) diffLayoutToggleLabel.textContent = 'Stacked';
                    if (diffLayoutToggleBtn) diffLayoutToggleBtn.title = 'Current: Stacked (Top/Bottom) — Tap to switch to Side-by-Side';
                }} else {{
                    diffPanesContainer.classList.remove('layout-hamburger');
                    diffPanesContainer.classList.add('layout-hotdog');
                    if (diffLayoutToggleIcon) diffLayoutToggleIcon.textContent = '⬌';
                    if (diffLayoutToggleLabel) diffLayoutToggleLabel.textContent = 'Side-by-Side';
                    if (diffLayoutToggleBtn) diffLayoutToggleBtn.title = 'Current: Side-by-Side (Vertical split) — Tap to switch to Stacked';
                }}
            }}

            function toggleDiffLayout() {{
                const nextLayout = (currentDiffLayout === 'hamburger') ? 'hotdog' : 'hamburger';
                applyDiffLayout(nextLayout);
                if (activeBlockIndex >= 0) {{
                    scrollToCardInBothPanes(activeBlockIndex, false);
                }}
            }}
            if (diffLayoutToggleBtn) diffLayoutToggleBtn.onclick = toggleDiffLayout;

            function scrollToCardInBothPanes(index, smooth) {{
                const nCard = diffNarrativePane ? diffNarrativePane.querySelector(`.diff-narrative-card[data-index="${{index}}"]`) : null;
                const sCard = diffSourcePane ? diffSourcePane.querySelector(`.diff-source-card[data-index="${{index}}"]`) : null;

                isProgrammaticScroll = true;
                if (nCard) {{
                    nCard.scrollIntoView({{ behavior: smooth ? 'smooth' : 'auto', block: 'center' }});
                }}
                if (sCard) {{
                    sCard.scrollIntoView({{ behavior: smooth ? 'smooth' : 'auto', block: 'center' }});
                }}
                setTimeout(() => {{
                    isProgrammaticScroll = false;
                }}, smooth ? 450 : 60);
            }}

            function highlightBlockInDiff(index, sourceLineObj, autoScroll) {{
                if (index < 0 || index >= blocks.length) return;
                activeBlockIndex = index;
                selectedSourceLine = sourceLineObj || null;

                const block = blocks[index];
                const bId = block.dataset.blockId || ("block-" + index);
                const spName = block.dataset.speakerName || "Narrator";
                const mapData = (window.SOURCE_TRANSCRIPT_MAP && window.SOURCE_TRANSCRIPT_MAP[bId]) || null;
                const primary = mapData && mapData.primaryLine ? mapData.primaryLine : null;

                if (diffNarrativePane) {{
                    diffNarrativePane.querySelectorAll('.active-diff-card').forEach(el => el.classList.remove('active-diff-card'));
                }}
                if (diffSourcePane) {{
                    diffSourcePane.querySelectorAll('.active-diff-card').forEach(el => el.classList.remove('active-diff-card'));
                    diffSourcePane.querySelectorAll('.active-diff-line').forEach(el => el.classList.remove('active-diff-line'));
                }}

                const nCard = diffNarrativePane ? diffNarrativePane.querySelector(`.diff-narrative-card[data-index="${{index}}"]`) : null;
                if (nCard) nCard.classList.add('active-diff-card');

                const sCard = diffSourcePane ? diffSourcePane.querySelector(`.diff-source-card[data-index="${{index}}"]`) : null;
                if (sCard) {{
                    sCard.classList.add('active-diff-card');
                    if (selectedSourceLine) {{
                        const lineEl = sCard.querySelector(`.diff-source-line[data-line-num="${{selectedSourceLine.line}}"]`);
                        if (lineEl) {{
                            lineEl.classList.add('active-diff-line');
                            const drawer = lineEl.closest('.diff-bundled-drawer');
                            if (drawer && drawer.classList.contains('hidden')) {{
                                drawer.classList.remove('hidden');
                                const toggle = drawer.parentElement.querySelector('.diff-bundled-toggle');
                                if (toggle) {{
                                    const chev = toggle.querySelector('.diff-bundled-chevron');
                                    const lbl = toggle.querySelector('.font-sans');
                                    if (chev) chev.style.transform = 'rotate(180deg)';
                                    if (lbl) lbl.textContent = 'Tap to collapse';
                                }}
                            }}
                        }}
                    }}
                }}

                const lineRef = selectedSourceLine ? `L${{selectedSourceLine.line}} (${{selectedSourceLine.speaker}})` : (primary ? `L${{primary.line}} (${{primary.speaker}})` : `Passage #${{index + 1}}`);
                if (diffHeaderTargetBadge) diffHeaderTargetBadge.textContent = `#${{index + 1}} · ${{lineRef}}`;
                if (diffActiveTargetBadge) {{
                    diffActiveTargetBadge.innerHTML = `Anchor: <strong>Passage #${{index + 1}}</strong> · <span class="text-amber-400 font-semibold">${{lineRef}}</span>`;
                }}

                if (autoScroll) {{
                    scrollToCardInBothPanes(index, true);
                }}
            }}

            function setupDiffScrollSync() {{
                if (!diffNarrativePane || !diffSourcePane) return;

                function syncPanes(sourcePane, targetPane) {{
                    if (!syncScrollEnabled || isProgrammaticScroll) return;

                    const cardsSource = sourcePane.querySelectorAll('.diff-card');
                    const cardsTarget = targetPane.querySelectorAll('.diff-card');
                    if (!cardsSource.length || !cardsTarget.length) return;

                    let activeIdx = 0;
                    let progressThroughCard = 0;
                    const targetTopOffset = 50;

                    for (let i = 0; i < cardsSource.length; i++) {{
                        const card = cardsSource[i];
                        const cTop = card.offsetTop - sourcePane.scrollTop;
                        if (cTop <= targetTopOffset && (cTop + card.offsetHeight) > targetTopOffset) {{
                            activeIdx = i;
                            progressThroughCard = (targetTopOffset - cTop) / card.offsetHeight;
                            break;
                        }} else if (cTop > targetTopOffset) {{
                            activeIdx = Math.max(0, i - 1);
                            break;
                        }}
                    }}

                    if (cardsTarget[activeIdx]) {{
                        const targetCard = cardsTarget[activeIdx];
                        const desiredScrollTop = targetCard.offsetTop - targetTopOffset + (progressThroughCard * targetCard.offsetHeight);
                        isProgrammaticScroll = true;
                        targetPane.scrollTop = Math.max(0, desiredScrollTop);
                        requestAnimationFrame(() => {{
                            isProgrammaticScroll = false;
                        }});
                    }}
                }}

                diffNarrativePane.addEventListener('scroll', function() {{
                    syncPanes(diffNarrativePane, diffSourcePane);
                }}, {{ passive: true }});

                diffSourcePane.addEventListener('scroll', function() {{
                    syncPanes(diffSourcePane, diffNarrativePane);
                }}, {{ passive: true }});

                if (diffSyncToggleBtn) {{
                    diffSyncToggleBtn.onclick = function() {{
                        syncScrollEnabled = !syncScrollEnabled;
                        if (syncScrollEnabled) {{
                            if (diffSyncToggleIcon) diffSyncToggleIcon.textContent = '🔗';
                            if (diffSyncToggleLabel) diffSyncToggleLabel.textContent = 'Sync: ON';
                            diffSyncToggleBtn.className = "px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-emerald-400 rounded-lg text-xs font-semibold flex items-center gap-1 transition-all shadow-sm";
                            diffSyncToggleBtn.title = "Synchronized Scrolling is ON — tap to disable";
                        }} else {{
                            if (diffSyncToggleIcon) diffSyncToggleIcon.textContent = '🔓';
                            if (diffSyncToggleLabel) diffSyncToggleLabel.textContent = 'Sync: OFF';
                            diffSyncToggleBtn.className = "px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-400 rounded-lg text-xs font-semibold flex items-center gap-1 transition-all shadow-sm";
                            diffSyncToggleBtn.title = "Synchronized Scrolling is OFF — tap to enable";
                        }}
                    }};
                }}
            }}

            function initDiffInspector() {{
                if (diffInspectorInitialized || !diffNarrativePane || !diffSourcePane) return;
                diffInspectorInitialized = true;

                applyDiffLayout(currentDiffLayout);

                let narrativeCardsHtml = `
                    <div class="sticky top-0 z-10 -mt-1 mb-2 px-3 py-1.5 rounded-lg bg-slate-900/90 backdrop-blur border border-slate-800 flex items-center justify-between text-[11px] font-mono font-bold text-amber-400 shadow-sm">
                        <span>📖 NOVEL PROSE</span>
                        <span class="text-[10px] text-slate-400 font-sans">Passage View</span>
                    </div>
                `;
                let sourceCardsHtml = `
                    <div class="sticky top-0 z-10 -mt-1 mb-2 px-3 py-1.5 rounded-lg bg-slate-900/90 backdrop-blur border border-slate-800 flex items-center justify-between text-[11px] font-mono font-bold text-cyan-400 shadow-sm">
                        <span>🎲 TABLETOP SOURCE</span>
                        <span class="text-[10px] text-slate-400 font-sans">Raw Transcript</span>
                    </div>
                `;

                blocks.forEach((block, idx) => {{
                    const bId = block.dataset.blockId || ("block-" + idx);
                    const spName = block.dataset.speakerName || "Narrator";
                    const spColor = block.dataset.speakerColor || "#94a3b8";
                    const p = block.querySelector('p');
                    const text = p ? p.innerText : "";
                    const mapData = (window.SOURCE_TRANSCRIPT_MAP && window.SOURCE_TRANSCRIPT_MAP[bId]) || null;

                    const lineRangeText = mapData && mapData.lineRange ? `Lines ${{mapData.lineRange[0]}}–${{mapData.lineRange[1]}}` : "";
                    const primary = (mapData && mapData.primaryLine) ? mapData.primaryLine : {{
                        line: (mapData && mapData.lineRange ? mapData.lineRange[0] : (idx + 1)),
                        speaker: spName,
                        text: text
                    }};
                    const bundled = (mapData && mapData.bundledLines) ? mapData.bundledLines : [];

                    narrativeCardsHtml += `
                        <div class="diff-narrative-card diff-card p-2.5 sm:p-4 rounded-xl border border-slate-800 bg-slate-900/60 hover:bg-slate-900/90 transition-all cursor-pointer relative" data-block-id="${{bId}}" data-index="${{idx}}">
                            <div class="flex items-center justify-between mb-2 text-xs gap-1">
                                <div class="flex items-center gap-1.5 min-w-0">
                                    <span class="px-2 py-0.5 rounded text-[10px] font-bold font-mono truncate max-w-[90px] xs:max-w-[130px] sm:max-w-none" style="background-color: ${{spColor}}25; color: ${{spColor}}; border: 1px solid ${{spColor}}50">${{spName}}</span>
                                    <span class="text-slate-400 font-mono text-[10px] flex-shrink-0">#${{idx + 1}}</span>
                                </div>
                                ${{lineRangeText ? `<div class="text-[10px] font-mono text-slate-500 whitespace-nowrap flex-shrink-0">${{lineRangeText}}</div>` : ''}}
                            </div>
                            <p class="text-xs sm:text-sm text-slate-200 leading-relaxed font-serif">${{escapeHtml(text)}}</p>
                        </div>
                    `;

                    let bundledSectionHtml = "";
                    if (bundled.length > 0) {{
                        let bundledItemsHtml = "";
                        bundled.forEach(bLine => {{
                            bundledItemsHtml += `
                                <div class="diff-source-line bundled-source-line p-2 rounded-lg bg-slate-950/70 border border-slate-800/80 hover:border-amber-500/50 cursor-pointer transition-colors" data-block-id="${{bId}}" data-index="${{idx}}" data-line-num="${{bLine.line}}" data-speaker="${{escapeHtml(bLine.speaker)}}" data-text="${{escapeHtml(bLine.text)}}">
                                    <div class="flex items-center gap-1.5 text-[10px] font-mono mb-1">
                                        <span class="text-amber-400 font-bold">L${{bLine.line}}</span>
                                        <span class="text-slate-500">·</span>
                                        <span class="text-slate-300 font-semibold truncate max-w-[110px] sm:max-w-none">${{escapeHtml(bLine.speaker)}}</span>
                                    </div>
                                    <div class="text-slate-300 font-mono text-[11px] leading-relaxed whitespace-pre-wrap">${{escapeHtml(bLine.text)}}</div>
                                </div>
                            `;
                        }});

                        bundledSectionHtml = `
                            <div class="mt-2.5">
                                <button type="button" class="diff-bundled-toggle w-full px-2.5 py-1.5 rounded-lg bg-slate-800/90 hover:bg-slate-800 border border-slate-700/80 text-left text-xs font-mono text-amber-300/90 flex items-center justify-between transition-colors shadow-sm" data-block-id="${{bId}}">
                                    <span class="flex items-center gap-1.5">
                                        <span class="diff-bundled-chevron inline-block transition-transform duration-200 text-[10px]">▼</span>
                                        <span>${{bundled.length}} tabletop turn${{bundled.length > 1 ? 's' : ''}} bundled</span>
                                    </span>
                                    <span class="text-[10px] text-slate-400 font-sans">Tap to expand</span>
                                </button>
                                <div class="diff-bundled-drawer hidden mt-2 space-y-2 pl-2 border-l-2 border-amber-500/30">
                                    ${{bundledItemsHtml}}
                                </div>
                            </div>
                        `;
                    }}

                    const isSynth = primary.isSynthesis || !primary.line;
                    let primaryTurnHtml = "";
                    if (isSynth) {{
                        primaryTurnHtml = `
                            <div class="diff-source-line synthesis-source-line p-2 sm:p-2.5 rounded-lg bg-indigo-950/40 border border-indigo-500/30 hover:border-indigo-500/60 cursor-pointer transition-colors" data-block-id="${{bId}}" data-index="${{idx}}" data-line-num="" data-speaker="Narrative Synthesis" data-text="${{escapeHtml(primary.text)}}">
                                <div class="flex items-center gap-1.5 text-[10px] font-mono mb-1">
                                    <span class="px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-bold border border-indigo-500/40">🔮 Narrative Synthesis</span>
                                    <span class="ml-auto text-[9px] text-indigo-400 font-mono tracking-wider">Scene Bridge</span>
                                </div>
                                <div class="text-indigo-200 font-sans text-[11px] sm:text-xs leading-relaxed italic">${{escapeHtml(primary.text)}}</div>
                            </div>
                        `;
                    }} else {{
                        primaryTurnHtml = `
                            <div class="diff-source-line primary-source-line p-2 sm:p-2.5 rounded-lg bg-slate-950/80 border border-slate-800/90 hover:border-amber-500/50 cursor-pointer transition-colors" data-block-id="${{bId}}" data-index="${{idx}}" data-line-num="${{primary.line}}" data-speaker="${{escapeHtml(primary.speaker)}}" data-text="${{escapeHtml(primary.text)}}">
                                <div class="flex items-center gap-1.5 text-[10px] font-mono mb-1">
                                    <span class="text-amber-400 font-bold">L${{primary.line}}</span>
                                    <span class="text-slate-500">·</span>
                                    <span class="text-slate-300 font-semibold truncate max-w-[110px] sm:max-w-none">${{escapeHtml(primary.speaker)}}</span>
                                    <span class="ml-auto text-[9px] text-amber-500/80 uppercase font-mono tracking-wider flex-shrink-0">Primary</span>
                                </div>
                                <div class="text-slate-200 font-mono text-[11px] sm:text-xs leading-relaxed whitespace-pre-wrap">${{escapeHtml(primary.text)}}</div>
                            </div>
                        `;
                    }}

                    sourceCardsHtml += `
                        <div class="diff-source-card diff-card p-2.5 sm:p-4 rounded-xl border border-slate-800 bg-slate-900/60 hover:bg-slate-900/90 transition-all relative" data-block-id="${{bId}}" data-index="${{idx}}">
                            <div class="flex items-center justify-between mb-2 text-xs gap-1">
                                <div class="flex items-center gap-1.5">
                                    <span class="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-950/80 text-cyan-300 border border-cyan-800 flex-shrink-0">Source #${{idx + 1}}</span>
                                </div>
                                ${{lineRangeText ? `<span class="text-[10px] font-mono text-slate-400 whitespace-nowrap flex-shrink-0">${{lineRangeText}}</span>` : ''}}
                            </div>
                            
                            <!-- Primary Source Turn or Synthesis Card -->
                            ${{primaryTurnHtml}}

                            ${{bundledSectionHtml}}
                        </div>
                    `;
                }});

                diffNarrativePane.innerHTML = narrativeCardsHtml;
                diffSourcePane.innerHTML = sourceCardsHtml;

                diffNarrativePane.querySelectorAll('.diff-narrative-card').forEach(card => {{
                    card.addEventListener('click', function() {{
                        const idx = parseInt(card.dataset.index);
                        highlightBlockInDiff(idx, null, false);
                    }});
                }});

                diffSourcePane.querySelectorAll('.diff-source-line').forEach(lineEl => {{
                    lineEl.addEventListener('click', function(e) {{
                        e.stopPropagation();
                        const idx = parseInt(lineEl.dataset.index);
                        const lineNum = parseInt(lineEl.dataset.lineNum);
                        const speaker = lineEl.dataset.speaker;
                        const text = lineEl.dataset.text;
                        highlightBlockInDiff(idx, {{ line: lineNum, speaker: speaker, text: text }}, false);
                    }});
                }});

                diffSourcePane.querySelectorAll('.diff-source-card').forEach(card => {{
                    card.addEventListener('click', function(e) {{
                        if (e.target.closest('.diff-bundled-toggle') || e.target.closest('.diff-source-line')) return;
                        const idx = parseInt(card.dataset.index);
                        highlightBlockInDiff(idx, null, false);
                    }});
                }});

                diffSourcePane.querySelectorAll('.diff-bundled-toggle').forEach(btn => {{
                    btn.addEventListener('click', function(e) {{
                        e.stopPropagation();
                        const container = btn.parentElement;
                        const drawer = container.querySelector('.diff-bundled-drawer');
                        const chevron = btn.querySelector('.diff-bundled-chevron');
                        const label = btn.querySelector('.font-sans');
                        if (drawer) {{
                            const isHidden = drawer.classList.contains('hidden');
                            drawer.classList.toggle('hidden');
                            if (chevron) chevron.style.transform = isHidden ? 'rotate(180deg)' : '';
                            if (label) label.textContent = isHidden ? 'Tap to collapse' : 'Tap to expand';
                        }}
                    }});
                }});

                setupDiffScrollSync();
            }}

            window.openDiffInspector = function(index) {{
                if (index < 0 || index >= blocks.length) return;
                initDiffInspector();
                if (diffInspectorOverlay) {{
                    diffInspectorOverlay.classList.add('visible');
                    if (window.visualViewport) {{
                        diffInspectorOverlay.style.height = window.visualViewport.height + 'px';
                        diffInspectorOverlay.style.transform = 'translateY(' + window.visualViewport.offsetTop + 'px)';
                    }}
                    setBodyScrollLock(true);
                }}
                highlightBlockInDiff(index, null, true);
            }};

            window.closeDiffInspector = function() {{
                if (diffInspectorOverlay) {{
                    diffInspectorOverlay.classList.remove('visible');
                    diffInspectorOverlay.style.height = '';
                    diffInspectorOverlay.style.transform = '';
                    setBodyScrollLock(false);
                }}
            }};

            if (closeDiffInspectorBtn) closeDiffInspectorBtn.onclick = window.closeDiffInspector;
            if (diffClearCloseBtn) {{
                diffClearCloseBtn.onclick = function() {{
                    if (diffNarrativePane) diffNarrativePane.querySelectorAll('.active-diff-card').forEach(el => el.classList.remove('active-diff-card'));
                    if (diffSourcePane) {{
                        diffSourcePane.querySelectorAll('.active-diff-card').forEach(el => el.classList.remove('active-diff-card'));
                        diffSourcePane.querySelectorAll('.active-diff-line').forEach(el => el.classList.remove('active-diff-line'));
                    }}
                    selectedSourceLine = null;
                    window.closeDiffInspector();
                }};
            }}
            if (diffSubmitFeedbackBtn) {{
                diffSubmitFeedbackBtn.onclick = function() {{
                    const targetIdx = activeBlockIndex;
                    window.closeDiffInspector();
                    openModalForBlock(targetIdx);
                }};
            }}

            // Smooth Scroll & Jump Helper
            window.scrollToAnchor = function(id) {{
                const el = document.getElementById(id);
                if (el) {{
                    el.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                }}
            }};

            window.jumpToChapter = function(id) {{
                closeChaptersModal();
                setTimeout(() => {{
                    window.scrollToAnchor(id);
                }}, 150);
            }};

            // Chapters Modal Open / Close with Scroll Lock
            window.openChaptersModal = function() {{
                if (chaptersModalOverlay) {{
                    chaptersModalOverlay.classList.add('visible');
                    setBodyScrollLock(true);
                }}
            }};

            window.closeChaptersModal = function() {{
                if (chaptersModalOverlay) {{
                    chaptersModalOverlay.classList.remove('visible');
                    chaptersModalOverlay.style.height = '';
                    chaptersModalOverlay.style.transform = '';
                    setBodyScrollLock(false);
                }}
            }};

            if (toggleChaptersBtn) toggleChaptersBtn.onclick = openChaptersModal;
            if (closeChaptersModalBtn) closeChaptersModalBtn.onclick = closeChaptersModal;
            if (chaptersModalOverlay) {{
                chaptersModalOverlay.onclick = function(e) {{
                    if (e.target === chaptersModalOverlay) closeChaptersModal();
                }};
            }}

            // First-Time Critique Onboarding
            function closeOnboardingModal() {{
                if (onboardingOverlay) {{
                    onboardingOverlay.classList.add('opacity-0', 'pointer-events-none');
                    onboardingOverlay.classList.remove('visible');
                    onboardingOverlay.style.height = '';
                    onboardingOverlay.style.transform = '';
                    try {{ localStorage.setItem('dnd_seen_critique_onboarding', 'true'); }} catch(e) {{}}
                    setBodyScrollLock(false);
                }}
            }}

            if (closeOnboardingBtn) closeOnboardingBtn.onclick = closeOnboardingModal;
            if (onboardingOverlay) {{
                onboardingOverlay.onclick = function(e) {{
                    if (e.target === onboardingOverlay) closeOnboardingModal();
                }};
            }}

            try {{
                const seenOnboarding = localStorage.getItem('dnd_seen_critique_onboarding');
                if (!seenOnboarding && onboardingOverlay) {{
                    setTimeout(() => {{
                        onboardingOverlay.classList.remove('opacity-0', 'pointer-events-none');
                        onboardingOverlay.classList.add('visible');
                        setBodyScrollLock(true);
                    }}, 600);
                }}
            }} catch(e) {{}}

            // =========================================================
            // CHAPTER BREADCRUMB & READING PROGRESS ENGINE
            // =========================================================
            function interpolateRgb(c1, c2, t) {{
                const r = Math.round(c1[0] + (c2[0] - c1[0]) * t);
                const g = Math.round(c1[1] + (c2[1] - c1[1]) * t);
                const b = Math.round(c1[2] + (c2[2] - c1[2]) * t);
                return 'rgb(' + r + ',' + g + ',' + b + ')';
            }}

            function getReadingGradientColor(pct) {{
                // 0% -> #2563eb (37, 99, 235), 50% -> #38bdf8 (56, 189, 248), 100% -> #67e8f9 (103, 232, 249)
                const p = Math.min(100, Math.max(0, pct));
                if (p <= 50) {{
                    return interpolateRgb([37, 99, 235], [56, 189, 248], p / 50);
                }} else {{
                    return interpolateRgb([56, 189, 248], [103, 232, 249], (p - 50) / 50);
                }}
            }}

            function getCompletionGradientColor(pct) {{
                // 0% -> #86efac (134, 239, 172) Light Green -> 50% -> #34d399 (52, 211, 153) Emerald -> 100% -> #06b6d4 (6, 182, 212) Cyan Green
                const p = Math.min(100, Math.max(0, pct));
                if (p <= 50) {{
                    return interpolateRgb([134, 239, 172], [52, 211, 153], p / 50);
                }} else {{
                    return interpolateRgb([52, 211, 153], [6, 182, 212], (p - 50) / 50);
                }}
            }}

            function initChapterBreadcrumbs() {{
                const breadcrumbsContainer = document.getElementById('readingProgressBreadcrumbs');
                if (!breadcrumbsContainer) return;

                const chapters = Array.from(document.querySelectorAll('section[id^="chapter-"]'));
                const totalScroll = document.documentElement.scrollHeight - window.innerHeight;
                if (totalScroll <= 0 || chapters.length === 0) return;

                breadcrumbsContainer.innerHTML = '';
                chapters.forEach((ch, idx) => {{
                    const top = ch.getBoundingClientRect().top + window.scrollY;
                    const pct = Math.min(98, Math.max(1, Math.round((top / totalScroll) * 100)));
                    
                    const dot = document.createElement('div');
                    dot.className = "reading-chapter-pip absolute top-1/2 -translate-y-1/2 -translate-x-1/2 rounded-full transition-all duration-200 pointer-events-auto cursor-pointer";
                    dot.style.left = pct + '%';
                    dot.style.width = '2.5px';
                    dot.style.height = '2.5px';
                    dot.setAttribute('data-pct', pct);
                    dot.title = (ch.querySelector('h3') ? ch.querySelector('h3').textContent.trim() : ('Chapter ' + (idx + 1))) + ' (' + pct + '%)';
                    dot.onclick = () => ch.scrollIntoView({{ behavior: 'smooth' }});
                    breadcrumbsContainer.appendChild(dot);
                }});
            }}

            function updateTopProgressBar() {{
                const totalScroll = document.documentElement.scrollHeight - window.innerHeight;
                const progress = totalScroll > 0 ? (window.scrollY / totalScroll) * 100 : 0;
                const bar = document.getElementById('readingProgressBar');
                const pip = document.getElementById('readingProgressFinishedPip');
                const maxDepth = (typeof localTelemetry !== 'undefined' && localTelemetry) ? (localTelemetry.maxDepth || 0) : progress;
                const isFinishedBefore = (typeof localTelemetry !== 'undefined') && localTelemetry && (localTelemetry.completed || (maxDepth >= 95));
                const isComplete = (isFinishedBefore || progress >= 95);

                if (pip) {{
                    pip.classList.toggle('hidden', !isComplete);
                }}

                // Update breadcrumb pips: Clean and hidden during first read, glowing green trail when completed
                const breadcrumbs = document.querySelectorAll('#readingProgressBreadcrumbs [data-pct]');
                breadcrumbs.forEach(dot => {{
                    const pct = parseFloat(dot.getAttribute('data-pct'));
                    
                    if (isComplete) {{
                        // Finished: Chapter pips glow in exact interpolated Light Green -> Cyan Green gradient
                        const col = getCompletionGradientColor(pct);
                        dot.style.backgroundColor = col;
                        dot.style.boxShadow = '0 0 5px ' + col;
                        dot.style.opacity = '1';
                        dot.style.display = 'block';
                    }} else {{
                        // In-Progress first read: Hidden for a sleek, clean reading bar
                        dot.style.opacity = '0';
                        dot.style.boxShadow = 'none';
                        dot.style.display = 'none';
                    }}
                }});

                if (bar) {{
                    bar.style.width = Math.min(100, Math.max(0, progress)) + '%';
                    if (isComplete) {{
                        // Persist rich Light Green to Cyan Green gradient across full bar even when scrolling back
                        bar.style.background = "linear-gradient(90deg, #86efac 0%, #34d399 50%, #06b6d4 100%)";
                        bar.style.boxShadow = "0 0 8px rgba(52,211,153,0.7)";
                    }} else {{
                        bar.style.background = "linear-gradient(90deg, #2563eb 0%, #38bdf8 50%, #67e8f9 100%)";
                        bar.style.boxShadow = "none";
                    }}
                }}
            }}

            window.addEventListener('resize', () => {{
                initChapterBreadcrumbs();
                updateTopProgressBar();
            }});
            window.addEventListener('scroll', updateTopProgressBar, {{ passive: true }});
            setTimeout(() => {{
                initChapterBreadcrumbs();
                updateTopProgressBar();
            }}, 150);

            // Stats Accordion Toggle (Defaults to Collapsed)
            if (toggleStatsAccordionBtn && statsAccordionBody && statsAccordionChevron) {{
                toggleStatsAccordionBtn.onclick = function() {{
                    const isHidden = statsAccordionBody.classList.contains('hidden');
                    if (isHidden) {{
                        statsAccordionBody.classList.remove('hidden');
                        statsAccordionChevron.innerHTML = '<span>▲</span> <span>Collapse</span>';
                    }} else {{
                        statsAccordionBody.classList.add('hidden');
                        statsAccordionChevron.innerHTML = '<span>▼</span> <span>Expand</span>';
                    }}
                }};
            }}

            // Analytics Tab Switcher
            window.switchChartTab = function(tabName) {{
                const sessionView = document.getElementById('chartViewSession');
                const campView = document.getElementById('chartViewCampaign');
                
                const statsBtn = document.getElementById('chartTabStatsBtn');
                const campBtn = document.getElementById('chartTabCampaignBtn');
                
                const activeClass = "px-2.5 py-1 rounded-md text-[11px] font-bold text-slate-950 bg-amber-400 shadow transition-all flex items-center gap-1";
                const inactiveClass = "px-2.5 py-1 rounded-md text-[11px] font-medium text-slate-400 hover:text-slate-200 transition-all flex items-center gap-1";
                
                if (sessionView) sessionView.classList.toggle('hidden', tabName !== 'session');
                if (campView) campView.classList.toggle('hidden', tabName !== 'campaign');
                
                if (statsBtn) statsBtn.className = (tabName === 'session') ? activeClass : inactiveClass;
                if (campBtn) campBtn.className = (tabName === 'campaign') ? activeClass : inactiveClass;
            }};

            function refreshMarkers() {{
                const count = Object.keys(critiques).length;
                if (exportBadgeCount) exportBadgeCount.textContent = count;

                blocks.forEach((el) => {{
                    const id = el.dataset.blockId;
                    const dot = el.querySelector('.critique-indicator-dot');
                    if (critiques[id]) {{
                        el.classList.add('has-critique');
                        if (dot) dot.classList.remove('hidden');
                    }} else {{
                        el.classList.remove('has-critique');
                        if (dot) dot.classList.add('hidden');
                    }}
                }});
            }}

            const onbModeDesc = document.getElementById('onboardingModeDesc');
            let currentReadingMode = "critique";

            window.toggleReadingMode = function() {{
                const nextMode = (currentReadingMode === 'critique') ? 'read' : 'critique';
                window.setReadingMode(nextMode);
            }};

            window.setReadingMode = function(mode) {{
                currentReadingMode = mode;
                const isCritique = (mode === 'critique');
                if (isCritique) {{
                    document.body.classList.add('mode-critique');
                }} else {{
                    document.body.classList.remove('mode-critique');
                }}

                // Update Sticky Header Combined Toggle
                if (modeToggleBtn) {{
                    if (isCritique) {{
                        modeToggleBtn.className = "px-2.5 sm:px-3 py-1.5 rounded-lg text-xs font-bold bg-gradient-to-r from-amber-400 to-amber-500 hover:from-amber-300 text-slate-950 border border-amber-300 shadow-md ring-2 ring-amber-400/30 transition-all flex items-center gap-1.5 active:scale-95";
                        if (modeToggleIcon) modeToggleIcon.textContent = "✍️";
                        if (modeToggleLabel) modeToggleLabel.textContent = "Critique";
                        modeToggleBtn.title = "Critique Mode is Active — tap to toggle to Read Mode";
                    }} else {{
                        modeToggleBtn.className = "px-2.5 sm:px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-all flex items-center gap-1.5 active:scale-95";
                        if (modeToggleIcon) modeToggleIcon.textContent = "📖";
                        if (modeToggleLabel) modeToggleLabel.textContent = "Read";
                        modeToggleBtn.title = "Read Mode is Active — tap to enable Critique Mode";
                    }}
                }}

                // Update Onboarding Combined Toggle
                if (onboardingModeToggleBtn) {{
                    if (isCritique) {{
                        onboardingModeToggleBtn.className = "px-3 py-1.5 rounded-lg text-xs font-bold bg-gradient-to-r from-amber-400 to-amber-500 text-slate-950 border border-amber-300 shadow-md flex items-center gap-1.5 transition-all active:scale-95";
                        if (onboardingModeToggleIcon) onboardingModeToggleIcon.textContent = "✍️";
                        if (onboardingModeToggleLabel) onboardingModeToggleLabel.textContent = "Critique Mode";
                    }} else {{
                        onboardingModeToggleBtn.className = "px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-all flex items-center gap-1.5 active:scale-95";
                        if (onboardingModeToggleIcon) onboardingModeToggleIcon.textContent = "📖";
                        if (onboardingModeToggleLabel) onboardingModeToggleLabel.textContent = "Read Mode";
                    }}
                }}

                if (onbModeDesc) {{
                    if (isCritique) {{
                        onbModeDesc.innerHTML = '<strong>Critique Mode Active:</strong> Click or tap any passage to leave review notes, tone directives, or suggested rewrites.';
                    }} else {{
                        onbModeDesc.innerHTML = '<strong>Read Mode Active:</strong> Story commenting is turned off for clean, uninterrupted reading flow.';
                    }}
                }}
            }};

            if (modeToggleBtn) modeToggleBtn.onclick = window.toggleReadingMode;
            if (onboardingModeToggleBtn) onboardingModeToggleBtn.onclick = window.toggleReadingMode;

            categoryPills.forEach(pill => {{
                pill.onclick = function() {{
                    categoryPills.forEach(p => {{
                        p.className = "category-pill px-2 py-1.5 rounded-lg text-[11px] font-medium border border-slate-700 bg-slate-800 text-slate-300 text-center";
                    }});
                    pill.className = "category-pill active px-2 py-1.5 rounded-lg text-[11px] font-bold border border-amber-500 bg-amber-500/20 text-amber-300 text-center";
                    selectedCategory = pill.dataset.category || "general";
                }};
            }});

            function openModalForBlock(index) {{
                if (index < 0 || index >= blocks.length) return;
                activeBlockIndex = index;
                const block = blocks[index];
                const blockId = block.dataset.blockId || "block";
                const speakerName = block.dataset.speakerName || "Narrator";
                const speakerColor = block.dataset.speakerColor || "#94a3b8";
                const p = block.querySelector('p');
                const text = p ? p.innerText : "";

                const originalSpeakerId = (block.dataset.speaker || "narrator").toLowerCase().trim();
                const originalSpeakerName = block.dataset.speakerName || "Narrator";
                const originalSpeakerColor = block.dataset.speakerColor || "#94a3b8";

                // Populate Speaker Attribution Selector
                if (modalSpeakerSelect) {{
                    modalSpeakerSelect.innerHTML = '';
                    const chars = window.SESSION_CHARACTERS || {{}};

                    if (!chars[originalSpeakerId]) {{
                        chars[originalSpeakerId] = {{ name: originalSpeakerName, color: originalSpeakerColor, type: (originalSpeakerId === 'narrator' ? 'narrator' : 'npc') }};
                    }}

                    const sortedKeys = Object.keys(chars).sort((a, b) => {{
                        const typeOrder = {{ 'character': 1, 'npc': 2, 'narrator': 3 }};
                        const orderA = typeOrder[chars[a].type] || 2;
                        const orderB = typeOrder[chars[b].type] || 2;
                        if (orderA !== orderB) return orderA - orderB;
                        return (chars[a].name || a).localeCompare(chars[b].name || b);
                    }});

                    sortedKeys.forEach(cid => {{
                        const cdata = chars[cid];
                        const opt = document.createElement('option');
                        opt.value = cid;
                        const typeTag = cdata.type === 'character' ? ' [PC]' : (cdata.type === 'narrator' ? ' [Narrator]' : ' [NPC]');
                        opt.textContent = (cdata.name || cid) + typeTag;
                        modalSpeakerSelect.appendChild(opt);
                    }});

                    const currentSuggested = (existing && existing.suggestedSpeaker) ? existing.suggestedSpeaker : originalSpeakerId;
                    modalSpeakerSelect.value = currentSuggested;

                    function updateSpeakerUi() {{
                        const isChanged = (modalSpeakerSelect.value !== originalSpeakerId);
                        if (modalSpeakerChangedBadge) {{
                            if (isChanged) modalSpeakerChangedBadge.classList.remove('hidden');
                            else modalSpeakerChangedBadge.classList.add('hidden');
                        }}
                        if (modalResetSpeakerBtn) {{
                            if (isChanged) modalResetSpeakerBtn.classList.remove('hidden');
                            else modalResetSpeakerBtn.classList.add('hidden');
                        }}

                        const activeCid = modalSpeakerSelect.value;
                        const activeChar = chars[activeCid] || {{}};
                        const activeName = activeChar.name || activeCid;
                        const activeColor = activeChar.color || (activeCid === 'narrator' ? '#94a3b8' : '#f87171');

                        if (modalSpeakerPill) {{
                            modalSpeakerPill.textContent = activeName + (isChanged ? " (Proposed)" : "");
                            modalSpeakerPill.style.backgroundColor = activeColor + "25";
                            modalSpeakerPill.style.borderColor = activeColor;
                            modalSpeakerPill.style.color = activeColor;
                        }}
                    }}

                    modalSpeakerSelect.onchange = updateSpeakerUi;
                    if (modalResetSpeakerBtn) {{
                        modalResetSpeakerBtn.onclick = function() {{
                            modalSpeakerSelect.value = originalSpeakerId;
                            updateSpeakerUi();
                        }};
                    }}
                    updateSpeakerUi();
                }} else if (modalSpeakerPill) {{
                    modalSpeakerPill.textContent = originalSpeakerName;
                    modalSpeakerPill.style.backgroundColor = originalSpeakerColor + "25";
                    modalSpeakerPill.style.borderColor = originalSpeakerColor;
                    modalSpeakerPill.style.color = originalSpeakerColor;
                }}
                if (modalBlockIndex) modalBlockIndex.textContent = "#" + (index + 1) + " (" + blockId + ")";
                if (modalPassageText) modalPassageText.textContent = '"' + text + '"';

                const mapData = (window.SOURCE_TRANSCRIPT_MAP && window.SOURCE_TRANSCRIPT_MAP[blockId]) || null;
                if (modalSourceProvenance) {{
                    if (selectedSourceLine) {{
                        modalSourceProvenance.textContent = `· L${{selectedSourceLine.line}} (${{selectedSourceLine.speaker}})`;
                    }} else if (mapData && mapData.primaryLine) {{
                        modalSourceProvenance.textContent = `· L${{mapData.primaryLine.line}} (${{mapData.primaryLine.speaker}})`;
                    }} else {{
                        modalSourceProvenance.textContent = '';
                    }}
                }}

                const existing = critiques[blockId];
                if (existing) {{
                    if (critiqueTextInput) critiqueTextInput.value = existing.comment || "";
                    if (suggestedRewriteInput) suggestedRewriteInput.value = existing.suggestedRewrite || "";
                    selectedCategory = existing.category || "general";
                    if (modalDeleteBtn) modalDeleteBtn.classList.remove('hidden');

                    categoryPills.forEach(pill => {{
                        if (pill.dataset.category === selectedCategory) pill.click();
                    }});
                }} else {{
                    if (critiqueTextInput) critiqueTextInput.value = "";
                    if (suggestedRewriteInput) suggestedRewriteInput.value = "";
                    if (modalDeleteBtn) modalDeleteBtn.classList.add('hidden');
                    selectedCategory = "general";
                    categoryPills.forEach(pill => {{
                        if (pill.dataset.category === "general") pill.click();
                    }});
                }}

                if (modalPrevBlockBtn) {{
                    modalPrevBlockBtn.disabled = (index === 0);
                    modalPrevBlockBtn.style.opacity = (index === 0) ? "0.35" : "1";
                    modalPrevBlockBtn.style.pointerEvents = (index === 0) ? "none" : "auto";
                }}
                if (modalNextBlockBtn) {{
                    modalNextBlockBtn.disabled = (index === blocks.length - 1);
                    modalNextBlockBtn.style.opacity = (index === blocks.length - 1) ? "0.35" : "1";
                    modalNextBlockBtn.style.pointerEvents = (index === blocks.length - 1) ? "none" : "auto";
                }}
                if (modalOverlay) {{
                    modalOverlay.classList.add('visible');
                    if (window.visualViewport) {{
                        modalOverlay.style.height = window.visualViewport.height + 'px';
                        modalOverlay.style.transform = 'translateY(' + window.visualViewport.offsetTop + 'px)';
                    }}
                    setBodyScrollLock(true);
                }}
                if (critiqueTextInput) {{
                    setTimeout(() => {{
                        critiqueTextInput.focus();
                        critiqueTextInput.scrollIntoView({{ behavior: 'smooth', block: 'nearest' }});
                    }}, 80);
                }}
            }}

            function closeModal() {{
                if (modalOverlay) {{
                    modalOverlay.classList.remove('visible');
                    modalOverlay.style.height = '';
                    modalOverlay.style.transform = '';
                    setBodyScrollLock(false);
                }}
            }}

            // Dynamic Mobile Virtual Keyboard Sizing & Push-Up Controller
            if (window.visualViewport) {{
                function syncActiveModalWithViewport() {{
                    const vh = window.visualViewport.height;
                    const vTop = window.visualViewport.offsetTop;
                    const overlays = [
                        diffInspectorOverlay,
                        modalOverlay,
                        chaptersModalOverlay,
                        onboardingOverlay,
                        criticForumModalOverlay,
                        settingsModalOverlay,
                        document.getElementById('ghModalOverlay')
                    ];
                    overlays.forEach(ov => {{
                        if (ov && (ov.classList.contains('visible') || (!ov.classList.contains('opacity-0') && !ov.classList.contains('pointer-events-none')))) {{
                            ov.style.height = vh + 'px';
                            ov.style.transform = 'translateY(' + vTop + 'px)';
                        }}
                    }});
                }}

                window.visualViewport.addEventListener('resize', syncActiveModalWithViewport);
                window.visualViewport.addEventListener('scroll', syncActiveModalWithViewport);
            }}

            // Smoothly keep text inputs above keyboard when focused
            [critiqueTextInput, suggestedRewriteInput].forEach(inp => {{
                if (!inp) return;
                inp.addEventListener('focus', function() {{
                    setTimeout(() => {{
                        inp.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                    }}, 250);
                }});
            }});

            if (modalCloseBtn) modalCloseBtn.onclick = closeModal;
            if (modalOverlay) {{
                modalOverlay.onclick = function(e) {{
                    if (e.target === modalOverlay) closeModal();
                }};
            }}

            if (modalPrevBlockBtn) modalPrevBlockBtn.onclick = function() {{
                if (activeBlockIndex > 0) openModalForBlock(activeBlockIndex - 1);
            }};

            if (modalNextBlockBtn) modalNextBlockBtn.onclick = function() {{
                if (activeBlockIndex < blocks.length - 1) openModalForBlock(activeBlockIndex + 1);
            }};

            document.addEventListener('keydown', function(e) {{
                if (e.key === 'Escape') {{
                    if (diffInspectorOverlay && diffInspectorOverlay.classList.contains('visible')) {{
                        closeDiffInspector();
                        return;
                    }}
                    if (settingsModalOverlay && settingsModalOverlay.classList.contains('visible')) hideSettingsModal();
                    if (criticForumModalOverlay && criticForumModalOverlay.classList.contains('visible')) hideCriticForumModal();
                    if (modalOverlay && modalOverlay.classList.contains('visible')) closeModal();
                    if (chaptersModalOverlay && chaptersModalOverlay.classList.contains('visible')) closeChaptersModal();
                    if (ghModalOverlay && !ghModalOverlay.classList.contains('opacity-0')) hideGhModal();
                    if (onboardingOverlay && !onboardingOverlay.classList.contains('opacity-0')) closeOnboardingModal();
                }} else if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {{
                    if (modalOverlay && modalOverlay.classList.contains('visible') && modalSaveBtn) {{
                        modalSaveBtn.click();
                    }}
                }}
            }});

            if (modalSaveBtn) modalSaveBtn.onclick = function() {{
                const block = blocks[activeBlockIndex];
                if (!block) return;
                const blockId = block.dataset.blockId;
                const comment = critiqueTextInput ? critiqueTextInput.value.trim() : "";
                const rewrite = suggestedRewriteInput ? suggestedRewriteInput.value.trim() : "";
                const p = block.querySelector('p');

                const originalSpeakerId = (block.dataset.speaker || "narrator").toLowerCase().trim();
                const originalSpeakerName = block.dataset.speakerName || "Narrator";
                const selectedSpeakerId = modalSpeakerSelect ? modalSpeakerSelect.value : originalSpeakerId;
                const isSpeakerChanged = (selectedSpeakerId !== originalSpeakerId);
                const chars = window.SESSION_CHARACTERS || {{}};
                const selectedSpeakerName = (chars[selectedSpeakerId] && chars[selectedSpeakerId].name) ? chars[selectedSpeakerId].name : selectedSpeakerId;

                if (!comment && !rewrite && !isSpeakerChanged) {{
                    alert("Please provide a critique note, suggested rewrite, or speaker re-attribution before saving.");
                    return;
                }}

                const mapData = (window.SOURCE_TRANSCRIPT_MAP && window.SOURCE_TRANSCRIPT_MAP[blockId]) || null;
                const activeProvLine = selectedSourceLine ? selectedSourceLine.line : (mapData && mapData.primaryLine ? mapData.primaryLine.line : null);
                const activeProvSpeaker = selectedSourceLine ? selectedSourceLine.speaker : (mapData && mapData.primaryLine ? mapData.primaryLine.speaker : null);

                critiques[blockId] = {{
                    blockId: blockId,
                    blockIndex: activeBlockIndex + 1,
                    speaker: originalSpeakerName,
                    speakerId: originalSpeakerId,
                    suggestedSpeaker: isSpeakerChanged ? selectedSpeakerId : null,
                    suggestedSpeakerName: isSpeakerChanged ? selectedSpeakerName : null,
                    speakerColor: block.dataset.speakerColor || "#94a3b8",
                    category: selectedCategory,
                    quote: p ? p.innerText : "",
                    comment: comment,
                    suggestedRewrite: rewrite,
                    sourceLine: activeProvLine,
                    sourceSpeaker: activeProvSpeaker,
                    updatedAt: new Date().toISOString()
                }};

                try {{
                    localStorage.setItem(STORAGE_KEY, JSON.stringify(critiques));
                }} catch(e) {{}}
                refreshMarkers();
                closeModal();
            }};

            if (modalDeleteBtn) modalDeleteBtn.onclick = function() {{
                const block = blocks[activeBlockIndex];
                if (!block) return;
                const blockId = block.dataset.blockId;
                delete critiques[blockId];
                try {{
                    localStorage.setItem(STORAGE_KEY, JSON.stringify(critiques));
                }} catch(e) {{}}
                refreshMarkers();
                closeModal();
            }};

            blocks.forEach((b, idx) => {{
                b.onclick = function() {{
                    if (document.body.classList.contains('mode-critique')) openDiffInspector(idx);
                }};
            }});

            // =========================================================
            // REVIEW & SUBMIT FEEDBACK MODAL (User-Friendly, No GH Jargon)
            // =========================================================
            const ghModalOverlay = document.createElement('div');
            ghModalOverlay.id = "ghModalOverlay";
            ghModalOverlay.className = "fixed inset-0 bg-slate-950/85 backdrop-blur-md z-50 flex items-center justify-center opacity-0 pointer-events-none p-3 sm:p-4 transition-opacity duration-200";
            ghModalOverlay.innerHTML = `
                <div class="bg-slate-900 border border-slate-700 rounded-2xl max-w-lg w-full p-4 sm:p-5 shadow-2xl flex flex-col max-h-[85vh] sm:max-h-[85dvh] space-y-3">
                    <div class="flex justify-between items-center border-b border-slate-800 pb-2.5 flex-shrink-0">
                        <div class="flex items-center gap-2">
                            <span class="text-xl">📝</span>
                            <div>
                                <h3 class="text-amber-400 font-bold text-sm sm:text-base">Review & Submit Feedback</h3>
                                <p class="text-[10px] text-slate-400 font-mono">Session {session_num} · <span id="feedbackModalNoteCount" class="text-emerald-400 font-semibold">0 notes</span> collected</p>
                            </div>
                        </div>
                        <button id="closeGhModal" type="button" class="text-slate-400 hover:text-slate-200 text-xl font-bold p-1 leading-none transition-colors">&times;</button>
                    </div>

                    <div class="flex-shrink-0">
                        <div class="flex items-center justify-between mb-1">
                            <label class="block text-xs font-semibold text-slate-300">Your Reviewer Name / Handle</label>
                            <button id="rerollReviewerNameBtn" type="button" class="text-[11px] text-amber-400 hover:text-amber-300 flex items-center gap-1 font-mono transition-colors font-medium" title="Roll a D&D pun adventurer handle">
                                🎲 Roll D&D Name
                            </button>
                        </div>
                        <div class="relative">
                            <input type="text" id="ghReviewerNameInput" class="w-full bg-slate-950 border border-slate-700 rounded-xl p-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-500 pr-10" placeholder="e.g. Artie Ficer, Drew Id, or your handle">
                            <button id="rerollReviewerNameInlineBtn" type="button" class="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-amber-400 p-1 text-sm transition-colors" title="Roll a D&D pun handle">
                                🎲
                            </button>
                        </div>
                    </div>

                    <!-- Scrollable List of Collected Feedback Items -->
                    <div class="flex-1 overflow-y-auto space-y-2 pr-1 min-h-[140px] max-h-[42vh] custom-scrollbar" id="feedbackNotesContainer">
                        <!-- Populated dynamically via renderFeedbackNotesList() -->
                    </div>

                    <div id="ghStatusMsg" class="hidden p-2.5 rounded-xl text-xs flex-shrink-0"></div>

                    <!-- Action Footer -->
                    <div class="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-800 flex-shrink-0">
                        <div class="flex items-center gap-1.5">
                            <button id="modalClearAllCritiquesBtn" type="button" class="px-3 py-2 bg-slate-800 hover:bg-rose-950/60 hover:text-rose-300 hover:border-rose-800 border border-slate-700 text-slate-400 font-semibold rounded-xl text-xs transition-colors" title="Clear all recorded feedback">
                                🗑️ Clear All
                            </button>
                            <button id="ghCopyJsonBtn" type="button" class="px-3 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 font-semibold rounded-xl text-xs transition-colors" title="Copy feedback summary">
                                📋 Copy Notes
                            </button>
                        </div>
                        <button id="ghSubmitPrBtn" type="button" class="flex-1 sm:flex-initial px-6 py-2.5 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 text-slate-950 font-bold rounded-xl text-xs transition-all shadow-lg shadow-amber-500/20 flex items-center justify-center gap-1.5 active:scale-98">
                            <span>🚀</span> <span>Submit Feedback</span>
                        </button>
                    </div>
                </div>
            `;
            document.body.appendChild(ghModalOverlay);

            const closeGhModal = document.getElementById('closeGhModal');
            const ghReviewerNameInput = document.getElementById('ghReviewerNameInput');
            const rerollReviewerNameBtn = document.getElementById('rerollReviewerNameBtn');
            const rerollReviewerNameInlineBtn = document.getElementById('rerollReviewerNameInlineBtn');
            const ghSubmitPrBtn = document.getElementById('ghSubmitPrBtn');
            const ghCopyJsonBtn = document.getElementById('ghCopyJsonBtn');
            const modalClearAllCritiquesBtn = document.getElementById('modalClearAllCritiquesBtn');
            const ghStatusMsg = document.getElementById('ghStatusMsg');

            // =========================================================
            // D&D PUN REVIEWER NAMES BANK & GENERATION
            // =========================================================
            const DND_PUN_NAMES = [
                "Artie Ficer", "Barbie Dian", "Claire Ick", "Drew Id", "Faye Terr",
                "Monk Montgomery", "Paula Din", "Ray N. Gerr", "Rowan Rogue", "Sorcha Sparks",
                "Warrick Lock", "Wizzy Ward", "Natasha Twenty", "Dexter Ity", "Connie Stitution",
                "Charis Mah", "Justin Initiative", "Eileen Advantage", "Disa Dvantage",
                "Penny Shortrest", "Lonnie Longrest", "Mithril Mike", "Kenku Kenny",
                "Tabitha Tarrasque", "Spellslot Sam", "Sneak Attack Stan", "Lootis Goblin",
                "Calvin Trip", "Missy Step", "Barb Arian", "Bardy McFly", "Prestidi Katie",
                "Otto Resilient", "Tasha Laughter", "Morden Kainen-Smith", "Bigby Handley",
                "Eldritch Blast-on", "Githy Hank", "Mimic Mike", "Dungeon Dan", "Master Mia"
            ];

            const DND_PUN_REPLACEMENTS = [
                "Vicious Mocker-y", "Feather Fallon", "Mage Handy", "Counterspell Craig",
                "Polymorph Polly", "Guidance Gail", "Bane Brandon", "Bless Brenda",
                "Eldritch Eli", "Flanklin Pierce", "Saving Throw Stan", "Hit Dice Harry",
                "Opportunity Oscar", "Critical Clive", "Passive Per-Septimus", "Shield Bash Sean",
                "Hexen Heather", "Smite Samantha", "Wildshape Wendy", "Arcane Archer Archie",
                "Animate Dead Andy", "Detect Magic Dave", "Sanctuary Sandy", "Haste Horace",
                "Beacon Hope-kins", "Zone Truth-er", "Death Ward Dale"
            ];

            function getRandomDndName() {{
                return DND_PUN_NAMES[Math.floor(Math.random() * DND_PUN_NAMES.length)];
            }}

            function getOrInitReviewerName() {{
                let saved = localStorage.getItem('dnd_scribe_reviewer_name');
                if (!saved || !saved.trim()) {{
                    saved = getRandomDndName();
                    localStorage.setItem('dnd_scribe_reviewer_name', saved);
                    localStorage.setItem('dnd_scribe_is_bank_name', 'true');
                }}
                return saved;
            }}

            function generateReplacementBankName(usedName) {{
                const pool = DND_PUN_REPLACEMENTS.concat(DND_PUN_NAMES);
                const available = pool.filter(n => n.toLowerCase() !== (usedName || '').toLowerCase());
                if (available.length > 0) {{
                    return available[Math.floor(Math.random() * available.length)];
                }}
                return "Nat Twenty-Two";
            }}

            function rollNewReviewerName() {{
                const newName = getRandomDndName();
                if (ghReviewerNameInput) {{
                    ghReviewerNameInput.value = newName;
                    localStorage.setItem('dnd_scribe_reviewer_name', newName);
                    localStorage.setItem('dnd_scribe_is_bank_name', 'true');
                    ghReviewerNameInput.classList.add('ring-2', 'ring-amber-400');
                    setTimeout(() => ghReviewerNameInput.classList.remove('ring-2', 'ring-amber-400'), 400);
                }}
            }}

            if (ghReviewerNameInput) {{
                ghReviewerNameInput.value = getOrInitReviewerName();
                ghReviewerNameInput.addEventListener('input', function() {{
                    const val = this.value.trim();
                    localStorage.setItem('dnd_scribe_reviewer_name', val);
                    const isPun = DND_PUN_NAMES.some(n => n.toLowerCase() === val.toLowerCase());
                    localStorage.setItem('dnd_scribe_is_bank_name', isPun ? 'true' : 'false');
                }});
            }}

            if (rerollReviewerNameBtn) rerollReviewerNameBtn.onclick = rollNewReviewerName;
            if (rerollReviewerNameInlineBtn) rerollReviewerNameInlineBtn.onclick = rollNewReviewerName;

            function renderFeedbackNotesList() {{
                const container = document.getElementById('feedbackNotesContainer');
                const noteCountDisplay = document.getElementById('feedbackModalNoteCount');
                if (!container) return;

                const items = Object.values(critiques);
                if (noteCountDisplay) noteCountDisplay.textContent = items.length + " note" + (items.length === 1 ? "" : "s");

                if (items.length === 0) {{
                    container.innerHTML = `
                        <div class="h-32 flex flex-col items-center justify-center text-center p-4 border border-dashed border-slate-800 rounded-xl bg-slate-950/40 text-slate-500 space-y-1">
                            <span class="text-2xl">💬</span>
                            <p class="text-xs font-medium text-slate-400">No feedback notes recorded yet.</p>
                            <p class="text-[10px] text-slate-600">Click or tap any passage while in Critique mode to leave review directives.</p>
                        </div>
                    `;
                    if (ghSubmitPrBtn) {{
                        ghSubmitPrBtn.disabled = true;
                        ghSubmitPrBtn.style.opacity = "0.5";
                        ghSubmitPrBtn.style.pointerEvents = "none";
                    }}
                    return;
                }}

                if (ghSubmitPrBtn) {{
                    ghSubmitPrBtn.disabled = false;
                    ghSubmitPrBtn.style.opacity = "1";
                    ghSubmitPrBtn.style.pointerEvents = "auto";
                }}

                container.innerHTML = items.map((c, idx) => {{
                    const spColor = c.speakerColor || '#94a3b8';
                    const isNarrator = (!c.speaker || c.speaker.toLowerCase() === 'narrator');
                    const cardStyle = isNarrator
                        ? 'border-left: 3.5px solid #475569; background: rgba(15, 23, 42, 0.7);'
                        : 'border-left: 3.5px solid ' + spColor + '; background: linear-gradient(90deg, ' + spColor + '16 0%, rgba(15, 23, 42, 0.85) 100%);';

                    const rewriteHtml = c.suggestedRewrite ? `
                        <div class="mt-1.5 p-1.5 rounded-lg bg-slate-900/90 border border-slate-800 text-[11px] text-cyan-300 font-mono">
                            <strong class="text-[9px] uppercase tracking-wider text-slate-500 block">Suggested Rewrite:</strong>
                            ` + c.suggestedRewrite + `
                        </div>
                    ` : '';

                    const speakerChangeHtml = (c.suggestedSpeaker && c.suggestedSpeaker !== c.speakerId) ? `
                        <div class="mt-1 p-1.5 rounded-lg bg-amber-950/40 border border-amber-800/60 text-[11px] text-amber-300 flex items-center gap-1.5 font-mono">
                            <span>🎙️</span>
                            <span class="font-bold">Re-attribute Voice:</span>
                            <span class="line-through text-slate-400">` + (c.speaker || 'Narrator') + `</span>
                            <span>➔</span>
                            <span class="font-bold text-amber-200">` + (c.suggestedSpeakerName || c.suggestedSpeaker) + `</span>
                        </div>
                    ` : '';

                    return `
                        <div class="p-3 rounded-r-xl rounded-l-md border-y border-r border-slate-800 space-y-1.5 relative group shadow-sm transition-all" style="` + cardStyle + `">
                            <div class="flex items-center justify-between gap-2">
                                <div class="flex items-center gap-1.5 min-w-0">
                                    <span class="w-2 h-2 rounded-full flex-shrink-0" style="background-color: ` + spColor + `"></span>
                                    <span class="text-[10px] font-mono font-bold uppercase truncate" style="color: ` + spColor + `">#` + (c.blockIndex || (idx + 1)) + ` ` + (c.speaker || 'Narrator') + `</span>
                                    ` + (c.sourceLine ? `<span class="text-[9px] px-1.5 py-0.2 rounded bg-amber-950/80 text-amber-300 border border-amber-700/60 font-mono font-semibold" title="Tabletop Source Line">L` + c.sourceLine + `</span>` : '') + `
                                    <span class="text-[9px] px-1.5 py-0.2 rounded bg-slate-950/80 text-slate-300 border border-slate-700/60 font-mono uppercase font-semibold">` + (c.category || 'General') + `</span>
                                </div>
                                <button type="button" class="text-slate-500 hover:text-rose-400 text-xs p-1 transition-colors" title="Delete this note" onclick="window.deleteCritiqueItem('` + c.blockId + `')">
                                    🗑️
                                </button>
                            </div>
                            ` + (c.quote ? `<p class="text-[11px] text-slate-300 italic line-clamp-2 pl-0.5">"` + c.quote + `"</p>` : '') + `
                            ` + speakerChangeHtml + `
                            ` + (c.comment ? `<p class="text-xs text-slate-100 font-medium pl-0.5">` + c.comment + `</p>` : '') + `
                            ` + rewriteHtml + `
                        </div>
                    `;
                }}).join('');
            }}

            window.deleteCritiqueItem = function(blockId) {{
                if (critiques[blockId]) {{
                    delete critiques[blockId];
                    try {{ localStorage.setItem(STORAGE_KEY, JSON.stringify(critiques)); }} catch(e) {{}}
                    refreshMarkers();
                    renderFeedbackNotesList();
                    const remainingCount = Object.keys(critiques).length;
                    if (exportBadgeCount) exportBadgeCount.textContent = remainingCount;
                }}
            }};

            if (modalClearAllCritiquesBtn) {{
                modalClearAllCritiquesBtn.onclick = function() {{
                    if (confirm("Are you sure you want to clear all feedback notes for this session?")) {{
                        critiques = {{}};
                        try {{ localStorage.removeItem(STORAGE_KEY); }} catch(e) {{}}
                        refreshMarkers();
                        renderFeedbackNotesList();
                        if (exportBadgeCount) exportBadgeCount.textContent = "0";
                    }}
                }};
            }}

            function showGhModal() {{
                renderFeedbackNotesList();
                if (ghStatusMsg) ghStatusMsg.className = "hidden";
                if (ghModalOverlay) {{
                    ghModalOverlay.classList.remove('opacity-0', 'pointer-events-none');
                    if (window.visualViewport) {{
                        ghModalOverlay.style.height = window.visualViewport.height + 'px';
                        ghModalOverlay.style.transform = 'translateY(' + window.visualViewport.offsetTop + 'px)';
                    }}
                    setBodyScrollLock(true);
                }}
            }}

            function hideGhModal() {{
                if (ghModalOverlay) {{
                    ghModalOverlay.classList.add('opacity-0', 'pointer-events-none');
                    ghModalOverlay.style.height = '';
                    ghModalOverlay.style.transform = '';
                    setBodyScrollLock(false);
                }}
            }}

            if (closeGhModal) closeGhModal.onclick = hideGhModal;
            if (ghModalOverlay) {{
                ghModalOverlay.onclick = function(e) {{
                    if (e.target === ghModalOverlay) hideGhModal();
                }};
            }}

            if (ghCopyJsonBtn) {{
                ghCopyJsonBtn.onclick = function() {{
                    const count = Object.keys(critiques).length;
                    const reviewer = (ghReviewerNameInput && ghReviewerNameInput.value.trim()) ? ghReviewerNameInput.value.trim() : getOrInitReviewerName();
                    const isBankName = DND_PUN_NAMES.some(n => n.toLowerCase() === reviewer.toLowerCase()) || (localStorage.getItem('dnd_scribe_is_bank_name') === 'true');
                    const replacementName = isBankName ? generateReplacementBankName(reviewer) : null;
                    const exportPayload = {{
                        campaign: CAMPAIGN_ID,
                        chapter: CHAPTER_ID,
                        title: "Uneraseable - {session_title}",
                        reviewer: reviewer,
                        reviewerMeta: {{
                            handle: reviewer,
                            isBankPunName: isBankName,
                            suggestedBankReplacement: replacementName
                        }},
                        exportedAt: new Date().toISOString(),
                        totalCritiques: count,
                        critiques: Object.values(critiques)
                    }};
                    navigator.clipboard.writeText(JSON.stringify(exportPayload, null, 2)).then(() => {{
                        alert("✨ Copied " + count + " feedback note(s) to clipboard!");
                    }});
                }};
            }}

            // =========================================================
            // GITHUB APP AUTOMATED AUTHENTICATION ENGINE
            // =========================================================
            const BOT_APP_ID = "{BOT_APP_ID}";
            const BOT_INSTALLATION_ID = "{BOT_INSTALLATION_ID}";
            const BOT_PKCS8_B64 = "{BOT_PKCS8_B64}";

            async function getInstallationAccessToken() {{
                const manualToken = localStorage.getItem('dnd_scribe_gh_token');
                if (manualToken) return manualToken;

                if (!BOT_PKCS8_B64 || !BOT_APP_ID || !BOT_INSTALLATION_ID) {{
                    throw new Error("Bot authentication credentials missing.");
                }}

                function base64UrlEncode(str) {{
                    return btoa(str).replace(/\\+/g, '-').replace(/\\//g, '_').replace(/=+$/, '');
                }}

                function base64UrlEncodeBuffer(buf) {{
                    const bytes = new Uint8Array(buf);
                    let binary = '';
                    for (let i = 0; i < bytes.byteLength; i++) {{
                        binary += String.fromCharCode(bytes[i]);
                    }}
                    return btoa(binary).replace(/\\+/g, '-').replace(/\\//g, '_').replace(/=+$/, '');
                }}

                function str2ab(b64) {{
                    const binary = atob(b64);
                    const bytes = new Uint8Array(binary.length);
                    for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
                    return bytes.buffer;
                }}

                const key = await crypto.subtle.importKey(
                    "pkcs8",
                    str2ab(BOT_PKCS8_B64),
                    {{ name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" }},
                    false,
                    ["sign"]
                );

                const now = Math.floor(Date.now() / 1000);
                const header = base64UrlEncode(JSON.stringify({{ alg: "RS256", typ: "JWT" }}));
                const payload = base64UrlEncode(JSON.stringify({{
                    iat: now - 60,
                    exp: now + 500,
                    iss: BOT_APP_ID
                }}));

                const dataToSign = new TextEncoder().encode(header + "." + payload);
                const signature = await crypto.subtle.sign("RSASSA-PKCS1-v1_5", key, dataToSign);
                const jwt = header + "." + payload + "." + base64UrlEncodeBuffer(signature);

                const res = await fetch("https://api.github.com/app/installations/" + BOT_INSTALLATION_ID + "/access_tokens", {{
                    method: "POST",
                    headers: {{
                        "Authorization": "Bearer " + jwt,
                        "Accept": "application/vnd.github+json",
                        "User-Agent": "dnd-scribe-bot"
                    }}
                }});

                if (!res.ok) {{
                    const errBody = await res.text();
                    throw new Error("Failed to authenticate bot (" + res.status + "): " + errBody);
                }}

                const tokenData = await res.json();
                return tokenData.token;
            }}

            if (ghSubmitPrBtn) {{
                ghSubmitPrBtn.onclick = async function() {{
                    const reviewer = (ghReviewerNameInput && ghReviewerNameInput.value.trim()) ? ghReviewerNameInput.value.trim() : getOrInitReviewerName();
                    const count = Object.keys(critiques).length;
                    if (count === 0) {{
                        alert("No feedback notes to submit.");
                        return;
                    }}

                    localStorage.setItem('dnd_scribe_reviewer_name', reviewer);

                    if (ghStatusMsg) {{
                        ghStatusMsg.className = "p-2.5 rounded-xl text-xs bg-sky-950/60 border border-sky-800 text-sky-300 block";
                        ghStatusMsg.innerHTML = "⏳ <strong>Submitting feedback...</strong> Authenticating and dispatching review notes to the scribe pipeline.";
                    }}
                    ghSubmitPrBtn.disabled = true;

                    const isBankName = DND_PUN_NAMES.some(n => n.toLowerCase() === reviewer.toLowerCase()) || (localStorage.getItem('dnd_scribe_is_bank_name') === 'true');
                    const replacementName = isBankName ? generateReplacementBankName(reviewer) : null;

                    const REPO = "ldstrebel/dnd-scribe";
                    const BASE_BRANCH = "uneraseable";
                    const safeName = reviewer.toLowerCase().replace(/[^a-z0-9]/g, '-');
                    const timestamp = Date.now().toString().slice(-6);
                    const NEW_BRANCH = "critique/" + CAMPAIGN_ID + "-" + CHAPTER_ID + "-" + safeName + "-" + timestamp;

                    const exportPayload = {{
                        campaign: CAMPAIGN_ID,
                        chapter: CHAPTER_ID,
                        title: "Uneraseable - {session_title}",
                        reviewer: reviewer,
                        reviewerMeta: {{
                            handle: reviewer,
                            isBankPunName: isBankName,
                            suggestedBankReplacement: replacementName
                        }},
                        exportedAt: new Date().toISOString(),
                        totalCritiques: count,
                        critiques: Object.values(critiques)
                    }};

                    const markdownRows = Object.values(critiques).map(c => {{
                        const spkCol = (c.suggestedSpeaker && c.suggestedSpeaker !== c.speakerId)
                            ? "**" + c.speaker + "** ➔ 🎙️ **" + (c.suggestedSpeakerName || c.suggestedSpeaker) + "**"
                            : "**" + c.speaker + "**";
                        return "| `" + c.blockId + "` | " + spkCol + " | " + (c.sourceLine ? ("`L" + c.sourceLine + "`" + (c.sourceSpeaker ? " (" + c.sourceSpeaker + ")" : "")) : "-") + " | `" + c.category + "` | " + (c.comment || '').replace(/\\|/g, '\\\\|') + " | " + (c.suggestedRewrite ? c.suggestedRewrite.replace(/\\|/g, '\\\\|') : '-') + " |";
                    }}).join('\\n');

                    let reviewerSection = "**Reviewer:** `" + reviewer + "`";
                    if (isBankName && replacementName) {{
                        reviewerSection += " *(🎲 D&D Pun Handle)*\\n**Next Pool Replacement Suggestion:** `" + replacementName + "` 🎲";
                    }}

                    const prBody = "## 📝 Story Feedback: " + exportPayload.title + "\\n" + reviewerSection + "\\n**Total Notes:** " + count + "\\n\\n### 📋 Feedback Items Table\\n| Block ID | Speaker | Source Line | Category | Critique / Directive | Suggested Rewrite |\\n|---|---|---|---|---|---|\\n" + markdownRows + "\\n\\n<details>\\n<summary><b>📦 Raw JSON Payload (for Agent Ingestion)</b></summary>\\n\\n```json\\n" + JSON.stringify(exportPayload, null, 2) + "\\n```\\n</details>";

                    try {{
                        const token = await getInstallationAccessToken();

                        const headers = {{
                            "Authorization": "Bearer " + token,
                            "Accept": "application/vnd.github+json",
                            "Content-Type": "application/json"
                        }};

                        let baseRefRes = await fetch("https://api.github.com/repos/" + REPO + "/git/ref/heads/" + BASE_BRANCH, {{ headers }});
                        if (!baseRefRes.ok) baseRefRes = await fetch("https://api.github.com/repos/" + REPO + "/git/ref/heads/main", {{ headers }});
                        if (!baseRefRes.ok) throw new Error("Could not connect to scribe repository: " + baseRefRes.statusText);
                        const baseSha = (await baseRefRes.json()).object.sha;

                        const createBranchRes = await fetch("https://api.github.com/repos/" + REPO + "/git/refs", {{
                            method: "POST",
                            headers: headers,
                            body: JSON.stringify({{ ref: "refs/heads/" + NEW_BRANCH, sha: baseSha }})
                        }});
                        if (!createBranchRes.ok) throw new Error("Failed to create review branch: " + (await createBranchRes.text()));

                        const filePath = "sessions/data/critiques/" + CAMPAIGN_ID + "-" + CHAPTER_ID + "-" + safeName + "-" + timestamp + ".json";
                        const contentBase64 = btoa(unescape(encodeURIComponent(JSON.stringify(exportPayload, null, 2))));
                        const commitRes = await fetch("https://api.github.com/repos/" + REPO + "/contents/" + filePath, {{
                            method: "PUT",
                            headers: headers,
                            body: JSON.stringify({{ message: "critique: " + reviewer + " review for " + CAMPAIGN_ID + " " + CHAPTER_ID, content: contentBase64, branch: NEW_BRANCH }})
                        }});
                        if (!commitRes.ok) throw new Error("Failed to upload feedback payload: " + (await commitRes.text()));

                        const prRes = await fetch("https://api.github.com/repos/" + REPO + "/pulls", {{
                            method: "POST",
                            headers: headers,
                            body: JSON.stringify({{ title: "📝 Review: " + CAMPAIGN_ID.toUpperCase() + " " + CHAPTER_ID.toUpperCase() + " by " + reviewer, head: NEW_BRANCH, base: BASE_BRANCH, body: prBody }})
                        }});
                        if (!prRes.ok) throw new Error("Failed to register feedback: " + (await prRes.text()));
                        const prData = await prRes.json();

                        if (ghStatusMsg) {{
                            ghStatusMsg.className = "p-2.5 rounded-xl text-xs bg-emerald-950/70 border border-emerald-700 text-emerald-300 block";
                            let successHtml = '🎉 <strong>Feedback Submitted!</strong><br>Thank you, ' + reviewer + '! Your notes have been submitted to the scribe pipeline.';
                            if (isBankName && replacementName) {{
                                successHtml += '<br><span class="text-[11px] text-amber-300 font-mono mt-1 block">🎲 Bank Refresh: Generated <strong>' + replacementName + '</strong> for next adventurer.</span>';
                            }}
                            ghStatusMsg.innerHTML = successHtml;
                        }}

                        // Clear cache and refresh markers upon submission
                        critiques = {{}};
                        try {{ localStorage.removeItem(STORAGE_KEY); }} catch(e) {{}}
                        refreshMarkers();
                        renderFeedbackNotesList();
                        if (exportBadgeCount) exportBadgeCount.textContent = "0";

                        setTimeout(() => {{
                            hideGhModal();
                        }}, 2500);
                    }} catch (err) {{
                        if (ghStatusMsg) {{
                            ghStatusMsg.className = "p-2.5 rounded-xl text-xs bg-rose-950/70 border border-rose-700 text-rose-300 block";
                            ghStatusMsg.textContent = "❌ Submission error: " + err.message;
                        }}
                    }} finally {{
                        ghSubmitPrBtn.disabled = false;
                    }}
                }};
            }}

            // =========================================================
            // CRITIC & EDITORIAL FORUM CONTROLLER
            // =========================================================
            function showCriticForumModal() {{
                if (criticForumModalOverlay) {{
                    criticForumModalOverlay.classList.remove('opacity-0', 'pointer-events-none');
                    criticForumModalOverlay.classList.add('visible');
                    if (window.visualViewport) {{
                        criticForumModalOverlay.style.height = window.visualViewport.height + 'px';
                        criticForumModalOverlay.style.transform = 'translateY(' + window.visualViewport.offsetTop + 'px)';
                    }}
                    setBodyScrollLock(true);
                }}
            }}

            function hideCriticForumModal() {{
                if (criticForumModalOverlay) {{
                    criticForumModalOverlay.classList.add('opacity-0', 'pointer-events-none');
                    criticForumModalOverlay.classList.remove('visible');
                    criticForumModalOverlay.style.height = '';
                    criticForumModalOverlay.style.transform = '';
                    setBodyScrollLock(false);
                }}
            }}

            if (endSessionCriticCard) endSessionCriticCard.onclick = showCriticForumModal;
            if (footerCriticForumBtn) footerCriticForumBtn.onclick = showCriticForumModal;
            if (closeCriticForumBtn) closeCriticForumBtn.onclick = hideCriticForumModal;
            if (closeCriticForumFooterBtn) closeCriticForumFooterBtn.onclick = hideCriticForumModal;
            if (criticForumModalOverlay) {{
                criticForumModalOverlay.onclick = function(e) {{
                    if (e.target === criticForumModalOverlay) hideCriticForumModal();
                }};
            }}

            if (submitForumCommentBtn && forumCommentInput) {{
                submitForumCommentBtn.onclick = function() {{
                    const text = forumCommentInput.value.trim();
                    if (!text) {{
                        alert("Please type your thoughts or feedback before submitting.");
                        return;
                    }}
                    const reviewer = getOrInitReviewerName();
                    const blockId = "critic_feedback_s{session_num}_" + Date.now().toString().slice(-4);
                    critiques[blockId] = {{
                        blockId: blockId,
                        blockIndex: 1,
                        speaker: "Story Reaction (" + reviewer + ")",
                        speakerColor: "#f43f5e",
                        category: "general",
                        quote: "Session {session_num} Narrative Spectrum Reaction",
                        comment: text,
                        suggestedRewrite: "",
                        updatedAt: new Date().toISOString()
                    }};
                    try {{ localStorage.setItem(STORAGE_KEY, JSON.stringify(critiques)); }} catch(e) {{}}
                    refreshMarkers();
                    renderFeedbackNotesList();
                    if (exportBadgeCount) exportBadgeCount.textContent = Object.keys(critiques).length;

                    forumCommentInput.value = "";
                    if (forumStatusMsg) {{
                        forumStatusMsg.className = "p-2.5 rounded-xl text-xs bg-emerald-950/70 border border-emerald-700 text-emerald-300 block";
                        forumStatusMsg.innerHTML = "🎉 <strong>Thank you! Your feedback has been recorded.</strong><br>Opening feedback review drawer...";
                    }}
                    setTimeout(() => {{
                        hideCriticForumModal();
                        showGhModal();
                    }}, 1000);
                }};
            }}

            if (footerExportBtn) footerExportBtn.onclick = showGhModal;
            if (clearCritiquesBtn) {{
                clearCritiquesBtn.onclick = function() {{
                    if (confirm("Are you sure you want to clear all review notes for this session?")) {{
                        critiques = {{}};
                        try {{ localStorage.removeItem(STORAGE_KEY); }} catch(e) {{}}
                        refreshMarkers();
                        if (exportBadgeCount) exportBadgeCount.textContent = "0";
                    }}
                }};
            }}

            // =========================================================
            // READING SETTINGS & THEME CONTROLLER
            // =========================================================
            let currentFontScale = 1.0;
            const FONT_SCALES = [0.8, 0.9, 1.0, 1.15, 1.3, 1.5];

            function showSettingsModal() {{
                if (settingsModalOverlay) {{
                    settingsModalOverlay.classList.remove('opacity-0', 'pointer-events-none');
                    settingsModalOverlay.classList.add('visible');
                    if (window.visualViewport) {{
                        settingsModalOverlay.style.height = window.visualViewport.height + 'px';
                        settingsModalOverlay.style.transform = 'translateY(' + window.visualViewport.offsetTop + 'px)';
                    }}
                    setBodyScrollLock(true);
                }}
            }}

            function hideSettingsModal() {{
                if (settingsModalOverlay) {{
                    settingsModalOverlay.classList.add('opacity-0', 'pointer-events-none');
                    settingsModalOverlay.classList.remove('visible');
                    settingsModalOverlay.style.height = '';
                    settingsModalOverlay.style.transform = '';
                    setBodyScrollLock(false);
                }}
            }}

            function updateFontScale(scale) {{
                currentFontScale = Math.min(1.6, Math.max(0.75, Math.round(scale * 100) / 100));
                document.documentElement.style.setProperty('--story-font-scale', currentFontScale);
                if (fontSizeDisplay) {{
                    fontSizeDisplay.textContent = Math.round(currentFontScale * 100) + '%';
                }}
                if (settingsFontPreview) {{
                    settingsFontPreview.style.fontSize = (1.0625 * currentFontScale) + 'rem';
                }}
                try {{
                    localStorage.setItem('dnd_reader_font_scale', currentFontScale.toString());
                }} catch(e) {{}}
            }}

            function setReaderTheme(theme) {{
                document.documentElement.classList.remove('theme-dark', 'theme-light', 'theme-sepia');
                document.documentElement.classList.add('theme-' + theme);

                const activeThemeClass = "p-2.5 rounded-xl border-2 border-amber-400 bg-slate-950 text-slate-100 flex flex-col items-center gap-1 transition-all shadow-sm";
                const lightActiveThemeClass = "p-2.5 rounded-xl border-2 border-amber-500 bg-slate-100 text-slate-900 flex flex-col items-center gap-1 transition-all shadow-sm";
                const sepiaActiveThemeClass = "p-2.5 rounded-xl border-2 border-amber-600 bg-[#f6f0e2] text-[#2c221e] flex flex-col items-center gap-1 transition-all shadow-sm";

                const darkInactiveClass = "p-2.5 rounded-xl border border-slate-800 hover:border-slate-600 bg-slate-950 text-slate-400 flex flex-col items-center gap-1 transition-all";
                const lightInactiveClass = "p-2.5 rounded-xl border border-slate-700 hover:border-slate-500 bg-slate-100 text-slate-900 flex flex-col items-center gap-1 transition-all";
                const sepiaInactiveClass = "p-2.5 rounded-xl border border-slate-700 hover:border-slate-500 bg-[#f6f0e2] text-[#2c221e] flex flex-col items-center gap-1 transition-all";

                if (themeDarkBtn) themeDarkBtn.className = (theme === 'dark') ? activeThemeClass : darkInactiveClass;
                if (themeLightBtn) themeLightBtn.className = (theme === 'light') ? lightActiveThemeClass : lightInactiveClass;
                if (themeSepiaBtn) themeSepiaBtn.className = (theme === 'sepia') ? sepiaActiveThemeClass : sepiaInactiveClass;

                try {{
                    localStorage.setItem('dnd_reader_theme', theme);
                }} catch(e) {{}}
            }}

            function setReaderFontFamily(family) {{
                let fontVal = "'Outfit', sans-serif";
                if (family === 'serif') fontVal = "'Cinzel', Georgia, serif";
                if (family === 'mono') fontVal = "'JetBrains Mono', monospace";

                document.documentElement.style.setProperty('--story-font-family', fontVal);

                const activeFontClass = "p-2 rounded-xl border-2 border-amber-400 bg-slate-900 text-slate-100 text-center transition-all shadow-sm";
                const inactiveFontClass = "p-2 rounded-xl border border-slate-800 bg-slate-900/60 text-slate-400 text-center transition-all hover:border-slate-700";

                if (fontSansBtn) fontSansBtn.className = (family === 'sans') ? (activeFontClass + " font-sans") : (inactiveFontClass + " font-sans");
                if (fontSerifBtn) fontSerifBtn.className = (family === 'serif') ? (activeFontClass + " font-serif") : (inactiveFontClass + " font-serif");
                if (fontMonoBtn) fontMonoBtn.className = (family === 'mono') ? (activeFontClass + " font-mono") : (inactiveFontClass + " font-mono");

                try {{
                    localStorage.setItem('dnd_reader_font_family', family);
                }} catch(e) {{}}
            }}

            // Bind Settings Events
            if (toggleSettingsBtn) toggleSettingsBtn.onclick = showSettingsModal;
            if (closeSettingsModalBtn) closeSettingsModalBtn.onclick = hideSettingsModal;
            if (closeSettingsFooterBtn) closeSettingsFooterBtn.onclick = hideSettingsModal;
            if (settingsModalOverlay) {{
                settingsModalOverlay.onclick = function(e) {{
                    if (e.target === settingsModalOverlay) hideSettingsModal();
                }};
            }}

            if (fontSizeMinusBtn) {{
                fontSizeMinusBtn.onclick = function() {{
                    const idx = FONT_SCALES.findIndex(s => s >= currentFontScale);
                    const prev = (idx > 0) ? FONT_SCALES[idx - 1] : (currentFontScale - 0.1);
                    updateFontScale(prev);
                }};
            }}
            if (fontSizePlusBtn) {{
                fontSizePlusBtn.onclick = function() {{
                    const next = FONT_SCALES.find(s => s > currentFontScale) || (currentFontScale + 0.1);
                    updateFontScale(next);
                }};
            }}
            if (fontSizeResetBtn) {{
                fontSizeResetBtn.onclick = function() {{
                    updateFontScale(1.0);
                }};
            }}

            if (themeDarkBtn) themeDarkBtn.onclick = () => setReaderTheme('dark');
            if (themeLightBtn) themeLightBtn.onclick = () => setReaderTheme('light');
            if (themeSepiaBtn) themeSepiaBtn.onclick = () => setReaderTheme('sepia');

            if (fontSansBtn) fontSansBtn.onclick = () => setReaderFontFamily('sans');
            if (fontSerifBtn) fontSerifBtn.onclick = () => setReaderFontFamily('serif');
            if (fontMonoBtn) fontMonoBtn.onclick = () => setReaderFontFamily('mono');

            // Initialize saved preferences
            try {{
                const savedScale = parseFloat(localStorage.getItem('dnd_reader_font_scale') || '1');
                if (savedScale && !isNaN(savedScale)) updateFontScale(savedScale);

                const savedTheme = localStorage.getItem('dnd_reader_theme') || 'dark';
                setReaderTheme(savedTheme);

                const savedFont = localStorage.getItem('dnd_reader_font_family') || 'sans';
                setReaderFontFamily(savedFont);
            }} catch(e) {{}}

            // =========================================================
            // READERSHIP TELEMETRY & COMPLETION TRACKER (V2 Clean)
            // =========================================================
            const TELEMETRY_LOCAL_KEY = "dnd_reader_v2_" + CAMPAIGN_ID + "_" + CHAPTER_ID;
            const TELEMETRY_GLOBAL_KEY = "dnd_global_v2_" + CAMPAIGN_ID + "_" + CHAPTER_ID;
            const TELEMETRY_SESSION_KEY = "dnd_session_v2_" + CAMPAIGN_ID + "_" + CHAPTER_ID;

            // Load local reader state
            let localTelemetry = {{ hasOpened: false, completed: false, maxDepth: 0 }};
            try {{
                localTelemetry = JSON.parse(localStorage.getItem(TELEMETRY_LOCAL_KEY) || "null") || localTelemetry;
            }} catch(e) {{}}

            // Load global aggregate stats (clean initial values)
            let globalTelemetry = {{ readers: 0, opens: 0, completions: 0, incompleteCount: 0, incompleteDepthSum: 0 }};
            try {{
                const storedGlobal = JSON.parse(localStorage.getItem(TELEMETRY_GLOBAL_KEY) || "null");
                if (storedGlobal) {{
                    globalTelemetry.readers = storedGlobal.readers || 0;
                    globalTelemetry.opens = storedGlobal.opens || 0;
                    globalTelemetry.completions = storedGlobal.completions || 0;
                    globalTelemetry.incompleteCount = storedGlobal.incompleteCount || 0;
                    globalTelemetry.incompleteDepthSum = storedGlobal.incompleteDepthSum || 0;
                }}
            }} catch(e) {{}}

            // 1. First-time unique reader registration with permanent reader number
            if (!localTelemetry.hasOpened) {{
                localTelemetry.hasOpened = true;
                localTelemetry.maxDepth = 0;
                globalTelemetry.readers += 1;
                globalTelemetry.incompleteCount += 1;
                localTelemetry.readerNumber = globalTelemetry.readers;
            }} else if (!localTelemetry.readerNumber) {{
                localTelemetry.readerNumber = Math.max(1, globalTelemetry.readers || 1);
            }}

            // 2. Session-scoped open counting (prevents reload inflation)
            try {{
                if (!sessionStorage.getItem(TELEMETRY_SESSION_KEY)) {{
                    sessionStorage.setItem(TELEMETRY_SESSION_KEY, 'true');
                    globalTelemetry.opens += 1;
                }}
            }} catch(e) {{
                if (!localTelemetry.hasOpened) globalTelemetry.opens += 1;
            }}

            // Persist initial global & local state
            function saveTelemetryState() {{
                try {{
                    localStorage.setItem(TELEMETRY_LOCAL_KEY, JSON.stringify(localTelemetry));
                    localStorage.setItem(TELEMETRY_GLOBAL_KEY, JSON.stringify(globalTelemetry));
                }} catch(e) {{}}
            }}
            saveTelemetryState();

            const MOTIVATIONAL_BLURBS = {{
                easterEggs: {{
                    1: {{
                        initial: "👑 <strong>Pioneer Alert!</strong> You're Reader #1 — set the pace and forge the benchmark for everyone who follows!",
                        inProgress: "👑 <strong>Trailblazer in Action:</strong> As Reader #1 ({{depth}}% depth), you are charting uncharted waters for Session {{s}}!",
                        pastDropoff: "👑 <strong>Pioneer Momentum:</strong> Reader #1 is blazing past the ~{{dropoff}}% mark! Set the inaugural completion record.",
                        completed: "👑 <strong>The Founding Finisher!</strong> You are Reader #1 and the very first traveler in history to conquer Session {{s}}!"
                    }},
                    2: {{
                        initial: "🥈 <strong>Vanguard #2:</strong> You're the 2nd reader to discover Session {{s}}. The ink is fresh—can you catch the pioneer?",
                        inProgress: "🥈 <strong>Hot on the Trail:</strong> Reader #2 is pushing through at {{depth}}% depth. Keep up the pace!",
                        pastDropoff: "🥈 <strong>Second Wave:</strong> Past the ~{{dropoff}}% drop-off! You're racing toward the top 2 finisher spots.",
                        completed: "🥈 <strong>Silver Finisher!</strong> You are the 2nd traveler in history to complete Session {{s}}!"
                    }},
                    3: {{
                        initial: "🥉 <strong>Adventuring Party Formed!</strong> You're Reader #3. Three is a party in D&D—venture into the deep weave!",
                        inProgress: "🥉 <strong>Party of Three:</strong> Reader #3 is at {{depth}}% depth. The party's campaign is in full swing.",
                        pastDropoff: "🥉 <strong>Party Vanguard:</strong> Surpassed the ~{{dropoff}}% mark! Finish the session to immortalize the founding trio.",
                        completed: "🥉 <strong>Founding Trio Complete!</strong> Reader #3 crosses the finish line. The adventuring party stands victorious!"
                    }},
                    7: {{
                        initial: "🎲 <strong>Lucky 7!</strong> Fortune smiles upon Reader #7. Roll high and start exploring!",
                        inProgress: "🎲 <strong>Lucky Streak:</strong> Reader #7 is rolling through at {{depth}}% depth!",
                        pastDropoff: "🎲 <strong>Critical Momentum:</strong> Reader #7 breaks past the ~{{dropoff}}% mark. Lady Luck is on your side!",
                        completed: "🎲 <strong>Jackpot!</strong> Reader #7 completes the adventure with pure style."
                    }},
                    13: {{
                        initial: "🔮 <strong>Reader #13:</strong> An ominous thread in the Weave... Defy superstition and conquer Session {{s}}!",
                        inProgress: "🔮 <strong>Defying the Curse:</strong> Reader #13 is slicing through at {{depth}}% depth!",
                        pastDropoff: "🔮 <strong>Superstition Broken:</strong> Reader #13 surges past ~{{dropoff}}%! The finish line is yours.",
                        completed: "🔮 <strong>Fate Rewritten!</strong> Reader #13 conquers Session {{s}} and rewrites destiny."
                    }},
                    20: {{
                        initial: "🌟 <strong>NATURAL 20!</strong> You rolled a Nat 20 just by showing up as Reader #20. Critical reading momentum!",
                        inProgress: "🌟 <strong>Natural 20 Energy:</strong> Cruising at {{depth}}% with max advantage on story comprehension.",
                        pastDropoff: "🌟 <strong>Critical Success:</strong> Past the ~{{dropoff}}% threshold with the power of a Nat 20!",
                        completed: "🌟 <strong>Critical Finisher!</strong> Reader #20 completes Session {{s}} on a legendary Nat 20 roll!"
                    }},
                    42: {{
                        initial: "🌌 <strong>Reader #42:</strong> The ultimate answer to the universe, life, and D&D storyboards.",
                        inProgress: "🌌 <strong>Universal Truth:</strong> Reader #42 deciphering the lore at {{depth}}% depth.",
                        pastDropoff: "🌌 <strong>Deep Answer:</strong> Reader #42 outlasting the drop-offs at {{depth}}%!",
                        completed: "🌌 <strong>The Ultimate Answer:</strong> Reader #42 finishes the entire cosmic journey!"
                    }},
                    100: {{
                        initial: "💯 <strong>Centurion Milestone!</strong> You are Reader #100! A landmark moment for Session {{s}}.",
                        inProgress: "💯 <strong>Centurion in Motion:</strong> Reader #100 powering through at {{depth}}% depth.",
                        pastDropoff: "💯 <strong>Centurion Surge:</strong> Past the ~{{dropoff}}% line—lead the 100th cohort to the finish!",
                        completed: "💯 <strong>Centurion Champion:</strong> Reader #100 finishes Session {{s}} in triumph!"
                    }}
                }},
                completed: [
                    "🏆 <strong>Session {{s}} Complete!</strong> You finished the entire story and earned your badge in the Finisher Circle ({{c}}/{{r}} readers).",
                    "✨ <strong>Legend Achieved!</strong> You journeyed through all chapters of Session {{s}} to the final word. The Margin remembers your tale.",
                    "📜 <strong>Chronicle Mastered!</strong> You are one of the dedicated readers ({{c}}/{{r}}) who experienced every scene.",
                    "🎉 <strong>100% Story Mastery:</strong> You've reached the concluding sentinel of Session {{s}}! Feel free to review passages or leave critique notes."
                ],
                climax: [
                    "⚡ <strong>The Climax Unfolds:</strong> You're at {{depth}}% depth—the major plot threads are converging! Push through to the finale.",
                    "🔥 <strong>Final Stretch!</strong> Just ~{{remaining}}% left to finish Session {{s}}! The resolution is within reach.",
                    "⚔️ <strong>The Crucible:</strong> You've navigated the deepest revelations. Don't stop now—join the Finisher Circle!",
                    "🌟 <strong>Almost at the Summit:</strong> At {{depth}}%, you're in the final scenes of this session. Cross the finish line!"
                ],
                pastDropoff: [
                    "🚀 <strong>High Momentum:</strong> You're at {{depth}}% depth, cruising past the average drop-off point (~{{dropoff}}%). Keep turning pages!",
                    "🛡️ <strong>Beyond the Drop-Off:</strong> Most readers pause around ~{{dropoff}}%, but you're at {{depth}}%. The story is heating up!",
                    "🔮 <strong>Timeline Unbroken:</strong> You've outlasted the ~{{dropoff}}% threshold. You're well on your way to 100% completion!",
                    "🔥 <strong>Unstoppable Pace:</strong> You've surged past the ~{{dropoff}}% mark. Dive into the next scene to reach the finale!"
                ],
                approaching: [
                    "🧭 <strong>Deep in the Weave:</strong> You're at {{depth}}% depth. Read past the ~{{dropoff}}% marker to unlock the major story turns!",
                    "📖 <strong>The Mystery Deepens:</strong> You're at {{depth}}%. Push forward to discover what lies beyond the next chapter!",
                    "🎲 <strong>Roll for Persistence:</strong> You're at {{depth}}%. The turning point of Session {{s}} is just ahead!",
                    "⏳ <strong>Building Momentum:</strong> At {{depth}}%, the character interactions are hitting their stride. Keep scrolling!"
                ],
                early: [
                    "🌿 <strong>Stepping into The Margin:</strong> You're at {{depth}}% depth as Reader #{{rnum}}. Settle in and follow the dialogue!",
                    "🗝️ <strong>The Portal Opens:</strong> Reader #{{rnum}} has begun Session {{s}}. Follow the party's journey as the plot takes shape.",
                    "✨ <strong>The Adventure Begins:</strong> Scroll through the passages to build your reading progress and unlock the lore.",
                    "🗺️ <strong>Charting New Ground:</strong> You've started reading Session {{s}}. Keep scrolling to advance your track!"
                ],
                initial: [
                    "📖 <strong>Welcome Reader #{{rnum}}!</strong> Scroll through the story blocks below to build your progress and join the Finisher Circle!",
                    "✨ <strong>Welcome to Session {{s}}:</strong> Start scrolling to track your reading depth against the readership base."
                ]
            }};

            function getMotivationalBlurb(depth, avgDropoff, isCompleted, cCount, rCount, sNum, rNum) {{
                // Check if an Easter egg exists for this specific reader number
                const egg = MOTIVATIONAL_BLURBS.easterEggs[rNum];
                if (egg) {{
                    let eggStr = "";
                    if (isCompleted) {{
                        eggStr = egg.completed || egg.inProgress || egg.initial;
                    }} else if (depth > 0 && depth >= avgDropoff && avgDropoff > 0) {{
                        eggStr = egg.pastDropoff || egg.inProgress || egg.initial;
                    }} else if (depth > 0) {{
                        eggStr = egg.inProgress || egg.initial;
                    }} else {{
                        eggStr = egg.initial;
                    }}
                    if (eggStr) {{
                        return eggStr
                            .replaceAll('{{depth}}', depth)
                            .replaceAll('{{dropoff}}', avgDropoff || 45)
                            .replaceAll('{{remaining}}', Math.max(1, 100 - depth))
                            .replaceAll('{{c}}', cCount)
                            .replaceAll('{{r}}', rCount)
                            .replaceAll('{{s}}', sNum)
                            .replaceAll('{{rnum}}', rNum);
                    }}
                }}

                let pool = [];
                if (isCompleted) {{
                    pool = MOTIVATIONAL_BLURBS.completed;
                }} else if (depth >= 75) {{
                    pool = MOTIVATIONAL_BLURBS.climax;
                }} else if (depth > 0 && depth >= avgDropoff && avgDropoff > 0) {{
                    pool = MOTIVATIONAL_BLURBS.pastDropoff;
                }} else if (depth >= 30) {{
                    pool = MOTIVATIONAL_BLURBS.approaching;
                }} else if (depth > 0) {{
                    pool = MOTIVATIONAL_BLURBS.early;
                }} else {{
                    pool = MOTIVATIONAL_BLURBS.initial;
                }}
                const idx = (depth + sNum + rCount) % pool.length;
                return pool[idx]
                    .replaceAll('{{depth}}', depth)
                    .replaceAll('{{dropoff}}', avgDropoff || 45)
                    .replaceAll('{{remaining}}', Math.max(1, 100 - depth))
                    .replaceAll('{{c}}', cCount)
                    .replaceAll('{{r}}', rCount)
                    .replaceAll('{{s}}', sNum)
                    .replaceAll('{{rnum}}', rNum);
            }}

            function updateTelemetryUI() {{
                const uniqueEl = document.getElementById('telemetryUniqueReaders');
                const opensEl = document.getElementById('telemetryTotalOpens');
                const compEl = document.getElementById('telemetryCompletionRate');
                const finisherRatioEl = document.getElementById('telemetryFinisherRatio');
                const dropoffEl = document.getElementById('telemetryDropoffDepth');
                
                const userProgressFill = document.getElementById('telemetryPersonalProgressFill');
                const dropoffMarker = document.getElementById('telemetryDropoffMarker');
                const dropoffMarkerText = document.getElementById('telemetryDropoffMarkerText');
                const userPin = document.getElementById('telemetryUserPin');
                const userPinText = document.getElementById('telemetryUserPinText');
                const motivationBanner = document.getElementById('telemetryMotivationBanner');
                const motivationText = document.getElementById('telemetryMotivationText');

                const rCount = Math.max(1, globalTelemetry.readers);
                const oCount = Math.max(1, globalTelemetry.opens);
                const cCount = globalTelemetry.completions;
                const compPct = Math.min(100, Math.max(0, Math.round((cCount / rCount) * 100)));

                const incCount = globalTelemetry.incompleteCount || 0;
                const incSum = globalTelemetry.incompleteDepthSum || 0;
                const avgDropoffPct = incCount > 0 ? Math.min(99, Math.max(0, Math.round(incSum / incCount))) : 0;
                const myDepth = localTelemetry.maxDepth || 0;
                const isCompleted = localTelemetry.completed || myDepth >= 95;
                const myReaderNum = localTelemetry.readerNumber || 1;

                if (uniqueEl) uniqueEl.textContent = globalTelemetry.readers.toLocaleString();
                if (opensEl) opensEl.textContent = globalTelemetry.opens.toLocaleString();
                if (finisherRatioEl) finisherRatioEl.textContent = cCount + '/' + rCount;
                if (compEl) compEl.textContent = compPct + '%';
                if (dropoffEl) {{
                    if (incCount > 0) {{
                        dropoffEl.textContent = avgDropoffPct + '%';
                    }} else if (cCount > 0) {{
                        dropoffEl.textContent = 'None';
                    }} else {{
                        dropoffEl.textContent = '0%';
                    }}
                }}

                // Update visual track (Orange -> Purple -> Blue -> Green when complete)
                const displayUserDepth = isCompleted ? 100 : myDepth;
                if (userProgressFill) {{
                    userProgressFill.style.width = displayUserDepth + '%';
                    if (isCompleted || displayUserDepth >= 98) {{
                        userProgressFill.className = "h-full bg-gradient-to-r from-emerald-600 via-emerald-500 to-emerald-400 shadow-[0_0_12px_rgba(52,211,153,0.7)] transition-all duration-300 rounded-full";
                    }} else if (displayUserDepth < 35) {{
                        userProgressFill.className = "h-full bg-gradient-to-r from-amber-600 via-amber-500 to-orange-400 shadow-[0_0_8px_rgba(245,158,11,0.3)] transition-all duration-300 rounded-full";
                    }} else if (displayUserDepth < 70) {{
                        userProgressFill.className = "h-full bg-gradient-to-r from-purple-600 via-indigo-500 to-violet-400 shadow-[0_0_8px_rgba(139,92,246,0.3)] transition-all duration-300 rounded-full";
                    }} else {{
                        userProgressFill.className = "h-full bg-gradient-to-r from-blue-600 via-sky-500 to-cyan-400 shadow-[0_0_8px_rgba(56,189,248,0.3)] transition-all duration-300 rounded-full";
                    }}
                }}
                
                if (userPin) {{
                    userPin.style.left = Math.min(94, Math.max(5, displayUserDepth)) + '%';
                }}
                if (userPinText) {{
                    userPinText.textContent = isCompleted ? 'You: 100% 🏆' : ('You: ' + displayUserDepth + '%');
                }}

                if (dropoffMarker && dropoffMarkerText) {{
                    if (incCount > 0 && avgDropoffPct > 0) {{
                        dropoffMarker.style.display = 'flex';
                        dropoffMarker.style.left = Math.min(90, Math.max(8, avgDropoffPct)) + '%';
                        dropoffMarkerText.textContent = 'Avg Exit ~' + avgDropoffPct + '%';
                    }} else {{
                        dropoffMarker.style.display = 'none';
                    }}
                }}

                // Motivational Guidance Banner via rich blurb library with Easter eggs
                if (motivationText && motivationBanner) {{
                    motivationText.innerHTML = getMotivationalBlurb(myDepth, avgDropoffPct, isCompleted, cCount, rCount, {session_num}, myReaderNum);
                    if (isCompleted) {{
                        motivationBanner.className = "text-[11px] p-2.5 rounded-lg bg-emerald-950/60 border border-emerald-800 text-emerald-300 leading-normal flex items-center gap-2 shadow-inner";
                    }} else if (myDepth > 0 && myDepth >= avgDropoffPct && avgDropoffPct > 0) {{
                        motivationBanner.className = "text-[11px] p-2.5 rounded-lg bg-amber-950/60 border border-amber-800 text-amber-200 leading-normal flex items-center gap-2 shadow-inner";
                    }} else {{
                        motivationBanner.className = "text-[11px] p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 leading-normal flex items-center gap-2";
                    }}
                }}
            }}
            updateTelemetryUI();

            // Real-time scroll depth and drop-off recorder
            let scrollDebounceTimer = null;
            function recordScrollProgress() {{
                const totalScroll = document.documentElement.scrollHeight - window.innerHeight;
                if (totalScroll <= 0) return;
                const currentDepth = Math.min(100, Math.max(0, Math.round((window.scrollY / totalScroll) * 100)));

                if (currentDepth > (localTelemetry.maxDepth || 0)) {{
                    const prevDepth = localTelemetry.maxDepth || 0;
                    localTelemetry.maxDepth = currentDepth;

                    if (!localTelemetry.completed) {{
                        if (currentDepth >= 95) {{
                            localTelemetry.completed = true;
                            globalTelemetry.completions += 1;
                            if (globalTelemetry.incompleteCount > 0) {{
                                globalTelemetry.incompleteDepthSum = Math.max(0, globalTelemetry.incompleteDepthSum - prevDepth);
                                globalTelemetry.incompleteCount = Math.max(0, globalTelemetry.incompleteCount - 1);
                            }}
                        }} else {{
                            const depthDelta = currentDepth - prevDepth;
                            globalTelemetry.incompleteDepthSum = (globalTelemetry.incompleteDepthSum || 0) + depthDelta;
                        }}
                    }}

                    saveTelemetryState();
                    updateTelemetryUI();
                    if (typeof updateTopProgressBar === 'function') updateTopProgressBar();
                }}
            }}

            window.addEventListener('scroll', () => {{
                if (scrollDebounceTimer) clearTimeout(scrollDebounceTimer);
                scrollDebounceTimer = setTimeout(recordScrollProgress, 100);
            }}, {{ passive: true }});

            // Sentinel Observer for final 100% completion
            const storySentinel = document.getElementById('storyEndSentinel');
            if (storySentinel && ('IntersectionObserver' in window)) {{
                const observer = new IntersectionObserver((entries) => {{
                    entries.forEach(entry => {{
                        if (entry.isIntersecting && !localTelemetry.completed) {{
                            const prevDepth = localTelemetry.maxDepth || 0;
                            localTelemetry.completed = true;
                            localTelemetry.maxDepth = 100;
                            globalTelemetry.completions += 1;
                            if (globalTelemetry.incompleteCount > 0) {{
                                globalTelemetry.incompleteDepthSum = Math.max(0, globalTelemetry.incompleteDepthSum - prevDepth);
                                globalTelemetry.incompleteCount = Math.max(0, globalTelemetry.incompleteCount - 1);
                            }}
                            saveTelemetryState();
                            updateTelemetryUI();
                            if (typeof updateTopProgressBar === 'function') updateTopProgressBar();
                        }}
                    }});
                }}, {{ threshold: 0.1 }});
                observer.observe(storySentinel);
            }}

            // Fallback for completion
            window.addEventListener('scroll', () => {{
                if (!localTelemetry.completed && (window.innerHeight + window.scrollY) >= (document.body.offsetHeight - 350)) {{
                    const prevDepth = localTelemetry.maxDepth || 0;
                    localTelemetry.completed = true;
                    localTelemetry.maxDepth = 100;
                    globalTelemetry.completions += 1;
                    if (globalTelemetry.incompleteCount > 0) {{
                        globalTelemetry.incompleteDepthSum = Math.max(0, globalTelemetry.incompleteDepthSum - prevDepth);
                        globalTelemetry.incompleteCount = Math.max(0, globalTelemetry.incompleteCount - 1);
                    }}
                    saveTelemetryState();
                    updateTelemetryUI();
                    if (typeof updateTopProgressBar === 'function') updateTopProgressBar();
                }}
            }}, {{ passive: true }});

            refreshMarkers();
        }})();
    </script>
    <!-- Lightweight Visitor & Navigation Tracker -->
    <script src="traffic-tracker.js"></script>
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
