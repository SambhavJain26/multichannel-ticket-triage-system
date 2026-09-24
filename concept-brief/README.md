# Automation Concept Brief — Reusable HTML/CSS Template Kit

**Brand:** Sambhav Builds / Automation Concept  
**Audience:** Property Management Decision-Makers (Founders, Principals, VP/Directors of Operations)  
**Format:** 3-Page Executive PDF (US Letter: `8.5in` × `11in`)  
**Design Identity:** Modern SaaS Product Design × Systems Architecture × Boutique Consulting Presentation  

---

## 1. Overview & Strategy

The **Automation Concept Brief** is a high-leverage client-facing document offered as **free upfront value** during cold outreach to property management executives.

### The Two Strategic Goals
A busy property management executive skimming this document for **30–60 seconds** should walk away thinking:
1. **“I understand exactly what outcome this system could give us.”** (Operational result, not just feature descriptions).
2. **“I understand how this could actually be implemented within our business.”** (Clear, tangible architecture without disrupting existing systems).

### The Golden Constraint: Honest Personalization
Before a conversation takes place, you do not know the prospect's exact internal workflows, spending policies, or custom software nuances. **The document never pretends otherwise.**
* Where company-specific details are unverified, the template uses graceful conceptual framing:
  * *“Conceptual workflow”*
  * *“Potential implementation”*
  * *“AppFolio / Existing PM System — To Be Confirmed”*
  * *“Items We Validate Together Prior to Implementation”*
* It never invents false ROI figures, hours saved, or unproven percentage claims.

---

## 2. Directory Structure

```text
concept-brief/
├── template.html                   # Master reusable HTML template
├── template.css                    # Comprehensive design system & print stylesheet
├── brief-data.json                 # Personalization data model (10-20% custom fields)
├── README.md                       # Complete guide & documentation
├── scripts/
│   ├── generate-brief.js           # CLI generator: merges JSON into HTML template
│   └── render-pdf.ps1              # Headless Edge/Chrome PDF export utility
└── examples/
    ├── maintenance-triage-brief.html  # Live, fully rendered 3-page example
    ├── maintenance-triage-brief.pdf   # Pixel-perfect 3-page export
    └── blank-concept-brief.html       # Blank starter template with raw [PLACEHOLDERS]
```

---

## 3. Visual Language & Component Grammar

The visual design avoids cliché AI tropes (no brains, no robots, no cyberpunk neon gradients). Instead, it relies on a **rigorous semantic color grammar**:

| Semantic Role | Color Tokens | Badge Style | When To Use |
|---|---|---|---|
| **External Input** | Slate / Neutral (`#0f766e` / `#f0fdfa`) | `badge-system` | Resident email, portal form, SMS, phone call trigger. |
| **Automation Logic** | Royal Blue (`#1d4ed8` / `#eff6ff`) | `badge-auto` | Normalization, deduplication, state persistence, locks. |
| **AI Interpretation** | Indigo (`#4338ca` / `#eef2ff`) | `badge-ai` | Extraction of trade, urgency, symptoms, drafting. |
| **Human Checkpoint** | Warm Amber (`#b45309` / `#fffbeb`) | `badge-human` | Manager alert, approval buttons, spend authorization. |
| **Executed Outcome** | Emerald Green (`#047857` / `#ecfdf5`) | `badge-outcome` | Verified dispatch sent, factual resident update. |
| **Exception / Danger** | Rose / Coral (`#be123c` / `#fff1f2`) | `badge-warn` | Delivery failure, unreadable report, safety alarm. |
| **To Confirm (TBD)** | Muted Slate (`#475569` / `#f8fafc`) | `badge-tbd` | Unverified software, unknown thresholds, checklist. |

---

## 4. The 3-Page Structure

### Page 01 — The Opportunity
* **Header & Metadata Box:** Company name, prospect attention, known PM stack, and document ref.
* **Why This Concept Was Prepared:** 2–3 sentence operational context tailored to the prospect's known portfolio (e.g. 450 scattered-site doors).
* **The Operational Problem:** Real-world friction (unstructured messages, the two-sided risk of under- vs over-response, after-hours coverage gap).
* **The Target Outcome Hero (Visual Centerpiece):** High-contrast dark gradient card summarizing the primary transformation with 3 operational shifts (Instant Risk Flagging, Hands-Off Clarification, One-Tap Manager Approval).
* **Transformation Pipeline:** 3-column comparative view contrasting *01 Current Friction* $\rightarrow$ *02 Automation Overlay* $\rightarrow$ *03 Target State*.

