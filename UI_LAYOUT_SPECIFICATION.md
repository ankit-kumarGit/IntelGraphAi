# IntelGraphAI — User Interface Layout & Positioning Specification

This document provides an exact, comprehensive structural and spatial map of the **IntelGraphAI (Unified Asset & Operations Brain)** web application. It specifies every container, component, positioning class, HTML tag, dimensions, coordinates, and CSS styling across the user interface.

---

## 1. Master Viewport & Shell Layout

```text
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ VIEWPORT: 100vw × 100vh (h-screen, overflow-hidden, bg-slate-950 text-slate-100 font-sans)             │
├───────────────────┬────────────────────────────────────────────────────────────────────────────────────┤
│                   │ TOP SAFETY BANNER (h-auto, min-h-[36px], bg-amber-950/30, border-b)                │
│                   ├────────────────────────────────────────────────────────────────────────────────────┤
│                   │ TOPBAR (h-16 / 64px, sticky top-0, z-30, bg-slate-900, border-b, px-6)            │
│   LEFT SIDEBAR    ├────────────────────────────────────────────────────────────────────────────────────┤
│   (w-64 / 256px,  │ MAIN SCROLLABLE WORKSPACE                                                          │
│   min-h-screen,   │ (flex-1, overflow-y-auto, bg-slate-950/95, px-6, py-6, max-w-7xl mx-auto)          │
│   bg-slate-900,   │                                                                                    │
│   border-r,       │  • Overview Dashboard OR                                                           │
│   shrink-0)       │  • Asset Profile (Header + 8 Tabs + Grounded AI Studio) OR                         │
│                   │  • Action Center / Knowledge / Compliance / Reports / Settings                     │
│                   │                                                                                    │
├───────────────────┴────────────────────────────────────────────────────────────────────────────────────┤
│ GLOBAL MODAL OVERLAYS (fixed inset-0, z-50, bg-black/75, backdrop-blur-sm, flex center)                │
│ • GlobalSearchModal (max-w-2xl, pt-20)     • GlobalChatModal (max-w-3xl, h-[85vh])                     │
│ • OnboardingWizardModal (max-w-xl)         • NewAssetModal (max-w-xl) • DocumentViewerModal (max-w-4xl)│
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Root Container
- **HTML:** `<div class="flex h-screen bg-slate-950 text-slate-100 overflow-hidden font-sans">`
- **Positioning:** Screen-locked row container (`width: 100vw`, `height: 100vh`, `display: flex`, `overflow: hidden`).
- **Background:** `#080d1a` (`bg-slate-950`).
- **Typography:** `font-sans` (`Inter, system-ui, sans-serif`).

---

## 2. Left Navigation Sidebar

Located on the far-left edge of the viewport.

- **HTML Container:** `<aside class="w-64 bg-slate-900 border-r border-slate-800 flex flex-col shrink-0 min-h-screen">`
- **Dimensions:** Width: `16rem` (`256px`), Height: `100vh` (`min-h-screen`), `flex-shrink: 0`.
- **Styling:** Background `#0f172a` (`bg-slate-900`), right border `1px solid #1e293b` (`border-slate-800`).

### 2.1 Brand Header (Top of Sidebar)
- **HTML:** `<div class="p-5 border-b border-slate-800 flex items-center gap-3">`
- **Elements:**
  - **Logo Container:** `<div class="w-9 h-9 rounded-lg bg-gradient-to-tr from-brand-600 to-cyan-400 flex items-center justify-center shadow-lg shadow-brand-500/20">`
    - Contains Lucide `<Layers class="w-5 h-5 text-white" />`.
  - **Brand Text:**
    - Title: `<h1 class="font-bold text-base text-white tracking-tight flex items-center gap-1.5">IntelGraph<span class="text-brand-400 text-xs px-1.5 py-0.5 rounded bg-brand-500/10 border border-brand-500/20">AI</span></h1>`
    - Subtitle: `<p class="text-[11px] text-slate-400 font-mono">Operations Brain v1.0</p>`.

