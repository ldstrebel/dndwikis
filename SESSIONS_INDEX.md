# D&D Wikis — Master Session Formats Index

> **Quick Reference Catalog**: This index catalogs every distinct front-end reading format built and tested across the D&D Wikis platform. Use this matrix to select the right UX pattern for new campaigns, explore existing implementations, and avoid reinventing established components.

---

## 🧭 Format Comparison Matrix

| Format Paradigm | Primary Reference Files | Primary Build Tool | Key User Experience | Mobile Ergonomics |
| :--- | :--- | :--- | :--- | :--- |
| **1. Interactive Novel Reader (Schema 2.0)** | `uneraseable-s1.html`<br>`uneraseable-s2.html`<br>`uneraseable-s3.html` | `build_ebooks.py` | Full novelization with "Hot Dog" Diff Inspector, Voice Velocity bars, passage critique sheet, and zero-backend GitHub PR submissions. | Optimized; touch targets $\ge 44\text{px}$, sticky top/bottom bars, layered bottom sheets. |
| **2. Seamless Webtoon Strip (Graphic Comic)** | `vumbua-s8.html`<br>`vumbua-s9.html`<br>`vumbua-s10.html` | Static HTML / Art Pipeline | Continuous vertical image scrolling (0px gap), compact 480px width, expandable transcript narrative cards. | Excellent for phones; thumb-driven continuous vertical scroll. |
| **3. Multi-Session Prose Arc Reader** | `vumbua-s1-6.html`<br>`vumbua-s7.html`<br>`session11.html`<br>`session12.html` | Static HTML / Markdown | Long-form novel manuscript reading with scene break anchors, character dossiers, and clean typography. | Standard reading flow; responsive margins and fluid font sizing. |
| **4. Reviewer & Analytics Dashboard** | `super-secret-stats.html` | Static HTML / `traffic-tracker.js` | Local device review log, reading velocity graphs, completion funnels, and Slack webhook diagnostic tools. | Fully responsive grid with collapsible panels. |
| **5. Legacy Slideshow / Card View** | `chpt-html-template.html`<br>`vs-ch1.html`<br>`dc-ch1.html` | Template-based | Slide-by-slide horizontal stepping with d20 dice loading animation and keyboard shortcuts. | Card-based; requires explicit next/prev tapping. |

---

## 1. Interactive Schema 2.0 Novel Reader (Flagship)

