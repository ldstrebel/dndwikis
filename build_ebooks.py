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

def generate_html_for_session(manifest_path: Path, output_path: Path):
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    campaign = data.get("campaign", {})
    session = data.get("session", {})
    characters = data.get("characters", {})
    stats = data.get("stats", {})
    blocks = data.get("blocks", [])

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

        /* Overlay Transitions & Viewport Sizing */
        #chaptersModalOverlay, #critiqueModalOverlay, #ghModalOverlay, #onboardingModalOverlay {{
            transition: opacity 0.25s ease, backdrop-filter 0.25s ease;
            height: 100vh;
            height: 100dvh;
        }}
        #chaptersModalOverlay.visible, #critiqueModalOverlay.visible {{
            opacity: 1;
            pointer-events: auto;
        }}

        #chaptersModalCard, #critiqueBottomSheet {{
            transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.2s ease, max-height 0.2s ease;
            transform: scale(0.96) translateY(-10px);
            opacity: 0;
            max-height: min(88vh, 88dvh);
        }}
        #chaptersModalOverlay.visible #chaptersModalCard,
        #critiqueModalOverlay.visible #critiqueBottomSheet {{
            transform: scale(1) translateY(0);
            opacity: 1;
        }}

        @media (max-width: 640px) {{
            #critiqueModalOverlay {{
                align-items: flex-start !important;
                padding-top: 0.75rem !important;
                padding-bottom: 0.75rem !important;
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
    </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen pb-24 mode-critique">

    <!-- STICKY TOP APP BAR (Clean & Content-Focused with Minimal Reading Progress) -->
    <header class="sticky top-0 z-40 bg-slate-900/95 backdrop-blur-md border-b border-slate-800">
        <div class="max-w-4xl mx-auto flex items-center justify-between gap-3 px-4 py-2.5">
            <div class="flex items-center gap-2.5 min-w-0">
                <a href="index.html?c={campaign_id}" class="text-slate-400 hover:text-amber-400 transition-colors flex items-center text-xs sm:text-sm font-semibold gap-1 py-1 px-1.5 -ml-1.5 rounded-lg hover:bg-slate-800/60" title="Back to {campaign_name} Sessions">
                    <span>←</span> <span class="font-medium">Sessions</span>
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
                    <span>Chapters</span>
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

        <!-- Bottom Page Controls & Feedback Review Summary -->
        <footer class="mt-16 pt-8 border-t border-slate-800 text-center space-y-4">
            <div class="bg-slate-900/60 p-5 rounded-2xl border border-slate-800 max-w-md mx-auto shadow-lg">
                <div class="flex items-center justify-center gap-2 text-amber-400 mb-1">
                    <span class="text-lg">💬</span>
                    <h3 class="text-sm font-bold">Feedback & Review Notes</h3>
                </div>
                <p class="text-xs text-slate-400 mb-3">Review your collected notes, suggested rewrites, or submit feedback to the chronicle.</p>
                <div class="flex gap-2 justify-center">
                    <button id="footerExportBtn" type="button" class="px-5 py-2.5 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 text-slate-950 font-bold rounded-xl text-xs transition-all shadow-md flex items-center gap-1.5">
                        <span>📝</span> <span>Review Feedback</span>
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
                    <div class="grid grid-cols-3 sm:grid-cols-6 gap-1.5" id="categoryPillContainer">
                        <button type="button" class="category-pill active px-2 py-1.5 rounded-lg text-[11px] font-bold border border-amber-500 bg-amber-500/20 text-amber-300 text-center" data-category="general">General</button>
                        <button type="button" class="category-pill px-2 py-1.5 rounded-lg text-[11px] font-medium border border-slate-700 bg-slate-800 text-slate-300 text-center" data-category="tone">Tone / Voice</button>
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

    <!-- ========================================================= -->
    <!-- FIRST-TIME SESSION WELCOME & FEATURE TOUR MODAL -->
    <!-- ========================================================= -->
    <div id="onboardingModalOverlay" class="fixed inset-0 bg-slate-950/85 backdrop-blur-md z-50 flex items-center justify-center opacity-0 pointer-events-none p-4 transition-opacity duration-200">
        <div class="bg-slate-900 border border-amber-500/40 rounded-2xl max-w-md w-full p-5 sm:p-6 shadow-2xl space-y-4 text-left">
            <div class="flex items-center gap-3 border-b border-slate-800 pb-3">
                <div class="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-xl flex-shrink-0">
                    ✨
                </div>
                <div>
                    <h3 class="text-base font-bold text-slate-100 font-serif">Welcome to Session {session_num}</h3>
                    <p class="text-xs text-amber-400 font-mono">Interactive Reader & Critique Engine</p>
                </div>
            </div>

            <p class="text-xs text-slate-300 leading-relaxed">
                Here is a quick overview of what this interactive session offers:
            </p>

            <div class="space-y-2.5 text-xs text-slate-300">
                <!-- 1. Critique Mode & Interactive Toggle Matching Header -->
                <div class="bg-slate-950/70 p-3 rounded-xl border border-slate-800 space-y-2">
                    <div class="flex items-center justify-between gap-2">
                        <span class="font-bold text-amber-300 flex items-center gap-1.5 text-xs">
                            <span>✍️</span> <span>Reading & Critique Mode</span>
                        </span>
                        <!-- Interactive Toggle component matching Header -->
                        <div class="flex bg-slate-950 border border-slate-800 rounded-lg p-0.5 shadow-inner">
                            <button id="onboardingModeReaderBtn" type="button" class="px-2.5 py-1 rounded-md text-xs font-medium text-slate-400 hover:text-slate-200 transition-all flex items-center gap-1">
                                <span>📖</span> <span>Read</span>
                            </button>
                            <button id="onboardingModeCritiqueBtn" type="button" class="px-2.5 py-1 rounded-md text-xs font-bold text-slate-950 bg-amber-400 shadow transition-all flex items-center gap-1">
                                <span>✍️</span> <span>Critique</span>
                            </button>
                        </div>
                    </div>
                    <p id="onboardingModeDesc" class="text-[11px] text-slate-300 leading-normal bg-slate-900/60 p-2 rounded-lg border border-slate-800/80">
                        <strong>Critique Mode Active:</strong> Click or tap any passage to leave review notes, tone directives, or suggested rewrites.
                    </p>
                </div>

                <!-- 2. Chapters & Diagnostics -->
                <div class="bg-slate-950/70 p-3 rounded-xl border border-slate-800 space-y-1">
                    <div class="flex items-center justify-between">
                        <span class="font-bold text-indigo-300 flex items-center gap-1.5">
                            <span>📑</span> <span>Chapters & Session Stats</span>
                        </span>
                        <span class="text-[10px] text-slate-500 font-mono">Top Header</span>
                    </div>
                    <p class="text-[11px] text-slate-400 leading-normal">
                        Tap <strong>📑 Chapters</strong> anytime to jump to scenes, view dialogue shares per chapter, inspect character voice velocity curves, sensory registers, and campaign analytics.
                    </p>
                </div>

                <!-- 3. Reading Progress Bar -->
                <div class="bg-slate-950/70 p-3 rounded-xl border border-slate-800 space-y-1">
                    <div class="flex items-center justify-between">
                        <span class="font-bold text-emerald-300 flex items-center gap-1.5">
                            <span>📏</span> <span>Live Reading Progress</span>
                        </span>
                        <span class="text-[10px] text-slate-500 font-mono">Under Header</span>
                    </div>
                    <p class="text-[11px] text-slate-400 leading-normal">
                        The minimal blue bar directly beneath the top header tracks how far along you are in the story from start to finish.
                    </p>
                </div>
            </div>

            <button id="closeOnboardingBtn" type="button" class="w-full py-3 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 text-slate-950 font-bold rounded-xl text-xs transition-all shadow-lg shadow-amber-500/20 active:scale-98 flex items-center justify-center gap-1.5">
                <span>Start Reading Session {session_num}</span> <span>🚀</span>
            </button>
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
            let selectedCategory = "general";
            const blocks = Array.from(document.querySelectorAll('.story-block'));

            const chaptersModalOverlay = document.getElementById('chaptersModalOverlay');
            const toggleChaptersBtn = document.getElementById('toggleChaptersBtn');
            const closeChaptersModalBtn = document.getElementById('closeChaptersModalBtn');
            const toggleStatsAccordionBtn = document.getElementById('toggleStatsAccordionBtn');
            const statsAccordionBody = document.getElementById('statsAccordionBody');
            const statsAccordionChevron = document.getElementById('statsAccordionChevron');

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

            const onboardingOverlay = document.getElementById('onboardingModalOverlay');
            const closeOnboardingBtn = document.getElementById('closeOnboardingBtn');

            // Modal Background Scroll Lock Helper
            function setBodyScrollLock(locked) {{
                if (locked) {{
                    document.body.style.overflow = 'hidden';
                }} else {{
                    const isAnyModalOpen = (
                        (chaptersModalOverlay && chaptersModalOverlay.classList.contains('visible')) ||
                        (modalOverlay && modalOverlay.classList.contains('visible')) ||
                        (onboardingOverlay && onboardingOverlay.classList.contains('visible')) ||
                        (typeof ghModalOverlay !== 'undefined' && ghModalOverlay && !ghModalOverlay.classList.contains('opacity-0'))
                    );
                    if (!isAnyModalOpen) {{
                        document.body.style.overflow = '';
                    }}
                }}
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

                // Update breadcrumb pips per chapter
                const breadcrumbs = document.querySelectorAll('#readingProgressBreadcrumbs [data-pct]');
                breadcrumbs.forEach(dot => {{
                    const pct = parseFloat(dot.getAttribute('data-pct'));
                    const isTraversed = isComplete || (maxDepth >= pct);
                    
                    if (isTraversed) {{
                        if (isComplete) {{
                            // Finished: Exact interpolated Light Green -> Cyan Green color
                            const col = getCompletionGradientColor(pct);
                            dot.style.backgroundColor = col;
                            dot.style.boxShadow = '0 0 4px ' + col;
                            dot.style.opacity = '1';
                        }} else {{
                            // In-Progress: Exact interpolated Blue -> Sky -> Cyan color matching the bar at that point
                            const col = getReadingGradientColor(pct);
                            dot.style.backgroundColor = col;
                            dot.style.boxShadow = '0 0 4px ' + col;
                            dot.style.opacity = '0.95';
                        }}
                    }} else {{
                        dot.style.backgroundColor = 'rgba(71, 85, 105, 0.45)';
                        dot.style.boxShadow = 'none';
                        dot.style.opacity = '0.35';
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

            const onbModeReaderBtn = document.getElementById('onboardingModeReaderBtn');
            const onbModeCritiqueBtn = document.getElementById('onboardingModeCritiqueBtn');
            const onbModeDesc = document.getElementById('onboardingModeDesc');

            window.setReadingMode = function(mode) {{
                const isCritique = (mode === 'critique');
                if (isCritique) {{
                    document.body.classList.add('mode-critique');
                }} else {{
                    document.body.classList.remove('mode-critique');
                }}
                
                const activeBtnClass = "px-2.5 py-1 rounded-md text-xs font-bold text-slate-950 bg-amber-400 shadow transition-all flex items-center gap-1";
                const inactiveBtnClass = "px-2.5 py-1 rounded-md text-xs font-medium text-slate-400 hover:text-slate-200 transition-all flex items-center gap-1";

                if (modeReaderBtn && modeCritiqueBtn) {{
                    modeReaderBtn.className = !isCritique ? activeBtnClass : inactiveBtnClass;
                    modeCritiqueBtn.className = isCritique ? activeBtnClass : inactiveBtnClass;
                }}

                if (onbModeReaderBtn && onbModeCritiqueBtn) {{
                    onbModeReaderBtn.className = !isCritique ? activeBtnClass : inactiveBtnClass;
                    onbModeCritiqueBtn.className = isCritique ? activeBtnClass : inactiveBtnClass;
                }}

                if (onbModeDesc) {{
                    if (isCritique) {{
                        onbModeDesc.innerHTML = '<strong>Critique Mode Active:</strong> Click or tap any passage to leave review notes, tone directives, or suggested rewrites.';
                    }} else {{
                        onbModeDesc.innerHTML = '<strong>Read Mode Active:</strong> Story commenting is turned off for clean, uninterrupted reading flow.';
                    }}
                }}
            }};

            if (modeReaderBtn) modeReaderBtn.onclick = () => window.setReadingMode('read');
            if (modeCritiqueBtn) modeCritiqueBtn.onclick = () => window.setReadingMode('critique');
            if (onbModeReaderBtn) onbModeReaderBtn.onclick = () => window.setReadingMode('read');
            if (onbModeCritiqueBtn) onbModeCritiqueBtn.onclick = () => window.setReadingMode('critique');

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
                        modalOverlay,
                        chaptersModalOverlay,
                        onboardingOverlay,
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

                if (!comment && !rewrite) {{
                    alert("Please provide a critique note or suggested rewrite before saving.");
                    return;
                }}

                critiques[blockId] = {{
                    blockId: blockId,
                    blockIndex: activeBlockIndex + 1,
                    speaker: block.dataset.speakerName,
                    speakerColor: block.dataset.speakerColor || "#94a3b8",
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

                    return `
                        <div class="p-3 rounded-r-xl rounded-l-md border-y border-r border-slate-800 space-y-1.5 relative group shadow-sm transition-all" style="` + cardStyle + `">
                            <div class="flex items-center justify-between gap-2">
                                <div class="flex items-center gap-1.5 min-w-0">
                                    <span class="w-2 h-2 rounded-full flex-shrink-0" style="background-color: ` + spColor + `"></span>
                                    <span class="text-[10px] font-mono font-bold uppercase truncate" style="color: ` + spColor + `">#` + (c.blockIndex || (idx + 1)) + ` ` + (c.speaker || 'Narrator') + `</span>
                                    <span class="text-[9px] px-1.5 py-0.2 rounded bg-slate-950/80 text-slate-300 border border-slate-700/60 font-mono uppercase font-semibold">` + (c.category || 'General') + `</span>
                                </div>
                                <button type="button" class="text-slate-500 hover:text-rose-400 text-xs p-1 transition-colors" title="Delete this note" onclick="window.deleteCritiqueItem('` + c.blockId + `')">
                                    🗑️
                                </button>
                            </div>
                            ` + (c.quote ? `<p class="text-[11px] text-slate-300 italic line-clamp-2 pl-0.5">"` + c.quote + `"</p>` : '') + `
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

                    const markdownRows = Object.values(critiques).map(c => 
                        "| `" + c.blockId + "` | **" + c.speaker + "** | `" + c.category + "` | " + (c.comment || '').replace(/\\|/g, '\\\\|') + " | " + (c.suggestedRewrite ? c.suggestedRewrite.replace(/\\|/g, '\\\\|') : '-') + " |"
                    ).join('\\n');

                    let reviewerSection = "**Reviewer:** `" + reviewer + "`";
                    if (isBankName && replacementName) {{
                        reviewerSection += " *(🎲 D&D Pun Handle)*\\n**Next Pool Replacement Suggestion:** `" + replacementName + "` 🎲";
                    }}

                    const prBody = "## 📝 Story Feedback: " + exportPayload.title + "\\n" + reviewerSection + "\\n**Total Notes:** " + count + "\\n\\n### 📋 Feedback Items Table\\n| Block ID | Speaker | Category | Critique / Directive | Suggested Rewrite |\\n|---|---|---|---|---|\\n" + markdownRows + "\\n\\n<details>\\n<summary><b>📦 Raw JSON Payload (for Agent Ingestion)</b></summary>\\n\\n```json\\n" + JSON.stringify(exportPayload, null, 2) + "\\n```\\n</details>";

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