### 2.2 Navigation Menu List (Middle of Sidebar)
- **HTML:** `<nav class="flex-1 p-3 space-y-1">`
- **Section Heading:** `<div class="px-3 py-2 text-[10px] font-semibold uppercase tracking-wider text-slate-400">Operations Platform</div>`
- **7 Primary Navigation Items:**
  - Standard Item Class: `w-full flex items-center justify-between px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all`
  - Active Item Class: `bg-brand-500/15 text-brand-400 border border-brand-500/30 shadow-sm`
  - Inactive Item Class: `text-slate-400 hover:text-slate-200 hover:bg-slate-800/60`
  1. **Overview:** Icon: `LayoutDashboard (w-4 h-4)` | Label: `Overview`
  2. **Assets:** Icon: `Cpu (w-4 h-4)` | Label: `Assets`
  3. **Action Center:** Icon: `AlertCircle (w-4 h-4)` | Label: `Action Center` | Badge: `<span class="text-xs font-semibold px-2 py-0.5 rounded-full bg-red-500/20 text-red-400 border border-red-500/30">1</span>`
  4. **Knowledge:** Icon: `Network (w-4 h-4)` | Label: `Knowledge`
  5. **Compliance:** Icon: `ShieldCheck (w-4 h-4)` | Label: `Compliance`
  6. **Reports:** Icon: `FileText (w-4 h-4)` | Label: `Reports`
  7. **Settings:** Icon: `Sliders (w-4 h-4)` | Label: `Settings`

### 2.3 Plant Hierarchy Card (Bottom of Sidebar)
- **HTML:** `<div class="p-3 m-3 rounded-lg bg-slate-950/70 border border-slate-800 text-[11px] text-slate-400 space-y-1">`
- **Contents:**
  - Header Row: `<span class="text-[10px] uppercase tracking-wider text-slate-400">Target Plant</span>` + Active Status: `<span class="text-emerald-400 flex items-center gap-1"><span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span> Plant A</span>`
  - Sub-line: `Gulf Coast Unit 2 Line`

---

## 3. Right Main App Column

Takes up the remaining screen width to the right of the sidebar: `<div class="flex-1 flex flex-col min-w-0 overflow-hidden">`.

### 3.1 Top Safety Disclaimer Banner (Rule #17)
- **HTML:** `<div class="bg-amber-950/30 border-b border-amber-900/40 px-4 py-2 text-xs text-amber-300 flex items-center justify-between">`
- **Left Group:**
  - Icon: `<AlertTriangle class="w-3.5 h-3.5 text-amber-400 shrink-0" />`
  - Text: `<strong class="font-semibold text-amber-200">Industrial Decision-Support System:</strong> AI-generated insights must be verified against approved procedures, OEM documentation, and site safety requirements before performing work.`
- **Right Group:**
  - Icon: `<ShieldCheck class="w-3 h-3 text-emerald-400" />`
  - Text: `<span class="hidden md:flex items-center gap-1.5 text-[11px] text-amber-400/80 font-mono">Strict Grounding Enforced</span>`

### 3.2 Topbar Header Bar
- **HTML:** `<header class="h-16 bg-slate-900 border-b border-slate-800 px-6 flex items-center justify-between gap-4 sticky top-0 z-30">`
- **Height & Sticky:** `64px` (`h-16`), pinned to top (`sticky top-0`), `z-index: 30`.
- **Left Zone — Hierarchy Breadcrumb:**
  - `<div class="flex items-center gap-1.5 text-xs text-slate-400 overflow-hidden truncate">`
  - Breadcrumbs: `Apex Energy` → `ChevronRight` → `Plant A` → `ChevronRight` → `Unit 2` → `ChevronRight`
  - Active Target Pill: `<span class="text-brand-400 font-semibold px-2 py-0.5 rounded bg-brand-500/10 border border-brand-500/20">P-101 — Centrifugal Water Injection Pump</span>`
