# D&D Wikis — The Living Campaign Portal

> **Interactive Web Publishing for Tabletop Roleplaying Campaigns**: Transforming raw tabletop audio, live gameplay transcripts, and graphic storyboards into polished, auditable web novellas and digital graphic novels.

🌐 **Live Production Site**: [https://ldstrebel.github.io/dndwikis/](https://ldstrebel.github.io/dndwikis/)

---

## 🧭 Master Documentation Sitemap

| Guide | Description | Target Audience |
| :--- | :--- | :--- |
| 🚀 **[CONTRIBUTING.md](CONTRIBUTING.md)** | Step-by-step guide to publishing new chapters, building reader files, and running the pipeline. | Authors, Scribes & Editors |
| 📚 **[SESSIONS_INDEX.md](SESSIONS_INDEX.md)** | Catalog of all 5 tested session UX formats (Interactive Readers, Webtoon Strips, Multi-Session Arcs, Dashboards). | UI Developers & Storytellers |
| 🎨 **[FRONTEND_COMPONENTS.md](FRONTEND_COMPONENTS.md)** | Component catalog, design tokens, character color keys, and proven UX rules vs. anti-patterns. | Frontend Engineers |

---

## 🌟 Platform Highlights

### 1. Interactive Novelization Reader (Schema 2.0)
* **The "Hot Dog" Diff Inspector**: Side-by-side vertical view that synchronizes narrative prose against verbatim tabletop audio transcripts.
* **Chapters & Voice Velocity**: Live character voice breakdown per chapter, highlighting active named NPCs (`#f87171`) and PC dialogue shares.
* **Passage Critique Modal**: In-browser feedback sheet allowing readers and editors to submit rewrites, dialogue notes, or speaker re-attributions.
* **Zero-Backend GitHub PR Pipeline**: Uses the browser's Web Crypto API to sign JWTs for a GitHub App, committing structured critique payloads directly to upstream repositories without requiring user logins.

### 2. Seamless Webtoon Strips
* Infinite vertical scroll format with 0px image gaps, compact 480px responsive viewports, and interactive Tailwind narrative cards.

---

## 📖 Active Campaigns Showcase

### 1. Uneraseable *(Sci-Fi / Post-Apocalyptic / Mythic Mystery)*
*Displaced from reality into the timeless haven of The Margin, four strangers race across severed timeline seams to recover stolen fate epigraphy.*
* **Format**: Schema 2.0 Interactive Novel Reader
* **Available Sessions**:
  * [Session 1: The Bus From Vegas & The Library of the Fates](uneraseable-s1.html)
  * [Session 2: The Margin, The Fragments & The Lost Roads](uneraseable-s2.html)
  * [Session 3: The Museum Heist in North Carolina](uneraseable-s3.html)
  * [Session 4: The Medusa Protocol & The Raleigh Redactors](uneraseable-s4.html)

### 2. Vumbua *(Steampunk / Fantasy Academy)*
*A sprawling graphic narrative detailing the trials, tribulations, and adventures of students at the prestigious Vumbua Academy across Sessions 0 to 12.*
* **Format**: Seamless Webtoon Strips & Prose Arcs
* **Key Sessions**:
  * [Session 8: Squad 907 (Webtoon Strip)](vumbua-s8.html)
  * [Session 9: Five Sectors (Webtoon Strip)](vumbua-s9.html)
  * [Session 10: Dagger Sharks (Webtoon Strip)](vumbua-s10.html)
  * [Sessions 1–6 Omnibus Archive](vumbua-s1-6.html)
  * [Session 12: The Origins](clan-origins.html)

### 3. Classic Tabletop Archives
* **The Chronicles of Meryl**: Fantasy adventure ([meryl1.html](meryl1.html), [meryl2.html](meryl2.html))
* **Sigmar’s Heirs**: Warhammer Fantasy RPG ([sigmar1-9.html](sigmar1-9.html), [sigmar-ch10.html](sigmar-ch10.html))
* **Dungeon Crawlers**: Sci-Fi LitRPG ([dc-ch1.html](dc-ch1.html))
* **Verdant Scar**: High fantasy ([vs-ch1.html](vs-ch1.html))

---

## ⚙️ Quick Start: How to Build & Publish

```powershell
# 1. Ensure upstream data is ready in dnd-scribe
cd D:\Code\dnd-scribe
python sessions/_scripts/generate_web_manifest.py sN

# 2. Build interactive reader files
cd D:\Code\dndwikis-main\dndwikis-main
python build_ebooks.py

# 3. Commit and push to publish on GitHub Pages
git add uneraseable-sN.html index.html
git commit -m "feat(reader): publish Session N"
git push origin main
```
*For detailed instructions, see [CONTRIBUTING.md](CONTRIBUTING.md).*

---

## 🔗 Upstream Repository
This web publishing portal is fed by the canon transcription, parity auditing, and editorial pipeline in:
* **Repository**: [`ldstrebel/dnd-scribe`](https://github.com/ldstrebel/dnd-scribe)

---

## 📄 License
© All original campaign content, worldbuilding lore, character concepts, and stories are the property of their respective creators. Code and reader components are distributed for platform publication.
