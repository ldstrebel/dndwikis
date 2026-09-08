"""Builds interactive Schema 2.0 HTML EBooks with:
1. Clean sticky top bar with "Chapters" button (replaces "Hide Stats")
2. Chapters Drawer with Vertical Chapter List (Y-Axis) & Stacked Horizontal Speaker Bars (X-Axis):
   - Each chapter displays chapter number, title, read time, and stacked horizontal bar of speakers (PC colors + red named NPCs)
   - Tapping any chapter row scrolls smoothly to that scene in the story
3. Secondary analytics (Character velocity line chart, KPIs, Campaign to date)
4. Elevated Mobile Critique Modal (Shifted above keyboard, top passage navigation arrows, dynamic scroll)
5. Natural prose flow for narration blocks
6. Named NPCs in red (#f87171), clean PC names, fast scene jump pills
"""

import json
import re
from pathlib import Path

MANIFEST_DIR = Path("d:/Code/dnd-scribe/sessions/data/index")
OUTPUT_DIR = Path("d:/Code/dndwikis-main/dndwikis-main")

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

def get_speaker_color(speaker_id: str, char_info: dict = None) -> str:
    sp_id = speaker_id.lower().strip()
    if sp_id in PC_COLORS:
        return PC_COLORS[sp_id]
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

