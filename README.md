# Paiyum Emailinator — Shipping Document Verification System

> **Hackathon Project Repository** | Team Pai-piriyargal  
> *End-to-End Autonomous Email Inbox Classifier, Shipping Document Discrepancy Extractor, and Human-in-the-Loop Operations Dashboard.*

---

## 🎯 Executive Summary & Problem Context

In global shipping operations, operations teams manage complex inboxes receiving requests for document checks, new Shipping Instructions (SIs), invoice queries, and operational updates alongside spam. 

Manual verification of draft Bills of Lading (BL) against Shipping Instructions (SI) is time-consuming, prone to human error, and complicated by field label variations (e.g., `Port of Loading` vs `Load Port`). A missed discrepancy can lead to delayed shipments, severe port penalties, and expensive customs corrections.

**Paiyum Emailinator** solves this by automating:
1. **Inbox Email Classification**: Filtering messages into 5 operational categories (`BL_COMPARISON`, `SI_REQUEST`, `INVOICE_QUERY`, `GENERAL`, `SPAM`).
2. **Multi-Format Document Parsing**: Processing TXT, PDF, Word (DOCX), and Excel (XLSX) attachments.
3. **Field Extraction & Normalization**: Extracting 7 key shipment fields with alias resolution (`shipper`, `consignee`, `notify_party`, `port_of_loading`, `port_of_discharge`, `container_count`, `gross_weight_kg`).
4. **Discrepancy Comparison Engine**: Identifying mismatches side-by-side with high precision.
5. **Human-in-the-Loop Operations Dashboard**: Escalating uncertain cases (`NEEDS_REVIEW`) with clear audit trails for operator confirmation.

---

## 🏗 System Architecture

```
                               ┌─────────────────────────┐
                               │     Incoming Email      │
                               └────────────┬────────────┘
                                            │
                                  ┌─────────▼─────────┐
                                  │ Email Classifier  │
                                  └─────────┬─────────┘
                                            │
               ┌────────────────────────────┼────────────────────────────┐
               │                            │                            │
     [SI_REQUEST / INVOICE /        [BL_COMPARISON]                  [SPAM]
      GENERAL] -> status: OK                │                            │
               │                            │                      status: OK
               └────────────────────┐       │
                                    │       ▼
                                ┌───┴───────────────┐
                                │ Document Parser   │ (TXT / PDF / DOCX / XLSX)
                                └───┬───────────────┘
                                    │
                                    ▼
                                ┌───────────────────┐
                                │  Field Extractor  │ (Alias Map & Regex)
                                └───┬───────────────┘
                                    │
                                    ▼
                                ┌───────────────────┐
                                │ Document          │
                                │ Comparator        │
                                └───┬───────────────┘
                                    │
               ┌────────────────────┼────────────────────┐
               │                    │                    │
          [Status: OK]      [Status: MISMATCH]   [Status: NEEDS_REVIEW]
         No Discrepancies     Defect Flagged      Missing Attachment/
               │                    │              Unreadable / Missing Val
               │                    │                    │
               └────────────────────┴────────────────────┘
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │ Human-in-the-Loop     │
                        │ Review Dashboard UI   │
                        └───────────────────────┘
```

---

## 📁 Project Repository Layout

```
.
├── README.md                   # System Architecture & Technical Game Plan
├── .gitignore                  # Git ignore rules
├── sdoc-hackathon-bundle/      # Participant dataset & static sample files
│   ├── inbox/                  # JSON email records
│   ├── attachments/            # SI and BL attachments (.txt, .pdf, .docx, .xlsx)
│   ├── loader.py               # Data loader helper
│   └── sample_submission.json  # Output formatting specification
├── sdoc-hackathon-docker/      # Local evaluation server setup (Docker Compose)
└── shipping-verification/      # Core Verification Engine
    ├── main.py                 # Pipeline entry point
    ├── loader.py               # Integrated loader module
    ├── requirements.txt        # Python dependencies
    ├── README.md               # Subproject technical details
    ├── src/
    │   ├── classifier.py       # 5-category email classification module
    │   ├── parser.py           # Multi-format document parser
    │   ├── extractor.py        # 7-field extraction engine
    │   ├── comparator.py       # Discrepancy comparison & reliability logic
    │   └── dashboard.py        # Human-in-the-loop web UI
    └── tests/
        └── test_pipeline.py    # Automated unit test suite
```

---

## ⚡ Quick Start & Execution

### 1. Run the End-to-End Verification Pipeline
```bash
python shipping-verification/main.py sdoc-hackathon-bundle
```
Generates `submission.json` ready for scoring.

### 2. Run Automated Unit Tests
```bash
python -m unittest discover -s shipping-verification/tests
```

### 3. Launch Human-in-the-Loop Dashboard
```bash
python shipping-verification/src/dashboard.py
```
Access dashboard at `http://127.0.0.1:8000`.

---

## 📊 Scoring Rubric Breakdown (100% Total Score)

| Core Dimension | Weight | Strategy & Implementation Highlights |
|---|---|---|
| **Working Core Prototype** | 25% | Fully functional end-to-end pipeline processing all 520 inbox emails. |
| **System Design & Architecture** | 15% | Decoupled modular design (`classifier`, `parser`, `extractor`, `comparator`). |
| **Technology Integration** | 15% | NLP regex parsing, fuzzy string similarity, multi-format doc parsing (PDF/DOCX/XLSX). |
| **Technical Feasibility & Validation** | 15% | Validated output matching `sample_submission.json` schema & unit tests. |
| **Problem Statement Understanding** | 10% | Complete mapping of 5 email categories, 7 shipment fields, 4 review reasons. |
| **Innovation & Solution Approach** | 10% | Smart label alias mapping, unit normalization, fuzzy match tolerances. |
| **Practical Value & Potential** | 10% | Operator Web UI for human review of escalated cases and real-time audit logging. |

---
*Developed by Team Pai-piriyargal*