- **Right Zone — Utility Controls (`flex items-center gap-3`):**
  1. **Global Search Button:**
     - `<button class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-800 border border-slate-700/70 text-slate-400 text-xs shadow-inner">`
     - Icon: `Search (w-3.5 h-3.5)` + Text: `"Search tags, documents, records..."` + Shortcut Badge: `<kbd class="px-1.5 py-0.5 text-[10px] font-mono bg-slate-900 rounded border border-slate-700">⌘K</kbd>`
  2. **Ask Knowledge AI Quick Action:**
     - `<button class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gradient-to-r from-purple-600/20 to-brand-600/20 border border-purple-500/30 text-purple-300 text-xs font-medium">`
     - Icon: `Sparkles (w-3.5 h-3.5 text-purple-400)` + Text: `"Ask Knowledge AI"`
  3. **1-Click Reseed Button:**
     - `<button title="Reset database to verified demo story" class="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 border border-slate-700 text-xs">`
     - Icon: `RotateCw (w-3.5 h-3.5)`
  4. **Operational Role Switcher Dropdown:**
     - Container: `<div class="relative">`
     - Trigger: `<button class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 text-xs font-medium">`
     - Dropdown Overlay: `<div class="absolute right-0 mt-2 w-72 bg-slate-900 border border-slate-800 rounded-xl shadow-2xl p-2 z-50">`
     - 3 Switchable Options:
       - `Maintenance Engineer`
       - `Quality / Compliance User`
       - `Plant Manager`

---

## 4. Main Scrollable Workspace (`<main class="flex-1 overflow-y-auto bg-slate-950/95">`)

All application pages render inside a responsive centered grid: `<div class="p-6 max-w-7xl mx-auto space-y-6">`.

---

## 5. Screen 1: Master Asset Profile (`AssetProfile.jsx`)

When viewing an individual machine (e.g. `P-101`), the page organizes into:

### 5.1 Concise Asset Profile Header Card
- **HTML:** `<div class="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">`
- **Row 1 — Asset Identity & Status Highlights:**
  - **Left Block:**
    - Tag Badge: `<span class="font-mono text-sm font-bold text-brand-400 bg-brand-500/10 px-2 py-0.5 rounded border border-brand-500/20">P-101</span>`
    - Subtitle: `<span class="text-slate-400 text-xs">| ABC Pumps Inc. XYZ-200 • Plant A / Unit 2</span>`
    - Main Title: `<h2 class="text-xl font-bold text-white tracking-tight">Centrifugal Water Injection Pump</h2>`
  - **Right Block (Status Badges):**
    - Status Pill: `Operational` (`bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 rounded-full px-3 py-1 text-xs font-semibold`)
    - Completeness Pill: `Completeness: 92%` (`bg-slate-800 border border-slate-700 rounded-full px-3 py-1 text-xs font-bold text-brand-400`)
    - Open Findings Pill: `Open Findings: 1` (`bg-amber-500/10 border border-amber-500/20 rounded-full px-3 py-1 text-xs text-amber-300`)
    - Next Maintenance Pill: `Next Maint: 12 Sep 2026` (`bg-slate-800 border border-slate-700 rounded-full px-3 py-1 text-xs text-slate-300`)
- **Row 2 — 8-Tab Navigation Strip:**
  - `<div class="flex items-center gap-1 overflow-x-auto border-t border-slate-800 pt-3">`
  - 8 Interactive Tab Buttons (`px-3.5 py-2 rounded-lg text-xs font-semibold whitespace-nowrap`):
    1. **Overview** (Icon: `Layers`)
    2. **Knowledge Map** (Icon: `Cpu`)
    3. **Maintenance** (Icon: `Wrench`)
    4. **Telemetry** (Icon: `Activity`)
    5. **Findings** (Icon: `AlertCircle` + Badge `1`)
    6. **Documents** (Icon: `FileText` + Badge `8`)
    7. **Notes** (Icon: `MessageSquare` + Badge `1`)
    8. **Audit Log** (Icon: `History`)

---

