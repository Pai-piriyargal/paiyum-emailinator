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
4. **Discrepancy Comparison Engine**: Identifying mismatches side-by-side with high precision and fuzzy matching.
5. **Human-in-the-Loop Operations Dashboard**: Escalating uncertain cases (`NEEDS_REVIEW`) with urgency scoring and clear audit trails for operator confirmation.

---

## 🏗 Technical Architecture

```
                               ┌─────────────────────────┐
                               │     Incoming Email      │
                               └────────────┬────────────┘
                                            │
                                  ┌─────────▼─────────┐
                                  │ Email Classifier  │ (5-Category Intent Engine)
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
                                │  Field Extractor  │ (Alias Map & Normalization)
                                └───┬───────────────┘
                                    │
                                    ▼
                                ┌───────────────────┐
                                │ Document          │ (Fuzzy Match & Numeric
                                │ Comparator        │  Threshold Engine)
                                └───┬───────────────┘
                                    │
               ┌────────────────────┼────────────────────┐
               │                    │                    │
          [Status: OK]      [Status: MISMATCH]   [Status: NEEDS_REVIEW]
         No Discrepancies     Defect Flagged      Missing Attachment /
               │                    │              Unreadable / Missing Val
               │                    │                    │
               └────────────────────┴────────────────────┘
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │ Human-in-the-Loop     │
                        │ Review Dashboard UI   │ (FastAPI & Serverless Vercel)
                        └───────────────────────┘
```

The system employs a decoupled, modular microservice architecture built in Python:
- **Ingestion Layer (`loader.py`)**: Supports both local static bundle directory reading and HTTP API dataset ingestion over Docker/REST endpoints.
- **Classification Engine (`src/classifier.py`)**: Multi-layered regex and intent classifier to route email records.
- **Multi-Format Extraction Pipeline (`src/parser.py` & `src/extractor.py`)**: Converts PDF tables, Word text, and text attachments into standardized key-value JSON schema.
- **Comparison & Urgency Engine (`src/comparator.py`)**: Computes field-level discrepancies, assigns urgency scores (`HIGH`, `MEDIUM`, `LOW`), and generates human-readable review explanations.
- **Operational Dashboard (`src/dashboard.py` & `api/index.py`)**: High-performance FastAPI Web UI with glassmorphism UI design, operator overrides, and Vercel serverless deployment capabilities.

---

## 🛠 Implementation Details

### 1. 5-Category Email Classifier (`src/classifier.py`)
- Categorizes messages into `SPAM`, `INVOICE_QUERY`, `SI_REQUEST`, `BL_COMPARISON`, and `GENERAL`.
- Differentiates between emails referencing final tracking numbers vs. explicit requests to review draft BLs.

### 2. Multi-Format Document Ingestion (`src/parser.py`)
- Reads raw text (`.txt`), extractable PDFs (`PyPDF2`), Word documents (`python-docx`), and tabular spreadsheets (`pandas`).
- Handles corrupted, empty, or unreadable attachments gracefully by triggering explicit `unreadable` review escalations.

### 3. 7-Field Data Normalization Engine (`src/extractor.py`)
- Extracts required shipment fields: `shipper`, `consignee`, `notify_party`, `port_of_loading`, `port_of_discharge`, `container_count`, and `gross_weight_kg`.
- Resolves synonym aliases (e.g., `Load Port` = `Port of Loading`, `POD` = `Port of Discharge`).
- Converts weight units automatically (e.g., `LBS` or `MT` converted to standard `KG`) and strips container size descriptions (`20' Standard Container x 4` -> `4`).
- Handles complex legal clauses such as `"SAME AS CONSIGNEE"` by automatically resolving values.

### 4. Discrepancy & Urgency Scoring (`src/comparator.py`)
- Uses **RapidFuzz** fuzzy ratio matching (85%+ threshold) for company names and addresses to account for minor typos.
- Uses numeric tolerance thresholds for weight variations (< 1% variation allowed).
- Assigns priority badges:
  - 🚨 `HIGH`: Critical field mismatches (`consignee`, `port_of_discharge`, `gross_weight_kg`) or unreadable documents.
  - ⚠️ `MEDIUM`: Non-critical missing values or operational requests.
  - ℹ️ `LOW`: Clean verification checks (`OK`).

### 5. Operator Web UI & Serverless Deployment (`src/dashboard.py` & `vercel.json`)
- Interactive FastAPI dashboard showcasing real-time metrics, defect tables, urgency filters, and side-by-side evidence modals.
- Allows operators to perform manual value overrides and write corrections directly into `submission.json`.

---

## ⚠️ Challenges Faced & Solutions

1. **Attachment Filename Ambiguity**:
   - *Challenge*: Attachment names in the dataset (e.g. `attachment_1.txt`, `doc_2.pdf`) don't explicitly state whether they are an SI or a draft BL.
   - *Solution*: Developed a document structure scanner that analyzes header keywords inside the document text to dynamically identify SI vs. BL document roles.

