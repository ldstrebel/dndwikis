# D&D Wikis — Frontend Component Architecture & Standards

> **Guide for UI Contributors**: This document details the component architecture, visual design tokens, interaction lifecycles, and hard-won lessons learned across the D&D Wikis front-end reading applications.

---

## 🎨 Design Tokens & Theme Palettes

The reader applications are dark-mode first, optimized for OLED displays and low-light reading comfort:

### Surface & Background Tokens
* **Base Viewport Background**: `#0b0f19` (Deep Obsidian / Midnight Slate)
* **Card & Inspector Surface**: `bg-slate-900` (`#0f172a`) with borders in `border-slate-800` (`#1e293b`)
* **Modal Overlay Backdrops**: `bg-slate-950/85` with `backdrop-blur-sm` or `backdrop-blur-md`
* **Accent Gold / Amber**: `text-amber-400`, `bg-amber-500/20`, `border-amber-500/50` (Primary interactive highlights)

### Character & Voice Palette
Every character in the story receives a consistent, high-contrast color token:
* 🟣 **Prof. Edward Dravin**: `#8b5cf6` (Amethyst Purple)
* 🔵 **Pierre**: `#38bdf8` (Sky Blue)
* 🟡 **Alfie**: `#eab308` (Topaz Gold)
* 🟢 **Eusacles**: `#22c55e` (Emerald Green)
* 🔴 **Named NPCs (Fates, Nincy, Mike, Rosa, etc.)**: `#f87171` (Coral Crimson)
* ⚪ **Narrator / Scene Context**: `#94a3b8` (Slate Muted Grey)

---

## 🧩 Core Component Catalog

### 1. The "Hot Dog" Diff Inspector
* **Element ID**: `#diffInspectorOverlay`
* **Layout Mechanics**: 50/50 vertical side-by-side split (`flex-col md:flex-row`).
* **Why "Hot Dog" Won**:
  * During user testing, horizontal splitting ("Hamburger") required excessive vertical scrolling and constantly hid the prose when comparing against long transcripts.
  * The vertical 50/50 layout allows a reader or editor to view the adapted prose on the left and the raw tabletop dialogue on the right simultaneously.
* **Synchronized Scrolling & Accordions**:
  * If a single narrative paragraph represents multiple spoken lines, the lines are bundled into a clean accordion container with a tactile expander (`▼ Expand X table lines`).
  * Expanding an accordion automatically preserves scroll alignment.
* **Narrative Synthesis Indicator**:
  * Passages that bridge tabletop action or establish setting transitions without a 1:1 spoken quote are tagged with a purple badge:
    `[🔮 Narrative Synthesis · Scene Context]`
  * **Rule**: Never fall back to the previous line number. Explicitly tag synthesized passages.

---

### 2. Chapters & Voice Velocity Modal
* **Element ID**: `#chaptersModalOverlay`
* **Trigger**: Top sticky bar button: `📑 Chapters`
* **Anatomy**:
  1. **Header**: Clean back arrow (`←`) and tactile close button (`✕`).
  2. **Voice Velocity Breakdown**: A stacked horizontal bar chart displaying proportional spoken dialogue share across all party members and active NPCs.
  3. **Vertical Chapter List (Y-Axis)**:
     * Distinct novel chapters with scene range badges.
     * Active named NPC tags (`#f87171`) highlighting guest appearances in that chapter.
     * Tapping any chapter executes a smooth scroll directly to the corresponding DOM element and dismisses the modal.

---

### 3. Mobile Passage Critique Sheet
* **Element ID**: `#critiqueModalOverlay`
* **Design**: Bottom sheet on mobile viewports (`max-h-[85vh]`), centered dialog on desktop.
* **Layering**: Always assigned `z-[60]` (elevated strictly above the `z-50` Diff Inspector).
* **Capabilities**:
  * **Speaker Re-Attribution Select**: Instant dropdown to reassign the passage to any PC, named NPC, or Narrator.
  * **Critique Categorizer**: Chips for `General`, `Hallucination`, `Dialogue Drift`, `Pacing`, `Audio/TTS`.
  * **Suggested Rewrite Field**: Multi-line editor for proposing direct prose adjustments.
  * **Navigation Arrows**: `< Prev` and `Next >` buttons to step through sequential passages without returning to the root text.