### 5.2 Tab 1: Overview Tab (`activeTab === 'overview'`)
1. **Headline → Highlight → Evidence → Action Synthesis Card:**
   - Container: `<div class="p-5 rounded-2xl bg-gradient-to-r from-purple-950/30 via-slate-900 to-slate-900 border border-purple-500/30 space-y-3 shadow-lg">`
   - Top Meta: Sparkles icon + `AI Asset Health Synthesis` + `[Strictly Grounded]` badge + `[View Evidence]` toggle button.
   - Headline: `<h3 class="text-base font-bold text-white">⚠ Recurring bearing-related issue identified in available records.</h3>`
   - 3-Column Milestone Cards:
     - Col 1: Previous Overhaul (2024) — Drive-End Bearing Replaced (`WO-1023`)
     - Col 2: Condition Monitoring (2025) — Vibration Elevated: 6.8 mm/s (`INSP-456`)
     - Col 3: Unscheduled Trip (Feb 2026) — Bearing Seizure Failure (`INC-78 / WO-1189`)
   - Expandable Evidence Drawer (when toggled): Stored quotes from `Pump_P101_OEM_Manual`, `INSP-456`, and `WO-1189`.
2. **Knowledge Completeness Checklist:**
   - Container: `<div class="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-4">`
   - 6 Grid Cards (`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3`):
     - OEM Manual (`✓ Complete`)
     - SOP (`✓ Complete`)
     - Maintenance (`✓ Complete`)
     - Inspection (`✓ Complete`)
     - Failure History (`✓ Complete`)
     - Safety LOTO (`✓ Complete`)
     - Calibration Record (`⚠ Gap / Missing`)
3. **Specifications & Components Grid:**
   - 2 Equal Columns (`grid grid-cols-1 md:grid-cols-2 gap-6`):
     - Left: Technical Specs Table (Tag, Model, Serial, Flow, Head, RPM, Approved Lubricant `ISO VG 46`).
     - Right: Registered Components SKF parts list (DE Bearing `SKF 6312`, NDE Bearing `NU 312`, Impeller `316L SS`, Shaft `4140 Steel`).

---

### 5.3 Tab 2: Asset Knowledge Map Tab (`TabKnowledgeMap.jsx`)
- **Top Control Strip:** `<div class="flex items-center justify-between p-3 rounded-xl bg-slate-900 border border-slate-800 text-xs">`
  - Counter: `Asset Knowledge Map (Connected Entities, Stored Relationships)`
  - Filter Pills: `All`, `Component`, `Document`, `Maintenance`, `Inspection`, `Failure`.
- **Two-Column Interactive Workspace (`grid grid-cols-1 lg:grid-cols-3 gap-4`):**
  - **Left (Col Span 2) — Visual Canvas Area:**
    - Container: `<div class="p-5 rounded-xl bg-slate-950/80 border border-slate-800 min-h-[440px] flex flex-col justify-between">`
    - Legend Top Bar: Asset (blue), Component (cyan), Document (purple), Maintenance (blue), Inspection (emerald), Failure (red).
    - Node Layout Cloud: Interactive interactive node cards with type, label, details, and active white ring on selection.
  - **Right (Col Span 1) — Entity Inspector Drawer:**
    - Container: `<div class="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-4">`
    - Selected Entity Title, Description, and verified attributes table (`document_id`, `version`, `category`, `part_number`).
    - Connected Links list: Clicking any connected link switches the inspector focus to that connected node.
    - "Open Document & Chunks" button.

---

### 5.4 Tab 3: Maintenance Tab
- **Recurring Issue Alert:** `<div class="p-4 rounded-xl bg-amber-950/30 border border-amber-500/30 text-xs">`
  - `Recurring Drive-End Bearing replacement recorded (2 times)`.
- **Work Orders Feed:**
  - Container: `<div class="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-4">`
  - Cards for `WO-1023` (Preventive Overhaul) and `WO-1189` (Emergency Corrective) with dates, lead technician, replaced components, and findings.

---