2. **Field Label Heterogeneity**:
   - *Challenge*: Shipping lines use over 30 variations for field headers (e.g. `Exporter`, `Shipper Name`, `Place of Loading`, `Discharge Port`).
   - *Solution*: Built a flexible dictionary alias map in `src/extractor.py` that normalizes label variations to the 7 canonical target fields.

3. **Over-Escalation vs. Precision Balance**:
   - *Challenge*: Initial extraction logic flagged valid documents as `NEEDS_REVIEW` due to minor text formatting differences, resulting in low precision.
   - *Solution*: Implemented fuzzy matching thresholds and numeric unit converters, reducing false positive review flags while retaining **100% catch rate on true unreadable/corrupted files**.

---

## 🔮 Future Roadmap

* **🤖 LLM Vision & OCR Integration**: Integrate Google Gemini API / Vision OCR (`pytesseract` + `pdf2image`) to process low-resolution scanned image PDFs and handwritten Bill of Lading notes.
* **🔗 ERP & Customs API Connectors**: Build direct webhooks into SAP Transportation Management and Oracle Logistics to push verified BL details automatically.
* **🌍 Multi-Language Document Translation**: Expand field extractor to parse multi-lingual shipping documents in Spanish, Mandarin, and French.
* **✉️ Autonomous Email Response Drafting**: Automatically generate drafted email replies to shippers detailing flagged discrepancies for instant resolution.

---

## 📁 Project Repository Layout

```
.
├── README.md                   # System Architecture, Technical Specs & Roadmap
├── GETTING_STARTED.md          # Developer Guide & Execution Commands
├── TEAM_ROADMAP.md             # Team Task Breakdown
├── vercel.json                 # Vercel Serverless Deployment Config
├── requirements.txt            # Python Dependencies
├── api/
│   └── index.py                # Serverless Function Entry Point
├── sdoc-hackathon-bundle/      # Dataset & static sample files
├── sdoc-hackathon-docker/      # Local Evaluation Server (Docker Compose)
└── shipping-verification/      # Core Verification Engine
    ├── main.py                 # Main execution pipeline
    ├── loader.py               # Integrated loader module
    ├── requirements.txt        # Subproject dependencies
    ├── src/
    │   ├── classifier.py       # 5-Category email classifier
    │   ├── parser.py           # Multi-format document parser
    │   ├── extractor.py        # 7-Field extraction engine
    │   ├── comparator.py       # Discrepancy comparison & urgency engine
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
*Developed by Team Pai-piriyargal*
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
4. **Discrepancy Comparison Engine**: Identifying mismatches side-by-side with high precision and fuzzy matching.
5. **Human-in-the-Loop Operations Dashboard**: Escalating uncertain cases (`NEEDS_REVIEW`) with urgency scoring and clear audit trails for operator confirmation.

---

## 🏗 Technical Architecture

```
                               ┌─────────────────────────┐
                               │     Incoming Email      │
                               └────────────┬────────────┘
                                            │
                                  ┌─────────▼─────────┐
                                  │ Email Classifier  │ (5-Category Intent Engine)
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
                                │  Field Extractor  │ (Alias Map & Normalization)
                                └───┬───────────────┘
                                    │
                                    ▼
                                ┌───────────────────┐
                                │ Document          │ (Fuzzy Match & Numeric
                                │ Comparator        │  Threshold Engine)
                                └───┬───────────────┘
                                    │
               ┌────────────────────┼────────────────────┐
               │                    │                    │
          [Status: OK]      [Status: MISMATCH]   [Status: NEEDS_REVIEW]
         No Discrepancies     Defect Flagged      Missing Attachment /
               │                    │              Unreadable / Missing Val
               │                    │                    │
               └────────────────────┴────────────────────┘
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │ Human-in-the-Loop     │
                        │ Review Dashboard UI   │ (FastAPI & Serverless Vercel)
                        └───────────────────────┘