def build_vertical_chapters_html(chapters: list, characters: dict) -> str:
    """Builds a vertical chapter list (Y-Axis) with stacked horizontal speaker bars (X-Axis)."""
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
            "read_mins": max(1, round(ch["word_count"] / 250)),
            "dialogue_words": tot_dialogue,
            "speakers": speaker_words,
            "anchor_id": f"chapter-{idx}"
        })

    rows_html = []
    for cd in chapter_data:
        tot_d = cd["dialogue_words"]
        bar_fill_pct = max(12, round((tot_d / max_dialogue) * 100)) if tot_d > 0 else 0

        # Stacked horizontal bar segments
        segments = []
        speaker_legend_mini = []
        if tot_d > 0:
            for sp, w in sorted(cd["speakers"].items(), key=lambda x: -x[1]):
                c_info = characters.get(sp, {})
                sp_name = c_info.get("name", sp.title())
                col = get_speaker_color(sp, c_info)
                seg_pct = round((w / tot_d) * 100, 1)
                segments.append(
                    f'<div style="width: {seg_pct}%; background-color: {col};" class="h-full border-r border-slate-900/40" title="{sp_name}: {w}w ({seg_pct}%)"></div>'
                )
                speaker_legend_mini.append(
                    f'<span class="flex items-center gap-1"><span class="w-1.5 h-1.5 rounded-full" style="background-color: {col}"></span><span class="text-slate-300">{sp_name}</span> <strong class="font-mono text-slate-400 text-[9px]">{w}w</strong></span>'
                )
        else:
            segments.append('<div class="w-full h-full bg-slate-800/40" title="Narrative prose only"></div>')

        row_item = f"""
        <div class="p-2.5 sm:p-3 bg-slate-950/70 hover:bg-slate-900/90 border border-slate-800/80 hover:border-amber-500/50 rounded-xl transition-all cursor-pointer group shadow-sm flex flex-col gap-2 select-none"
             onclick="scrollToAnchor('{cd['anchor_id']}'); toggleChapters();">
            
            <div class="flex items-center justify-between gap-2">
                <div class="flex items-center gap-2 min-w-0">
                    <span class="px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/30 text-[10px] font-mono font-bold flex-shrink-0">
                        Ch {cd['num']}
                    </span>
                    <h4 class="text-xs sm:text-sm font-semibold text-slate-200 group-hover:text-amber-300 transition-colors truncate">
                        {cd['clean_title']}
                    </h4>
                </div>
                <span class="text-[10px] text-slate-500 font-mono flex-shrink-0">
                    ~{cd['read_mins']}m · {cd['total_words']:,}w
                </span>
            </div>

            <!-- X-Axis Stacked Dialogue Bar -->
            <div class="flex items-center gap-2 pt-0.5">
                <div class="flex-1 bg-slate-900 h-2.5 rounded-full overflow-hidden flex border border-slate-800 shadow-inner">
                    <div class="h-full flex rounded-full overflow-hidden" style="width: {bar_fill_pct}%;">
                        {''.join(segments)}
                    </div>
                </div>
                <span class="text-[10px] font-mono { 'text-amber-400 font-bold' if tot_d > 0 else 'text-slate-500 italic' } w-20 text-right flex-shrink-0">
                    { f"{tot_d}w spoken" if tot_d > 0 else "Prose only" }
                </span>
            </div>

            <!-- Mini Speaker Breakdown -->
            { f'<div class="flex flex-wrap gap-2 text-[10px] text-slate-400 pt-0.5 border-t border-slate-900/60">{"".join(speaker_legend_mini)}</div>' if speaker_legend_mini else '' }
        </div>
        """
        rows_html.append(row_item)

    return f"""
    <div class="space-y-2">
        <div class="flex items-center justify-between text-[11px] text-slate-400 px-1 mb-1">
            <span>Chapter Index (Y-Axis)</span>
            <span class="text-[10px] text-slate-500 font-mono">X-Axis: Speaker Share (Tap row to jump)</span>
        </div>
        <div class="space-y-2 max-h-[65vh] overflow-y-auto pr-1 custom-scrollbar">
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
        <div class="bg-slate-950/60 rounded-xl p-2.5 border border-slate-800">
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
    word_count = stats.get("wordCount", sum(len(b.get("text", "").split()) for b in blocks))
    read_mins = stats.get("estimatedReadMinutes", max(1, round(word_count / 250)))
    book_pages = stats.get("estimatedBookPages", round(word_count / 250, 1))
    diag_ratio = stats.get("dialogueRatio", {})
    spoken_pct = diag_ratio.get("spokenPct", 35)
    narrative_pct = diag_ratio.get("narrativePct", 65)
    raw_speaker_dist = stats.get("speakerDistribution", [])
    writing_metrics = stats.get("writingMetrics", {})
    sensory = writing_metrics.get("sensoryRegisters", {})

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

    # Legend Chips
    speaker_chips = ""
    for sp in spoken_speakers:
        pct = sp["pct"]
        color = sp["color"]
        name = sp["name"]
        npc_badge = '<span class="text-[9px] px-1 py-0.2 rounded bg-rose-950/60 text-rose-300 border border-rose-800/60 font-mono">NPC</span>' if sp["is_npc"] else ""
        speaker_chips += f"""
            <div class="flex items-center gap-1.5 text-xs text-slate-300 py-0.5">
                <span class="w-2.5 h-2.5 rounded-full flex-shrink-0" style="background-color: {color}"></span>
                <span class="font-medium truncate">{name}</span>
                {npc_badge}
                <span class="font-mono font-bold ml-auto" style="color: {color}">{pct}%</span>
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

    # =========================================================================
    # CHAPTERS & ANALYTICS DRAWER HTML
    # =========================================================================
    vertical_chapters_html = build_vertical_chapters_html(chapters, characters)
    session_line_chart_svg = build_session_line_chart_svg(chapters)
    campaign_whole_html = build_campaign_whole_html(session_num)
    camp_tab_label = "Campaign (S1)" if session_num == 1 else f"Campaign (S1–S{session_num})"

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
                    <span class="text-[11px] font-bold font-mono tracking-widest text-amber-500 uppercase">Part {chapter_index} (~{ch_mins}m read · {ch_words:,}w)</span>
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

        #sessionChaptersSection.collapsed {{
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
            transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.2s ease;
            transform: scale(0.96) translateY(-10px);
            opacity: 0;
            max-height: min(85vh, 85dvh);
        }}
        #critiqueModalOverlay.visible #critiqueBottomSheet {{
            transform: scale(1) translateY(0);
            opacity: 1;
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
    </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen pb-24 mode-critique">

    <!-- STICKY TOP APP BAR (Clean & Content-Focused) -->
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

            <!-- Header Controls: Chapters Button & Reading Mode Switcher -->
            <div class="flex items-center gap-2 flex-shrink-0">
                <button id="toggleChaptersBtn" type="button" class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 border border-slate-700 text-amber-300 flex items-center gap-1.5 transition-all shadow-sm active:scale-95" title="View Table of Contents & Chapter Dialogue Breakdown">
                    <span>📑</span>
                    <span id="toggleChaptersBtnLabel">Chapters</span>
                </button>

                <div class="flex bg-slate-950 border border-slate-800 rounded-lg p-0.5" title="Switch reading mode">
                    <button id="modeReaderBtn" type="button" class="px-2.5 py-1 rounded-md text-xs font-medium text-slate-400 hover:text-slate-200 transition-all flex items-center gap-1">
                        <span>📖</span> <span class="hidden sm:inline">Read</span>
                    </button>
                    <button id="modeCritiqueBtn" type="button" class="px-2.5 py-1 rounded-md text-xs font-bold text-slate-950 bg-amber-400 shadow transition-all flex items-center gap-1">
                        <span>✍️</span> <span class="hidden sm:inline">Critique</span>
                    </button>
                </div>
            </div>
        </div>
    </header>

    <!-- WRAPPER -->
    <div class="max-w-3xl mx-auto px-4 sm:px-6 pt-6">

        <!-- ========================================================= -->
        <!-- CHAPTERS & DIALOGUE BREAKDOWN DRAWER (Vertical Y-Axis List & Stacked X-Axis Bars) -->
        <!-- ========================================================= -->
        <section id="sessionChaptersSection" class="mb-8">
            <div class="bg-slate-900/90 border border-slate-800 rounded-2xl p-4 sm:p-5 shadow-2xl backdrop-blur-sm space-y-4">
                
                <!-- Drawer Header -->
                <div class="flex items-center justify-between border-b border-slate-800 pb-3">
                    <div class="flex items-center gap-2">
                        <span class="text-lg">📑</span>
                        <div>
                            <h2 class="text-sm font-bold tracking-wider uppercase text-amber-400">Chapters & Dialogue Breakdown</h2>
                            <p class="text-[11px] text-slate-400 font-mono">Session {session_num} · {len(chapters)} Chapters · {word_count:,} words (~{read_mins}m)</p>
                        </div>
                    </div>
                    <button id="closeChaptersDrawerBtn" type="button" class="text-xs text-slate-400 hover:text-slate-200 font-semibold flex items-center gap-1 bg-slate-800 hover:bg-slate-700 px-2.5 py-1 rounded-lg border border-slate-700 transition-colors">
                        <span>Close ▲</span>
                    </button>
                </div>

                <!-- Vertical Chapter List with Stacked Horizontal Dialogue Bars -->
                <div class="w-full">
                    {vertical_chapters_html}
                </div>

                <!-- Secondary Collapsible Analytics: Velocity Line Chart, KPIs & Campaign to Date -->
                <div class="pt-3 border-t border-slate-800/80 space-y-3">
                    
                    <!-- Mode Switcher for Analytics Tabs -->
                    <div class="flex flex-wrap items-center justify-between gap-2">
                        <span class="text-xs font-bold text-slate-400 uppercase tracking-wider font-mono">Analytics & Velocity</span>
                        <div class="flex bg-slate-950 border border-slate-800 rounded-lg p-0.5">
                            <button id="chartTabLineBtn" type="button" class="px-2.5 py-1 rounded-md text-[11px] font-bold text-slate-950 bg-amber-400 shadow transition-all flex items-center gap-1" onclick="switchChartTab('line')">
                                <span>📈</span> <span>Voice Velocity</span>
                            </button>
                            <button id="chartTabStatsBtn" type="button" class="px-2.5 py-1 rounded-md text-[11px] font-medium text-slate-400 hover:text-slate-200 transition-all flex items-center gap-1" onclick="switchChartTab('stats')">
                                <span>📊</span> <span>Session KPIs</span>
                            </button>
                            <button id="chartTabCampaignBtn" type="button" class="px-2.5 py-1 rounded-md text-[11px] font-medium text-slate-400 hover:text-slate-200 transition-all flex items-center gap-1" onclick="switchChartTab('campaign')">
                                <span>🌐</span> <span>{camp_tab_label}</span>
                            </button>
                        </div>
                    </div>

                    <!-- View 1: Character Velocity SVG Line Chart -->
                    <div id="chartViewLine" class="w-full">
                        {session_line_chart_svg}
                    </div>

                    <!-- View 2: Unified KPIs & Sensory Palette -->
                    <div id="chartViewStats" class="w-full hidden space-y-3">
                        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
                            <div class="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
                                <div class="text-[11px] text-slate-400 font-medium">Story Length & Read Time</div>
                                <div class="text-lg font-bold text-slate-100 mt-0.5 font-mono">{word_count:,} <span class="text-xs text-slate-500 font-normal">words</span></div>
                                <div class="text-[11px] text-emerald-400 mt-0.5">~{book_pages} Book Pages · {read_mins}m Read</div>
                            </div>

                            <div class="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
                                <div class="text-[11px] text-slate-400 font-medium">Dialogue Ratio</div>
                                <div class="text-lg font-bold text-amber-400 mt-0.5 font-mono">{spoken_pct}% <span class="text-xs text-slate-500 font-normal">spoken</span></div>
                                <div class="text-[11px] text-slate-400 mt-0.5">{narrative_pct}% Narrative Prose</div>
                            </div>

                            <div class="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
                                <div class="text-[11px] text-slate-400 font-medium mb-1.5">Sensory Palette ({sensory.get("registersCovered", 5)}/5)</div>
                                <div class="flex flex-wrap gap-1">
                                    <span class="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 text-[10px]">👁️ <strong class="text-amber-400">{sensory.get("visual", 30)}</strong></span>
                                    <span class="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 text-[10px]">👂 <strong class="text-sky-400">{sensory.get("auditory", 15)}</strong></span>
                                    <span class="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 text-[10px]">✋ <strong class="text-emerald-400">{sensory.get("tactile", 20)}</strong></span>
                                    <span class="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 text-[10px]">⚡ <strong class="text-amber-300">{sensory.get("atmospheric", 15)}</strong></span>
                                </div>
                            </div>
                        </div>

                        <!-- Spoken Line Share Progress Bar & Legend -->
                        <div class="space-y-2 bg-slate-950/40 p-3.5 rounded-xl border border-slate-800/60">
                            <div class="flex justify-between items-center text-xs font-semibold text-slate-300 mb-1">
                                <span>🎙️ Spoken Line Share ({total_spoken_words:,} spoken words across {len(spoken_speakers)} active voices)</span>
                            </div>
                            <div class="h-2.5 w-full rounded-full bg-slate-800 flex overflow-hidden shadow-inner">
                                {prog_bar_segments}
                            </div>
                            <div class="grid grid-cols-2 sm:grid-cols-3 gap-2 pt-1">
                                {speaker_chips}
                            </div>
                        </div>
                    </div>

                    <!-- View 3: Campaign Whole Comparison (Scoped to current session and before) -->
                    <div id="chartViewCampaign" class="w-full hidden">
                        {campaign_whole_html}
                    </div>

                </div>

            </div>
        </section>

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

        <!-- Bottom Page Controls & Review Summary -->
        <footer class="mt-16 pt-8 border-t border-slate-800 text-center space-y-4">
            <div class="bg-slate-900/60 p-5 rounded-2xl border border-slate-800 max-w-md mx-auto shadow-lg">
                <div class="flex items-center justify-center gap-2 text-amber-400 mb-1">
                    <span class="text-lg">🐙</span>
                    <h3 class="text-sm font-bold">Submit Review PR to GitHub</h3>
                </div>
                <p class="text-xs text-slate-400 mb-3">Submit your feedback directly to the dnd-scribe agent pipeline.</p>
                <div class="flex gap-2 justify-center">
                    <button id="footerExportBtn" type="button" class="px-5 py-2.5 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 text-slate-950 font-bold rounded-xl text-xs transition-all shadow-md flex items-center gap-1.5">
                        <span>🚀</span> <span>Open Review PR</span>
                        <span id="exportBadgeCount" class="bg-slate-950 text-amber-300 text-[10px] px-1.5 py-0.2 rounded-full font-bold ml-1">0</span>
                    </button>
                    <button id="clearCritiquesBtn" type="button" class="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 text-xs font-semibold rounded-xl transition-colors">
                        Clear All
                    </button>
                </div>
            </div>
            <p class="text-xs text-slate-600">UNERASEABLE © D&D Scribe Engine · Schema 2.0 Indexed.</p>
        </footer>

    </div>

    <!-- ========================================================= -->
    <!-- MOBILE CRITIQUE MODAL / PASSAGE EDITOR -->
    <!-- ========================================================= -->
    <div id="critiqueModalOverlay" class="fixed inset-0 bg-slate-950/85 backdrop-blur-sm z-50 flex items-start sm:items-center justify-center opacity-0 pointer-events-none p-3 sm:p-4 overflow-y-auto pt-5 sm:pt-4">
        <div id="critiqueBottomSheet" class="w-full max-w-lg bg-slate-900 border border-slate-700 rounded-2xl p-4 sm:p-5 shadow-2xl flex flex-col my-auto max-h-[85vh] sm:max-h-[82vh]">
            
            <!-- Top Header with Speaker, Block ID, and Prev/Next Passage Navigation -->
            <div class="flex items-center justify-between border-b border-slate-800 pb-3 mb-3 gap-2 flex-shrink-0">
                <div class="flex items-center gap-2 min-w-0">
                    <span id="modalSpeakerPill" class="px-2.5 py-1 rounded-md text-xs font-bold uppercase tracking-wider font-mono truncate"></span>
                    <span id="modalBlockIndex" class="text-xs text-slate-400 font-mono flex-shrink-0"></span>
                </div>
                <div class="flex items-center gap-1.5 flex-shrink-0">
                    <!-- Shifted Arrow Keys to Top for rapid passage jumping -->
                    <button id="modalPrevBlockBtn" type="button" class="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 active:bg-slate-600 border border-slate-700 text-slate-200 rounded-lg text-xs font-semibold flex items-center gap-1 transition-all" title="Previous passage">
                        <span>◀</span> <span class="hidden xs:inline text-[11px]">Prev</span>
                    </button>
                    <button id="modalNextBlockBtn" type="button" class="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 active:bg-slate-600 border border-slate-700 text-slate-200 rounded-lg text-xs font-semibold flex items-center gap-1 transition-all" title="Next passage">
                        <span class="hidden xs:inline text-[11px]">Next</span> <span>▶</span>
                    </button>
                    <button id="modalCloseBtn" type="button" class="text-slate-400 hover:text-slate-200 text-xl font-bold p-1 ml-1 leading-none transition-colors" title="Close">&times;</button>
                </div>
            </div>

            <!-- Scrollable Content Body (Expands & Scrolls Gracefully) -->
            <div class="overflow-y-auto space-y-3.5 pr-1 flex-1 min-h-0 custom-scrollbar">
                <div class="bg-slate-950/80 p-3 rounded-xl border border-slate-800/80">
                    <div class="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">Target Passage:</div>
                    <p id="modalPassageText" class="text-xs sm:text-sm text-slate-200 italic leading-relaxed max-h-28 overflow-y-auto custom-scrollbar"></p>
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
                    <textarea id="critiqueTextInput" rows="2" class="w-full bg-slate-950 border border-slate-700 rounded-xl p-2.5 text-xs sm:text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500" placeholder="E.g. Make this interaction sharper, emphasize the tension..."></textarea>
                </div>
                <div>
                    <label for="suggestedRewriteInput" class="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">Direct Suggested Rewrite <span class="text-slate-600 font-normal lowercase">(optional)</span></label>
                    <textarea id="suggestedRewriteInput" rows="2" class="w-full bg-slate-950 border border-slate-800 rounded-xl p-2 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-cyan-500" placeholder="Provide direct replacement line if desired..."></textarea>
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

    <!-- JAVASCRIPT CONTROLLER -->
    <script>
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
            let selectedCategory = "tone";
            const blocks = Array.from(document.querySelectorAll('.story-block'));

            const chaptersSection = document.getElementById('sessionChaptersSection');
            const toggleChaptersBtn = document.getElementById('toggleChaptersBtn');
            const closeChaptersDrawerBtn = document.getElementById('closeChaptersDrawerBtn');
            const modeReaderBtn = document.getElementById('modeReaderBtn');
            const modeCritiqueBtn = document.getElementById('modeCritiqueBtn');
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
            const categoryPills = Array.from(document.querySelectorAll('.category-pill'));

            // Smooth Scroll Helper
            window.scrollToAnchor = function(id) {{
                const el = document.getElementById(id);
                if (el) {{
                    el.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                }}
            }};

            // Chapters Drawer Toggle
            window.toggleChapters = function() {{
                if (!chaptersSection) return;
                chaptersSection.classList.toggle('collapsed');
            }};

            if (toggleChaptersBtn) toggleChaptersBtn.onclick = toggleChapters;
            if (closeChaptersDrawerBtn) closeChaptersDrawerBtn.onclick = toggleChapters;

            // Analytics Tab Switcher
            window.switchChartTab = function(tabName) {{
                const lineView = document.getElementById('chartViewLine');
                const statsView = document.getElementById('chartViewStats');
                const campView = document.getElementById('chartViewCampaign');
                
                const lineBtn = document.getElementById('chartTabLineBtn');
                const statsBtn = document.getElementById('chartTabStatsBtn');
                const campBtn = document.getElementById('chartTabCampaignBtn');
                
                const activeClass = "px-2.5 py-1 rounded-md text-[11px] font-bold text-slate-950 bg-amber-400 shadow transition-all flex items-center gap-1";
                const inactiveClass = "px-2.5 py-1 rounded-md text-[11px] font-medium text-slate-400 hover:text-slate-200 transition-all flex items-center gap-1";
                
                if (lineView) lineView.classList.toggle('hidden', tabName !== 'line');
                if (statsView) statsView.classList.toggle('hidden', tabName !== 'stats');
                if (campView) campView.classList.toggle('hidden', tabName !== 'campaign');
                
                if (lineBtn) lineBtn.className = (tabName === 'line') ? activeClass : inactiveClass;
                if (statsBtn) statsBtn.className = (tabName === 'stats') ? activeClass : inactiveClass;
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

            if (modeReaderBtn && modeCritiqueBtn) {{
                modeReaderBtn.onclick = function() {{
                    document.body.classList.remove('mode-critique');
                    modeReaderBtn.className = "px-2.5 py-1 rounded-md text-xs font-bold text-slate-950 bg-amber-400 shadow transition-all flex items-center gap-1";
                    modeCritiqueBtn.className = "px-2.5 py-1 rounded-md text-xs font-medium text-slate-400 hover:text-slate-200 transition-all flex items-center gap-1";
                }};

                modeCritiqueBtn.onclick = function() {{
                    document.body.classList.add('mode-critique');
                    modeCritiqueBtn.className = "px-2.5 py-1 rounded-md text-xs font-bold text-slate-950 bg-amber-400 shadow transition-all flex items-center gap-1";
                    modeReaderBtn.className = "px-2.5 py-1 rounded-md text-xs font-medium text-slate-400 hover:text-slate-200 transition-all flex items-center gap-1";
                }};
            }}

            categoryPills.forEach(pill => {{
                pill.onclick = function() {{
                    categoryPills.forEach(p => {{
                        p.className = "category-pill px-2 py-1.5 rounded-lg text-[11px] font-medium border border-slate-700 bg-slate-800 text-slate-300 text-center";
                    }});
                    pill.className = "category-pill active px-2 py-1.5 rounded-lg text-[11px] font-bold border border-amber-500 bg-amber-500/20 text-amber-300 text-center";
                    selectedCategory = pill.dataset.category || "tone";
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

                if (modalSpeakerPill) {{
                    modalSpeakerPill.textContent = speakerName;
                    modalSpeakerPill.style.backgroundColor = speakerColor + "25";
                    modalSpeakerPill.style.borderColor = speakerColor;
                    modalSpeakerPill.style.color = speakerColor;
                }}
                if (modalBlockIndex) modalBlockIndex.textContent = "#" + (index + 1) + " (" + blockId + ")";
                if (modalPassageText) modalPassageText.textContent = '"' + text + '"';

                const existing = critiques[blockId];
                if (existing) {{
                    if (critiqueTextInput) critiqueTextInput.value = existing.comment || "";
                    if (suggestedRewriteInput) suggestedRewriteInput.value = existing.suggestedRewrite || "";
                    selectedCategory = existing.category || "tone";
                    if (modalDeleteBtn) modalDeleteBtn.classList.remove('hidden');

                    categoryPills.forEach(pill => {{
                        if (pill.dataset.category === selectedCategory) pill.click();
                    }});
                }} else {{
                    if (critiqueTextInput) critiqueTextInput.value = "";
                    if (suggestedRewriteInput) suggestedRewriteInput.value = "";
                    if (modalDeleteBtn) modalDeleteBtn.classList.add('hidden');
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
                if (modalOverlay) modalOverlay.classList.add('visible');
                if (critiqueTextInput) {{
                    setTimeout(() => critiqueTextInput.focus(), 50);
                }}
            }}

            function closeModal() {{
                if (modalOverlay) modalOverlay.classList.remove('visible');
            }}

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
                if (!modalOverlay || !modalOverlay.classList.contains('visible')) return;
                if (e.key === 'Escape') {{
                    closeModal();
                }} else if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {{
                    if (modalSaveBtn) modalSaveBtn.click();
                }}
            }});

            if (modalSaveBtn) modalSaveBtn.onclick = function() {{
                const block = blocks[activeBlockIndex];
                if (!block) return;
                const blockId = block.dataset.blockId;
                const comment = critiqueTextInput ? critiqueTextInput.value.trim() : "";
                const rewrite = suggestedRewriteInput ? suggestedRewriteInput.value.trim() : "";
                const p = block.querySelector('p');

                if (!comment && !rewrite) {{
                    alert("Please provide a critique note or suggested rewrite before saving.");
                    return;
                }}

                critiques[blockId] = {{
                    blockId: blockId,
                    blockIndex: activeBlockIndex + 1,
                    speaker: block.dataset.speakerName,
                    category: selectedCategory,
                    quote: p ? p.innerText : "",
                    comment: comment,
                    suggestedRewrite: rewrite,
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
                    if (document.body.classList.contains('mode-critique')) openModalForBlock(idx);
                }};
            }});

            // =========================================================
            // GITHUB PR SUBMISSION MODAL
            // =========================================================
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
                        <button id="closeGhModal" type="button" class="text-slate-400 hover:text-slate-200 text-xl font-bold">&times;</button>
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
                        <button id="ghCopyJsonBtn" type="button" class="flex-1 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold rounded-lg text-xs transition-colors">📋 Copy JSON</button>
                        <button id="ghSubmitPrBtn" type="button" class="flex-1 py-2 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 text-slate-950 font-bold rounded-lg text-xs transition-colors shadow-lg shadow-amber-500/20 flex items-center justify-center gap-1.5"><span>🚀</span> <span>Open PR</span></button>
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

            if (ghTokenInput) ghTokenInput.value = localStorage.getItem('dnd_scribe_gh_token') || '';
            if (ghReviewerNameInput) ghReviewerNameInput.value = localStorage.getItem('dnd_scribe_reviewer_name') || 'Reviewer';

            function showGhModal() {{
                const count = Object.keys(critiques).length;
                if (count === 0) {{
                    alert("No review notes recorded yet! Click on any dialogue or narrator block to add notes first.");
                    return;
                }}
                if (ghCritiqueCountDisplay) ghCritiqueCountDisplay.textContent = count + " critique(s)";
                if (ghStatusMsg) ghStatusMsg.className = "hidden";
                if (ghModalOverlay) ghModalOverlay.classList.remove('opacity-0', 'pointer-events-none');
            }}

            function hideGhModal() {{
                if (ghModalOverlay) ghModalOverlay.classList.add('opacity-0', 'pointer-events-none');
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
                    const reviewer = ghReviewerNameInput ? ghReviewerNameInput.value.trim() : "Anonymous";
                    const exportPayload = {{
                        campaign: CAMPAIGN_ID,
                        chapter: CHAPTER_ID,
                        title: "Uneraseable - {session_title}",
                        reviewer: reviewer || "Anonymous",
                        exportedAt: new Date().toISOString(),
                        totalCritiques: count,
                        critiques: Object.values(critiques)
                    }};
                    navigator.clipboard.writeText(JSON.stringify(exportPayload, null, 2)).then(() => {{
                        alert("✨ Copied " + count + " critique(s) to clipboard!");
                        hideGhModal();
                    }});
                }};
            }}

            if (ghSubmitPrBtn) {{
                ghSubmitPrBtn.onclick = async function() {{
                    const token = ghTokenInput ? ghTokenInput.value.trim() : "";
                    const reviewer = (ghReviewerNameInput && ghReviewerNameInput.value.trim()) ? ghReviewerNameInput.value.trim() : 'Reviewer';
                    const count = Object.keys(critiques).length;
                    if (!token) {{
                        alert("Please enter your GitHub token to submit.");
                        return;
                    }}

                    localStorage.setItem('dnd_scribe_gh_token', token);
                    localStorage.setItem('dnd_scribe_reviewer_name', reviewer);

                    if (ghStatusMsg) {{
                        ghStatusMsg.className = "p-2.5 rounded-lg text-xs bg-sky-950/60 border border-sky-800 text-sky-300 block";
                        ghStatusMsg.textContent = "⏳ Contacting GitHub API to create critique branch...";
                    }}
                    ghSubmitPrBtn.disabled = true;

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
                        exportedAt: new Date().toISOString(),
                        totalCritiques: count,
                        critiques: Object.values(critiques)
                    }};

                    const markdownRows = Object.values(critiques).map(c => 
                        "| `" + c.blockId + "` | **" + c.speaker + "** | `" + c.category + "` | " + c.comment.replace(/\\|/g, '\\\\|') + " | " + (c.suggestedRewrite ? c.suggestedRewrite.replace(/\\|/g, '\\\\|') : '-') + " |"
                    ).join('\\n');

                    const prBody = "## 📝 Story Critique Batch: " + exportPayload.title + "\\n**Reviewer:** " + reviewer + "\\n**Total Notes:** " + count + "\\n\\n### 📋 Critique Items Table\\n| Block ID | Speaker | Category | Critique / Directive | Suggested Rewrite |\\n|---|---|---|---|---|\\n" + markdownRows + "\\n\\n<details>\\n<summary><b>📦 Raw JSON Payload (for Agent Ingestion)</b></summary>\\n\\n```json\\n" + JSON.stringify(exportPayload, null, 2) + "\\n```\\n</details>";

                    try {{
                        const headers = {{
                            "Authorization": "Bearer " + token,
                            "Accept": "application/vnd.github+json",
                            "Content-Type": "application/json"
                        }};

                        let baseRefRes = await fetch("https://api.github.com/repos/" + REPO + "/git/ref/heads/" + BASE_BRANCH, {{ headers }});
                        if (!baseRefRes.ok) baseRefRes = await fetch("https://api.github.com/repos/" + REPO + "/git/ref/heads/main", {{ headers }});
                        if (!baseRefRes.ok) throw new Error("Could not find base branch on GitHub repo: " + baseRefRes.statusText);
                        const baseSha = (await baseRefRes.json()).object.sha;

                        if (ghStatusMsg) ghStatusMsg.textContent = "⏳ Creating review branch: " + NEW_BRANCH;
                        const createBranchRes = await fetch("https://api.github.com/repos/" + REPO + "/git/refs", {{
                            method: "POST",
                            headers: headers,
                            body: JSON.stringify({{ ref: "refs/heads/" + NEW_BRANCH, sha: baseSha }})
                        }});
                        if (!createBranchRes.ok) throw new Error("Failed to create critique branch: " + (await createBranchRes.text()));

                        if (ghStatusMsg) ghStatusMsg.textContent = "⏳ Committing critique JSON payload...";
                        const filePath = "sessions/data/critiques/" + CAMPAIGN_ID + "-" + CHAPTER_ID + "-" + safeName + "-" + timestamp + ".json";
                        const contentBase64 = btoa(unescape(encodeURIComponent(JSON.stringify(exportPayload, null, 2))));
                        const commitRes = await fetch("https://api.github.com/repos/" + REPO + "/contents/" + filePath, {{
                            method: "PUT",
                            headers: headers,
                            body: JSON.stringify({{ message: "critique: " + reviewer + " review for " + CAMPAIGN_ID + " " + CHAPTER_ID, content: contentBase64, branch: NEW_BRANCH }})
                        }});
                        if (!commitRes.ok) throw new Error("Failed to commit critique file: " + (await commitRes.text()));

                        if (ghStatusMsg) ghStatusMsg.textContent = "⏳ Opening Pull Request on GitHub...";
                        const prRes = await fetch("https://api.github.com/repos/" + REPO + "/pulls", {{
                            method: "POST",
                            headers: headers,
                            body: JSON.stringify({{ title: "📝 Review: " + CAMPAIGN_ID.toUpperCase() + " " + CHAPTER_ID.toUpperCase() + " by " + reviewer, head: NEW_BRANCH, base: BASE_BRANCH, body: prBody }})
                        }});
                        if (!prRes.ok) throw new Error("Failed to open Pull Request: " + (await prRes.text()));
                        const prData = await prRes.json();

                        if (ghStatusMsg) {{
                            ghStatusMsg.className = "p-2.5 rounded-lg text-xs bg-emerald-950/70 border border-emerald-700 text-emerald-300 block";
                            ghStatusMsg.innerHTML = '🎉 <strong>PR Opened Successfully!</strong><br><a href="' + prData.html_url + '" target="_blank" class="underline font-bold text-amber-300">View Pull Request #' + prData.number + '</a>';
                        }}
                    }} catch (err) {{
                        if (ghStatusMsg) {{
                            ghStatusMsg.className = "p-2.5 rounded-lg text-xs bg-rose-950/70 border border-rose-700 text-rose-300 block";
                            ghStatusMsg.textContent = "❌ Error: " + err.message;
                        }}
                    }} finally {{
                        ghSubmitPrBtn.disabled = false;
                    }}
                }};
            }}

            if (footerExportBtn) footerExportBtn.onclick = showGhModal;
            if (clearCritiquesBtn) {{
                clearCritiquesBtn.onclick = function() {{
                    if (confirm("Are you sure you want to clear all review notes for this session?")) {{
                        critiques = {{}};
                        try {{ localStorage.removeItem(STORAGE_KEY); }} catch(e) {{}}
                        refreshMarkers();
                    }}
                }};
            }}

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