### 5.5 Tab 4: Telemetry Tab (`TabTelemetry.jsx`)
- **Top Banner:** `<div class="p-3.5 rounded-xl bg-cyan-950/30 border border-cyan-500/30 text-xs text-cyan-300">`
  - `[Synthetic Demo Data]` badge with disclaimer explaining correlation to historical milestones.
- **4 Condition KPI Gauges (`grid grid-cols-2 md:grid-cols-4 gap-4`):**
  1. Overall Vibration: `2.3 mm/s RMS` (Below 4.5 mm/s limit)
  2. Bearing Housing Temp: `50.5°C` (Max limit: 82°C)
  3. Discharge Pressure: `15.0 bar` (Design head: ~45m)
  4. Operating Hours: `21,050 hrs` (Speed: 2950 RPM)
- **Historical Telemetry Table:**
  - Full chronological time series highlighting `2025-08-15` warning spike (`6.8 mm/s`), `2026-02-22` trip (`12.4 mm/s`), and `2026-02-23` post-repair recovery (`2.2 mm/s`).

---

### 5.6 Tab 5: Findings Tab (Action-Oriented)
- **Finding Card:** `<div class="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-3 text-xs">`
  - Title: `Potential Recurring Bearing-Related Issue Detected` | Status: `Open`
  - Historical Evidence: `3 related historical records (WO-1023 in 2024, INSP-456 in 2025, WO-1189 in 2026)`
  - Recommended Next Step: `Review bearing inspection procedure and lubricant sampling frequency per SOP-101 Section 4.2`
  - Governing Procedure: `OEM Manual XYZ-200 / SOP-101` | Owner: `Maintenance Lead`

---

### 5.7 Tab 6: Documents Tab (`TabDocuments.jsx`)
- **Table Container:** `<div class="rounded-xl border border-slate-800 bg-slate-900/80 overflow-hidden">`
- **Columns:** Document Title & Filename, Category, Version, Effective Date, Review Date, Governance Status, Actions.
- **Statuses:**
  - `Approved` (`bg-emerald-500/15 text-emerald-400 border border-emerald-500/30`)
  - `Obsolete` (`bg-red-500/15 text-red-400 border border-red-500/30 line-through opacity-60`)
- **Action Buttons:** `View Chunks` (opens chunk modal) and `Retire / Approve` toggle.

---

### 5.8 Tab 7: Notes Tab (Human Input)
- **Form Card:** `<form class="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-3">`
  - Textarea, Author input, `[Human Input]` badge, and `Submit Field Note` button.
- **Notes Feed:**
  - Stream of notes badged with `[Operator Note]` showing Author, Timestamp, and observation text.

---

### 5.9 Tab 8: Audit Log Tab
- **Container:** `<div class="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-4">`
- **Entries:** Chronological immutable event cards (`Document Ingested`, `Extraction Confirmed`, `Maintenance Logged`, `Governance Updated`) with actor, role, and details.

---

### 5.10 Grounded AI Assistant Studio (Bottom of Asset Profile)
- **Container:** `<div class="p-5 rounded-2xl bg-gradient-to-br from-slate-900 via-slate-850 to-slate-900 border border-brand-500/30 space-y-4 shadow-xl">`
- **Header:** Sparkles icon + `Ask Grounded Knowledge Assistant About P-101` + `[FAISS RAG]` badge.
- **Quick Prompt Chips:**
  - `"What is the maintenance history of P-101?"`
  - `"Has P-101 experienced bearing failure before?"`
  - `"What is the recommended radial bearing clearance?"`
  - `"What lubricant is approved for P-101?"`
- **Query Input Row:**
  - Input: `<input class="flex-1 px-4 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white">`
  - Button: `<button class="px-4 py-2 rounded-xl bg-brand-500 text-white font-bold text-xs">`
- **Grounded Answer Card:**
  - Confidence Header: `High Confidence • 0.28ms Latency`
  - Response Text: Grounded explanation citing exact sections.
  - Supporting Citations Grid: Clickable cards displaying Document Name, Page #, Section, and excerpt. Clicking opens the `DocumentViewerModal`.

---

## 6. Global Modals & Overlay Windows

All modals are positioned with `fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4`.