```

The system employs a decoupled, modular microservice architecture built in Python:
- **Ingestion Layer (`loader.py`)**: Supports both local static bundle directory reading and HTTP API dataset ingestion over Docker/REST endpoints.
- **Classification Engine (`src/classifier.py`)**: Multi-layered regex and intent classifier to route email records.
- **Multi-Format Extraction Pipeline (`src/parser.py` & `src/extractor.py`)**: Converts PDF tables, Word text, and text attachments into standardized key-value JSON schema.
- **Comparison & Urgency Engine (`src/comparator.py`)**: Computes field-level discrepancies, assigns urgency scores (`HIGH`, `MEDIUM`, `LOW`), and generates human-readable review explanations.
- **Operational Dashboard (`src/dashboard.py` & `api/index.py`)**: High-performance FastAPI Web UI with glassmorphism UI design, operator overrides, and Vercel serverless deployment capabilities.

---

## 🛠 Implementation Details

### 1. 5-Category Email Classifier (`src/classifier.py`)
- Categorizes messages into `SPAM`, `INVOICE_QUERY`, `SI_REQUEST`, `BL_COMPARISON`, and `GENERAL`.
- Differentiates between emails referencing final tracking numbers vs. explicit requests to review draft BLs.

### 2. Multi-Format Document Ingestion (`src/parser.py`)
- Reads raw text (`.txt`), extractable PDFs (`PyPDF2`), Word documents (`python-docx`), and tabular spreadsheets (`pandas`).
- Handles corrupted, empty, or unreadable attachments gracefully by triggering explicit `unreadable` review escalations.

### 3. 7-Field Data Normalization Engine (`src/extractor.py`)
- Extracts required shipment fields: `shipper`, `consignee`, `notify_party`, `port_of_loading`, `port_of_discharge`, `container_count`, and `gross_weight_kg`.
- Resolves synonym aliases (e.g., `Load Port` = `Port of Loading`, `POD` = `Port of Discharge`).
- Converts weight units automatically (e.g., `LBS` or `MT` converted to standard `KG`) and strips container size descriptions (`20' Standard Container x 4` -> `4`).
- Handles complex legal clauses such as `"SAME AS CONSIGNEE"` by automatically resolving values.

### 4. Discrepancy & Urgency Scoring (`src/comparator.py`)
- Uses **RapidFuzz** fuzzy ratio matching (85%+ threshold) for company names and addresses to account for minor typos.
- Uses numeric tolerance thresholds for weight variations (< 1% variation allowed).
- Assigns priority badges:
  - 🚨 `HIGH`: Critical field mismatches (`consignee`, `port_of_discharge`, `gross_weight_kg`) or unreadable documents.
  - ⚠️ `MEDIUM`: Non-critical missing values or operational requests.
  - ℹ️ `LOW`: Clean verification checks (`OK`).

### 5. Operator Web UI & Serverless Deployment (`src/dashboard.py` & `vercel.json`)
- Interactive FastAPI dashboard showcasing real-time metrics, defect tables, urgency filters, and side-by-side evidence modals.
- Allows operators to perform manual value overrides and write corrections directly into `submission.json`.

---

## ⚠️ Challenges Faced & Solutions

1. **Attachment Filename Ambiguity**:
   - *Challenge*: Attachment names in the dataset (e.g. `attachment_1.txt`, `doc_2.pdf`) don't explicitly state whether they are an SI or a draft BL.
   - *Solution*: Developed a document structure scanner that analyzes header keywords inside the document text to dynamically identify SI vs. BL document roles.

2. **Field Label Heterogeneity**:
   - *Challenge*: Shipping lines use over 30 variations for field headers (e.g. `Exporter`, `Shipper Name`, `Place of Loading`, `Discharge Port`).
   - *Solution*: Built a flexible dictionary alias map in `src/extractor.py` that normalizes label variations to the 7 canonical target fields.

3. **Over-Escalation vs. Precision Balance**:
   - *Challenge*: Initial extraction logic flagged valid documents as `NEEDS_REVIEW` due to minor text formatting differences, resulting in low precision.
   - *Solution*: Implemented fuzzy matching thresholds and numeric unit converters, reducing false positive review flags while retaining **100% catch rate on true unreadable/corrupted files**.

---

## 🔮 Future Roadmap

* **🤖 LLM Vision & OCR Integration**: Integrate Google Gemini API / Vision OCR (`pytesseract` + `pdf2image`) to process low-resolution scanned image PDFs and handwritten Bill of Lading notes.
* **🔗 ERP & Customs API Connectors**: Build direct webhooks into SAP Transportation Management and Oracle Logistics to push verified BL details automatically.
* **🌍 Multi-Language Document Translation**: Expand field extractor to parse multi-lingual shipping documents in Spanish, Mandarin, and French.
* **✉️ Autonomous Email Response Drafting**: Automatically generate drafted email replies to shippers detailing flagged discrepancies for instant resolution.

---

## 📁 Project Repository Layout

```
.
├── README.md                   # System Architecture, Technical Specs & Roadmap
├── GETTING_STARTED.md          # Developer Guide & Execution Commands
├── TEAM_ROADMAP.md             # Team Task Breakdown
├── vercel.json                 # Vercel Serverless Deployment Config
├── requirements.txt            # Python Dependencies
├── api/
│   └── index.py                # Serverless Function Entry Point
├── sdoc-hackathon-bundle/      # Dataset & static sample files
├── sdoc-hackathon-docker/      # Local Evaluation Server (Docker Compose)
└── shipping-verification/      # Core Verification Engine
    ├── main.py                 # Main execution pipeline
    ├── loader.py               # Integrated loader module
    ├── requirements.txt        # Subproject dependencies
    ├── src/
    │   ├── classifier.py       # 5-Category email classifier
    │   ├── parser.py           # Multi-format document parser
    │   ├── extractor.py        # 7-Field extraction engine
    │   ├── comparator.py       # Discrepancy comparison & urgency engine
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
*Developed by Team Pai-piriyargal*