---

### 4. Zero-Backend GitHub PR Pipeline
* **Trigger**: `ghSubmitPrBtn.onclick`
* **Authentication Mechanics**:
  * Zero servers, zero serverless functions, zero user OAuth logins.
  * Uses the browser's native `window.crypto.subtle` Web Crypto API:
    1. Imports the PKCS8 private key of the GitHub App (`BOT_APP_ID: 4866708`).
    2. Signs an RS256 JWT valid for 500 seconds.
    3. Requests an ephemeral installation access token from `https://api.github.com/app/installations/{BOT_INSTALLATION_ID}/access_tokens`.
    4. Creates a new review branch on `ldstrebel/dnd-scribe` (`critique/{campaign}-{chapter}-{reviewer}-{timestamp}`).
    5. Commits the JSON payload to `sessions/data/critiques/`.
    6. Opens a formal Pull Request against `base: uneraseable`.

---

## 📐 Modal Layering Architecture (Strict Contract)

To prevent z-index wars and UI traps, all overlays adhere to a strict numeric hierarchy:

```text
┌─────────────────────────────────────────────────────────────┐
│ Level 4: GitHub PR Submission Modal (z-[70])               │
├─────────────────────────────────────────────────────────────┤
│ Level 3: Passage Critique Sheet Modal (z-[60])              │
├─────────────────────────────────────────────────────────────┤
│ Level 2: Diff Inspector / Chapters Overlay (z-50)           │
├─────────────────────────────────────────────────────────────┤
│ Level 1: Sticky Top Bar & Progress Trackers (z-40)          │
├─────────────────────────────────────────────────────────────┤
│ Level 0: Main Novel Prose / Text Stream                     │
└─────────────────────────────────────────────────────────────┘
```

### Escape Key & Dismissal Rules
* Modals maintain a virtual stack. Pressing <kbd>Esc</kbd> pops only the topmost visible modal.
* **Do NOT close the Diff Inspector when opening feedback**: The critique modal must layer on top (`openedFromDiff = true`). Closing the feedback modal restores focus directly back to the Diff Inspector.

---

## 🚫 Hard-Won Anti-Patterns & Gotchas

1. **Avoid Line Fallback Cascading**:
   * *The Pitfall*: If a block has no explicit line number, never inherit `last_line_num`. In early builds, this caused Pierre's quote from Line 987 to appear on 25 unrelated narrator paragraphs.
   * *The Standard*: Use `primary_line = None` and render `[🔮 Narrative Synthesis · Scene Context]`.
2. **Mobile Touch Target Minimums**:
   * *The Pitfall*: Buttons with `w-8 h-8` or placed flush against screen edges become impossible to tap on iPhones and notch screens.
   * *The Standard*: All interactive controls must satisfy Apple and Android touch guidelines: $\ge 44\text{px}$ hit areas (`min-h-[44px]`, `w-11 h-11`), styled with generous padding (`p-2.5` or `p-3`).
3. **Avoid Client-Side Direct Slack Webhooks**:
   * *The Pitfall*: Calling `fetch('https://hooks.slack.com/...')` from browser JavaScript causes CORS rejection errors.
   * *The Standard*: The browser creates the PR via the GitHub App token; GitHub Actions on Ubuntu runners (`.github/workflows/pr-slack-alert.yml`) dispatches the Slack alert cleanly.

---

## 🧪 How to Prototype & Experiment Safely

If you want to experiment with a new component (e.g. an audio-scrubbing waveform or a multi-panel visual comic viewer):

1. **Create an Isolated Sandbox File**:
   * Copy an existing build output (e.g. `cp uneraseable-s1.html sandbox-reader.html`).
   * Test your new CSS or JavaScript interactions directly in `sandbox-reader.html`.
2. **Verify Non-Interference**:
   * Verify that your changes do not break `critiqueModalOverlay` or GitHub token signing.
   * Run Node syntax verification:
     ```powershell
     node scratch/verify_script_syntax.js
     ```
3. **Upstream into `build_ebooks.py`**:
   * Once proven in the sandbox, incorporate the component template into `build_ebooks.py` so all sessions benefit automatically.
