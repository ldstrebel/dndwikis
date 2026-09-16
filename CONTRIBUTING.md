# Contributing to D&D Wikis

> **The Turn-Key Contributor Guide**: Everything you need to know to publish a new story session, build the interactive readers, or experiment with novel front-end components across the D&D Wikis ecosystem.

---

## 🏛️ The Two-Repository Architecture

The D&D Wikis reading platform operates across two interconnected repositories:

```text
┌─────────────────────────────────────────────────────────────┐
│ 1. Upstream Canon & Scribe Pipeline: ldstrebel/dnd-scribe    │
│    • Raw audio recordings & Whisper/diarization transcripts │
│    • Parity ledgers & forensic semantic grounding checks    │
│    • Schema 2.0 Web Manifests (sessions/data/index/*.json)  │
│    • Critique ingestion & retcon tracking                   │
└──────────────────────────────┬──────────────────────────────┘
                               │
                Compiles via   │ build_ebooks.py
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Web Publishing & Presentation: ldstrebel/dndwikis        │
│    • Interactive HTML Reader applications (uneraseable-*.html)
│    • Zero-backend GitHub App review PR dispatcher           │
│    • Webtoon and multi-session graphic readers               │
│    • Hosted globally via GitHub Pages (live production)      │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Publishing a New Session (Step-by-Step)

Follow this process whenever a new session has been transcribed and verified in `dnd-scribe`:

### Step 1: Confirm Upstream Readiness in `dnd-scribe`
Ensure the session has passed its forensic grounding and manifest generation:
```powershell
cd D:\Code\dnd-scribe
python sessions/_scripts/audit_semantic_grounding.py sN
python sessions/_scripts/generate_web_manifest.py sN
```
Verify that `sessions/data/index/sN-manifest-v2.json` exists and is populated with blocks.

### Step 2: Compile the Interactive Reader in `dndwikis`
Navigate to the `dndwikis` directory and run the compiler:
```powershell
cd D:\Code\dndwikis-main\dndwikis-main
python build_ebooks.py
```
The compiler will:
* Detect the GitHub App secret key (`dnd-scribe-bot.*.pem`).
* Parse the Schema 2.0 manifest from `dnd-scribe`.
* Generate a standalone, production-ready `uneraseable-sN.html`.

### Step 3: Run Script Syntax Validation
Run the static JavaScript validator to ensure zero syntax or bundling errors:
```powershell
node -e "
const fs = require('fs');
const acorn = require('acorn');
// Inspect generated script blocks
console.log('Validating inline scripts...');
"
```
*(Or run your local scratch syntax checker).*

### Step 4: Link the Session in `index.html`
Open [`index.html`](file:///d:/Code/dndwikis-main/dndwikis-main/index.html) and add the new session to the `data-chapters` JSON attribute of the corresponding campaign card:
```html
<article class="campaign-card"
    data-campaign-title="Uneraseable"
    data-chapters='[
        {"title": "Session 1: The Bus From Vegas", "url": "uneraseable-s1.html"},
        {"title": "Session 2: The Margin & Lost Roads", "url": "uneraseable-s2.html"},
        {"title": "Session 3: The Museum Heist", "url": "uneraseable-s3.html"},
        {"title": "Session 4: Your New Chapter", "url": "uneraseable-s4.html"}
    ]'>
```

### Step 5: Commit and Deploy
Commit the generated HTML and updated homepage:
```powershell
git add uneraseable-sN.html index.html
git commit -m "feat(reader): publish Session N interactive reader"
git push origin main
```
GitHub Pages automatically deploys the updated story within 60 seconds.

---

## 🧪 Developing New Front-End Components

If you are prototyping a new reading layout, audio visualizer, or navigation model:

1. **Review Existing Formats First**: Read [`SESSIONS_INDEX.md`](SESSIONS_INDEX.md) to see if an existing pattern already solves your need.
2. **Follow the Component Standards**: Read [`FRONTEND_COMPONENTS.md`](FRONTEND_COMPONENTS.md) for design tokens, touch target minimums ($\ge 44\text{px}$), and the strict modal z-index hierarchy (`z-50` $\rightarrow$ `z-[60]` $\rightarrow$ `z-[70]`).
3. **Use a Sandbox File**: Never test unverified experimental markup directly in `build_ebooks.py`. Create `sandbox-reader.html` to experiment and test on real mobile viewports first.

---

## 🔐 Credentials & Secrets Handling

* **Bot Private Key**: The GitHub App private key (`.pem`) and `app_config.json` should reside in a local `.secrets/` directory (gitignored in both repositories).
* **Push Protection**: Never commit raw webhook URLs or private RSA keys to git. Webhooks should be base64-encoded or handled by GitHub Actions runners.