### 6.1 Global Search Modal (`GlobalSearchModal.jsx`)
- **Dimensions:** Width: `max-w-2xl` (`672px`), Position: `items-start pt-20`.
- **Input Bar:** Search icon + text input + `ESC` badge.
- **Entity Resolution Banner:**
  - Displays when query matches alias (e.g. `Pump 101` → `P-101`), with direct "Open Profile" button.
- **Results Scroll Area:** Max height `max-h-96 overflow-y-auto`. Categorized results for assets, components, and documents.

### 6.2 Global Chat Modal (`GlobalChatModal.jsx`)
- **Dimensions:** Width: `max-w-3xl` (`768px`), Height: `85vh`.
- **Header:** Scope dropdown (e.g. `Scoped: P-101` vs `Fleet-Wide Search`) + Close button.
- **Quick Chips:** Prompt buttons across top.
- **Chat Stream:** User bubbles (right-aligned in brand blue) and Assistant bubbles (left-aligned with citations and confidence metrics).
- **Safety Disclaimer Strip:** Pinned above input bar.
- **Input Bar:** Full-width text input + Send button.

### 6.3 Legacy Onboarding Wizard Modal (`OnboardingWizardModal.jsx` — Use Case 1)
- **Dimensions:** Width: `max-w-xl` (`576px`).
- **4-Step Progress Bar:** `1. Upload File → 2. AI Extraction → 3. Human Confirmation → 4. Knowledge Saved`.
- **Human Confirmation Staging Card:**
  - Amber banner: *"Industrial records must not be blindly accepted from AI."*
  - Editable form fields: Canonical Asset Tag, Event Type, Event Date, Primary Component, Work Order Number.
  - Action buttons: `[Re-upload]` or `[Confirm & Commit to Asset]`.

### 6.4 New Asset Registration Modal (`NewAssetModal.jsx` — Use Case 2)
- **Dimensions:** Width: `max-w-xl` (`576px`).
- **Form Fields:** Asset Tag (`P-205`), Machine Name, Asset Type, Manufacturer, Model, Serial Number, Plant, Area, Description.
- **Success View:** Checkmark icon with confirmation that the knowledge profile starts from day one.

### 6.5 Document Chunk Viewer Modal (`DocumentViewerModal.jsx`)
- **Dimensions:** Width: `max-w-4xl` (`896px`), Height: `max-h-[90vh]`.
- **Header:** Document title, version, and governance status badge (`Approved` vs `Obsolete`).
- **Summary Box:** Executive document summary.
- **Chunk Stream:** All FAISS searchable text chunks with Page Number, Section Title, and exact text content.

---

## 7. Color Palette & Typography Token Map

| UI Element | Tailwind Class | HEX / RGB Equivalent | Purpose |
|---|---|---|---|
| **Base Background** | `bg-slate-950` | `#080d1a` | Main application background |
| **Panel / Sidebar** | `bg-slate-900` | `#0f172a` | Sidebar, topbar, and major card surfaces |
| **Borders** | `border-slate-800` | `#1e293b` | Enterprise card borders and dividers |
| **Brand Accent** | `text-brand-400` / `bg-brand-500` | `#38bdf8` / `#0ea5e9` | Primary action buttons, active tabs, tags |
| **Verified Badge** | `text-emerald-400` / `bg-emerald-500/10` | `#34d399` | Stored immutable records & operational status |
| **Human Input Badge**| `text-amber-400` / `bg-amber-500/10` | `#fbbf24` | Operator field notes and open findings |
| **AI Insight Badge** | `text-purple-400` / `bg-purple-500/10`| `#c084fc` | Data-grounded correlations and RAG citations |
| **Safety / Critical**| `text-red-400` / `bg-red-500/10` | `#f87171` | Unscheduled trips, vibration exceedances |
| **Primary Font** | `font-sans` | `Inter, system-ui, sans-serif` | Clean, modern industrial typography |
| **Technical Font** | `font-mono` | `JetBrains Mono, monospace` | Equipment tags, serials, and dates |
