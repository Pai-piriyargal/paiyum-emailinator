# 📋 Hackathon Team Roadmap & Task Allocation (4 Members)

This roadmap combines your suggestions (**Detailed Review Explanations** and **Review Urgency Scoring**) with the official **Organiser Work Sheet / Hackathon Requirements** (Email Classification, 7-Field Extraction, Multi-Format Parsing, Scanned Document OCR, Reliability & Self-Evaluation, and Human-in-the-Loop Dashboard).

---

## 👥 Team Work Breakdown Structure (4 Members)

```
                                 ┌───────────────────────────────────┐
                                 │     Paiyum Emailinator Team       │
                                 └─────────────────┬─────────────────┘
                                                   │
     ┌──────────────────────┬──────────────────────┼──────────────────────┬──────────────────────┐
     │                      │                      │                      │                      │
┌────▼─────────────┐   ┌────▼─────────────┐   ┌────▼─────────────┐   ┌────▼─────────────┐   ┌────▼─────────────┐
│ Member 1: Core   │   │ Member 2: Logic  │   │ Member 3: HITL   │   │ Member 4: QA,    │   │ All Members:     │
│ Extraction & OCR │   │ & Reliability    │   │ UI & Dashboard   │   │ Benchmarking &   │   │ Pitch & Demo     │
│ Specialist       │   │ Specialist       │   │ Specialist       │   │ Pitch Lead       │   │ Presentation     │
└──────────────────┘   └──────────────────┘   └──────────────────┘   └──────────────────┘   └──────────────────┘
```

---

### 👤 Member 1: Core Extraction, OCR & Messier Input Specialist
**Focus Area**: Document Ingestion, OCR Engine, Field Extraction, and Messier Formats.

#### 🎯 Key Tasks & Deliverables:
1. **Scanned PDF & Image OCR Integration** *(Organiser Advanced Challenge)*:
   - Integrate `pdf2image` + `pytesseract` (or OpenCV preprocessing) into `src/parser.py` to convert scanned image PDFs into readable text when standard text extraction returns empty.
2. **Messier Input & Label Alias Expansion**:
   - Expand `alias_map` in `src/extractor.py` to handle tricky or ambiguous headers (e.g., `Place of Receipt`, `Final Destination`, `Consignee Address`, `Shipper/Exporter`).
3. **Complex Number & Unit Parsing**:
   - Improve weight conversions in `extractor.py` (e.g., automatically converting pounds `LBS` or metric tons `MT` to kilograms `KG`).
   - Improve container string parsing (e.g. `20' Dry Standard x 4` -> `4`).
4. **Attachment Completeness Validator**:
   - Identify when an attachment is corrupted, missing text, or password-protected and flag it cleanly for `unreadable` review reason.

---

### 👤 Member 2: Discrepancy Logic, Explanations & Reliability Specialist
**Focus Area**: Decision Engine, Explanations, Urgency Scoring, and Self-Evaluation Benchmark.

#### 🎯 Key Tasks & Deliverables:
1. **Detailed Review Explanations (`review_explanation`)** *(Your Suggestion)*:
   - Enhance `src/comparator.py` so that every `NEEDS_REVIEW` case outputs a clear, human-readable sentence explaining *why* (e.g. `"Missing Bill of Lading attachment — only SI file found"`, or `"Field 'consignee' could not be found in draft BL"`).
2. **Review Urgency & Priority Scoring (`urgency`)** *(Your Suggestion)*:
   - Implement an urgency scoring algorithm in `src/comparator.py` categorizing every email into:
     - 🚨 `HIGH`: Critical field mismatches (`consignee`, `gross_weight_kg`, `port_of_discharge`) or unreadable attachments.
     - ⚠️ `MEDIUM`: Non-critical field missing values (`missing_value`), or pending `SI_REQUEST` / `INVOICE_QUERY`.
     - ℹ️ `LOW`: Routine messages (`GENERAL`) or clean verification checks (`OK`).
3. **Advanced Comparison Rules**:
   - Add port code equivalency lookups (e.g., UN/LOCODE matching like `CNNTG` = `Nantong Port`) and shipper company prefix ignore rules (e.g. `LTD`, `INC`, `CORP`).
4. **Self-Evaluation Scoreboard Integration**:
   - Connect `loader.py` to the local Docker HTTP server (`http://localhost:8080`) to automatically post submissions (`inbox.submit()`) and track scoreboard accuracy.

---

### 👤 Member 3: Human-in-the-Loop (HITL) Dashboard & UI Specialist
**Focus Area**: Web Interface, Side-by-Side Evidence Viewer, Operator Overrides, and Visual Polish.

#### 🎯 Key Tasks & Deliverables:
1. **Urgency Badges & Quick Filtering** *(Your Suggestion + UI)*:
   - Add colored urgency badges (Red = High, Yellow = Medium, Gray = Low) and filter buttons (`All`, `High Urgency Only`, `Needs Review`) on `src/dashboard.py`.
2. **Detailed Explanation Column**:
   - Render the new human-readable `review_explanation` directly inside the primary audit dashboard table.
3. **Side-by-Side SI vs BL Evidence Viewer (`/review/{eid}`)**:
   - Create a clean modal/page showing SI values in column A vs BL values in column B, with mismatched fields highlighted in red side-by-side.
4. **Human Operator Override & Save**:
   - Add input fields allowing operators to correct values, click **"Save & Approve"**, and write updated records back to `submission.json`.

---

### 👤 Member 4: Integration, Testing, Benchmarking & Presentation Lead
**Focus Area**: End-to-End QA, Test Suite, Performance Metrics, and Pitch Deck.

#### 🎯 Key Tasks & Deliverables:
1. **Automated Unit Test Suite Expansion**:
   - Expand `tests/test_pipeline.py` to cover new OCR fallbacks, urgency scoring logic, and detailed explanation generators.
2. **End-to-End Pipeline Verification**:
   - Run benchmark passes across all 520 emails, validating `submission.json` compliance against `sample_submission.json`.
3. **System Documentation & Architecture Diagrams**:
   - Keep `README.md` and `GETTING_STARTED.md` updated with latest feature instructions and system architecture diagrams.
4. **Pitch Deck & Demo Video Preparation**:
   - Prepare presentation slides highlighting problem statement, 5-category classifier, 7-field extraction, OCR capability, urgency triage system, and live dashboard walkthrough.

---

## 🚀 Recommended Immediate Next Actions

| Step | Action Item | Assigned To |
| :---: | :--- | :---: |
| **1** | Implement `review_explanation` and `urgency` scoring in `comparator.py` | **Member 2** |
| **2** | Add Urgency badges & side-by-side evidence viewer to `dashboard.py` | **Member 3** |
| **3** | Add OCR fallback for image-only PDFs in `parser.py` | **Member 1** |
| **4** | Run full pipeline benchmark and prepare presentation demo | **Member 4** |

---
*Created for Team Pai-piriyargal*