### Page 02 — How The System Works (Workflow Diagram)
* **Visual Component Legend:** Quick guide to the node grammar.
* **5-Stage Progression:**
  1. *Stage 01: Multi-Channel Intake* (Resident messages $\rightarrow$ Normalization & Dedupe $\rightarrow$ Preliminary Buffer).
  2. *Stage 02: Triage & Safety* (AI Interpretation $\rightarrow$ Binding Escalate-Only Safety Rules $\rightarrow$ Durable Persistence).
  3. *Stage 03: Routing & Filters* (3-way decision fork: Tenant Clarification, Sensitive Review Only, or Vendor Match).
  4. *Stage 04: Human Checkpoint* (Manager mobile notification with vendor choices $\rightarrow$ Database One-Send Lock $\rightarrow$ Approved Dispatch).
  5. *Stage 05: Sync & Status* (PMS Synchronization $\rightarrow$ Factual Resident Update sent *only after* vendor send succeeds).
* **Exceptions Bar:** 3 visible fallback paths (Unclear message, Vendor email failure, Unanswered emergency).

### Page 03 — How It Fits Into Their Business (The Overlay Principle)
* **4-Tier Integration Stack:**
  * *Layer 01 (Channels):* Existing Inbound Touchpoints.
  * *Layer 02 (Overlay):* Sambhav Builds Engine.
  * *Layer 03 (Business Record):* Existing Property Management System (`[KNOWN_PM_SOFTWARE]`).
  * *Layer 04 (Stakeholders):* Coordinators, Managers, Vendors, Owners.
* **The 3 Non-Disruptive Guarantees:** Zero software replacement, zero resident disruption, zero unapproved vendor dispatches.
* **Items We Validate Together:** 6-box alignment checklist (Software connectors, spending thresholds, alert channels, vendor rosters, sensitive boundaries, quiet hours).
* **Low-Friction Next Step:** "15-Minute Technical Feasibility Alignment" — zero sales pitch, no commitment.

---

## 5. How To Personalize & Generate

### Option A: Programmatic Generation via JSON (Recommended)

1. Open `concept-brief/brief-data.json` and update the prospect details:
   ```json
   {
     "company_name": "Apex Residential Properties",
     "prospect_name": "Sarah Jenkins, Director of Operations",
     "document_ref": "CB-2026-APEX",
     "known_pm_software": "Buildium / Existing PM System",
     "known_company_context": "Based on your 300-door multi-family portfolio in Denver, handling maintenance coordination during winter freeze events requires fast triage without overwhelming on-call staff.",
     "desired_outcome_headline": "Zero freeze-damage emergencies missed after hours, with 70%+ of routine triage prepared for single-tap staff approval."
   }
   ```
2. Run the Node generator:
   ```bash
   node concept-brief/scripts/generate-brief.js --data concept-brief/brief-data.json --out concept-brief/examples/apex-brief.html
   ```

### Option B: Quick Manual Editing

Copy `concept-brief/examples/blank-concept-brief.html` and search-and-replace the uppercase bracket tokens:
* `[COMPANY_NAME]`
* `[PROSPECT_NAME]`
* `[KNOWN_PM_SOFTWARE]`
* `[KNOWN_COMPANY_CONTEXT]`
* `[PROBLEM_SUMMARY]`
* `[DESIRED_OUTCOME_HEADLINE]`

---

## 6. How To Export Pixel-Perfect PDFs

### Method 1: Automated Script (PowerShell + Headless Edge/Chrome)

Run the included render script from the repository root:
```powershell
powershell -ExecutionPolicy Bypass -File concept-brief/scripts/render-pdf.ps1 -Source "concept-brief/examples/maintenance-triage-brief.html"
```
* **Renderer:** Automatically detects Microsoft Edge or Google Chrome.
* **Page Budgeting:** Uses `--virtual-time-budget=4000` to allow web fonts and SVGs to settle.
* **Validation:** Checks that the PDF has exactly 3 pages and reports file size.

### Method 2: Manual Browser Print

1. Open `template.html` or any generated HTML file in Google Chrome or Microsoft Edge.
2. Press `Ctrl + P` (or `Cmd + P` on Mac).
3. Set **Destination:** `Save as PDF`.
4. Set **Paper size:** `Letter`.
5. Set **Margins:** `None` (margins are built directly into CSS for pixel control).
6. Enable **Background graphics:** `Checked` (required for cards and pills).
7. Disable **Headers and footers:** `Unchecked` (the template renders its own running header and footer).
8. Click **Save**.