* **Reference Implementation**: [`uneraseable-s1.html`](file:///d:/Code/dndwikis-main/dndwikis-main/uneraseable-s1.html), [`uneraseable-s2.html`](file:///d:/Code/dndwikis-main/dndwikis-main/uneraseable-s2.html), [`uneraseable-s3.html`](file:///d:/Code/dndwikis-main/dndwikis-main/uneraseable-s3.html)
* **Compiler**: [`build_ebooks.py`](file:///d:/Code/dndwikis-main/dndwikis-main/build_ebooks.py)
* **Data Contract**: Consumes `sN-manifest-v2.json` and `sN-clean-story.md` from `dnd-scribe/sessions/data/index/`.

### Core Features
1. **"Hot Dog" Diff Inspector**:
   - A 50/50 vertical side-by-side split that reveals the exact raw tabletop audio transcript corresponding to any selected story passage.
   - Synchronized scrolling between narrative prose (left/top) and spoken tabletop lines (right/bottom).
   - Clustered transcript blocks collapse into expandable accordions to maintain reading rhythm.
   - Clearly flags `[🔮 Narrative Synthesis · Scene Context]` when narrative prose bridges table action without a 1:1 spoken dialogue quote.
2. **Chapters & Voice Velocity Modal**:
   - Triggered via sticky header `📑 Chapters`.
   - Features a vertical Y-axis chapter list and an X-axis horizontal stacked bar illustrating real-time character voice share percentages per chapter.
   - Named NPCs highlighted in red (`#f87171`); PCs highlighted in distinctive character palette chips.
   - Tap-to-jump automatically scrolls to the chapter and dismisses the modal.
3. **Passage Critique & Re-Attribution Modal**:
   - Reviewers can tap any passage to suggest rewrites, flag dialogue inaccuracies, or re-attribute misidentified speakers.
   - Fully decoupled modal layering (`diffInspectorOverlay` at `z-50`, `critiqueModalOverlay` at `z-[60]`) so opening feedback never closes or resets the Diff Inspector.
4. **Zero-Backend GitHub PR Pipeline**:
   - Embedded Web Crypto API (`RSASSA-PKCS1-v1_5`) mints an ephemeral installation token via GitHub App (`BOT_APP_ID: 4866708`).
   - Commits structured JSON feedback directly to `sessions/data/critiques/` on `ldstrebel/dnd-scribe` and opens a PR without requiring user GitHub accounts.

### When to Choose This Format
* For any campaign where **canonical transcript fidelity**, **editorial feedback**, or **multi-voice audio synthesis** is required.

---

## 2. Seamless Webtoon Strip (Graphic Comic)

* **Reference Implementation**: [`vumbua-s8.html`](file:///d:/Code/dndwikis-main/dndwikis-main/vumbua-s8.html), [`vumbua-s9.html`](file:///d:/Code/dndwikis-main/dndwikis-main/vumbua-s9.html), [`vumbua-s10.html`](file:///d:/Code/dndwikis-main/dndwikis-main/vumbua-s10.html)
* **Visual Style**: Webtoon / Manhwa vertical infinite scroll.

### Core Features
1. **Seamless 0px Panel Flow**:
   - Images styled with `display: block; width: 100%; margin: 0; padding: 0; line-height: 0;` inside a constrained `max-w-[480px]` container.
   - Eliminates gaps between sequential comic panels for continuous narrative immersion.
2. **Contextual Narrative Overlays**:
   - Tapping or scrolling past panels reveals translucent Tailwind narrative cards (`bg-slate-950/95 backdrop-blur-md border-slate-800`).
   - Pairs artwork with scene transcription, GM descriptions, and character dialogue.
3. **Web Share & Chapter Nav**:
   - Native navigator share sheet integration with fallback clipboard copying.

### When to Choose This Format
* For visual/illustrated sessions where image artwork drives the storytelling.

---

## 3. Multi-Session Prose Arc Reader

* **Reference Implementation**: [`vumbua-s1-6.html`](file:///d:/Code/dndwikis-main/dndwikis-main/vumbua-s1-6.html), [`vumbua-s7.html`](file:///d:/Code/dndwikis-main/dndwikis-main/vumbua-s7.html), [`session11.html`](file:///d:/Code/dndwikis-main/dndwikis-main/session11.html), [`session12.html`](file:///d:/Code/dndwikis-main/dndwikis-main/session12.html)
* **Visual Style**: Clean, modern digital novella.

### Core Features
1. **Continuous Reading Layout**:
   - Generous line height and typography tuned for prolonged reading sessions.
   - Built-in chapter index markers (`#ch1`, `#ch2`) allowing deep-linking directly into scene climaxes.
2. **Audio Transcript Collapsibles**:
   - Optional `<details>` accordion blocks housing raw tabletop audio transcripts for readers who want behind-the-scenes dice roll context.

### When to Choose This Format
* For multi-session compilation digests, character backstory novellas, and worldbuilding lore archives.

---

## 4. Reviewer & Analytics Dashboard

* **Reference Implementation**: [`super-secret-stats.html`](file:///d:/Code/dndwikis-main/dndwikis-main/super-secret-stats.html)
* **Engine**: [`traffic-tracker.js`](file:///d:/Code/dndwikis-main/dndwikis-main/traffic-tracker.js)

### Core Features
1. **Local Review Mode**:
   - Inspects `localStorage` across reading sessions on the current device to display pending feedback notes, draft critiques, and export statuses.
2. **Reading Depth & Completion Velocity**:
   - Visual progress bars showing scroll depth (e.g. 100% completion sentinels) across each session chapter.
3. **Slack Diagnostic Dispatcher**:
   - Interactive testing button to verify webhook alert health and check payload formatting.

---

## 5. Legacy Slideshow / Card View

* **Reference Implementation**: [`chpt-html-template.html`](file:///d:/Code/dndwikis-main/dndwikis-main/chpt-html-template.html), [`vs-ch1.html`](file:///d:/Code/dndwikis-main/dndwikis-main/vs-ch1.html), [`dc-ch1.html`](file:///d:/Code/dndwikis-main/dndwikis-main/dc-ch1.html)
* **Visual Style**: Tarot card / Slide presentation.

### Core Features
1. **Slide-by-Slide Navigation**:
   - Sequential `<div class="slide hidden">` nodes navigated via previous/next controls or arrow keys.
2. **D20 Loading Animations**:
   - Thematic SVG/GIF dice transitions between scene views.
