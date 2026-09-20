# Shipping Document Verification Pipeline (`shipping-verification`)

An automated AI/NLP pipeline for verifying shipping operations emails, extracting key shipment fields across Shipping Instructions (SI) and Bills of Lading (BL), detecting discrepancies, and escalating ambiguous cases for human-in-the-loop review.

---

## 📌 Features

1. **Email Classification (Stage 1)**:
   Classifies incoming operation inbox emails into 5 distinct categories:
   - `BL_COMPARISON`: Verification request for SI vs draft BL.
   - `SI_REQUEST`: Request to create/submit new Shipping Instruction.
   - `INVOICE_QUERY`: Invoice, billing, freight rate, or local charge inquiries.
   - `GENERAL`: General tracking summaries, operational updates, general correspondence.
   - `SPAM`: Unsolicited, promotional, or phishing emails.

2. **Multi-Format Ingestion & Parsing (Stage 2)**:
   Supports ingestion of plain text (`.txt`), PDF (`.pdf`), Word (`.docx`), and Excel (`.xlsx`) documents. Corrupt or unreadable files are escalated cleanly.

3. **7-Field Structured Extraction (Stage 3)**:
   Extracts and normalizes the core 7 shipment fields with alias resolution:
   - `shipper` (Shipper / Exporter)
   - `consignee` (Consignee / To the Order of)
   - `notify_party` (Notify Party / Same as Consignee)
   - `port_of_loading` (Port of Loading / POL / Load Port)
   - `port_of_discharge` (Port of Discharge / POD / Discharge Port)
   - `container_count` (Total Containers / Quantity)
   - `gross_weight_kg` (Gross Weight KG / Gross Wt)

4. **Smart Comparison & Defect Detection (Stage 4)**:
   - Evaluates SI vs BL field alignment.
   - Generates status: `OK`, `MISMATCH`, or `NEEDS_REVIEW`.
   - Captures `review_reason`: `missing_attachment`, `wrong_doc_type`, `unreadable`, or `missing_value`.
   - Surfacing explicit `defect_fields` side-by-side.

5. **Human-in-the-Loop Review Dashboard (Stage 5)**:
   FastAPI web dashboard allowing operations staff to inspect flagged cases, edit corrected fields, and update evaluation reports.

---

## 🛠 Project Structure

```
shipping-verification/
├── main.py               # End-to-end execution pipeline
├── loader.py             # Data loader (supports static bundle & Docker HTTP server)
├── requirements.txt      # Python dependencies
├── README.md             # Subproject documentation
├── src/
│   ├── __init__.py
│   ├── classifier.py     # Email classification engine
│   ├── parser.py         # Multi-format document parser
│   ├── extractor.py      # Field extraction & normalization engine
│   ├── comparator.py     # Discrepancy detector & reliability evaluator
│   └── dashboard.py      # Human-in-the-loop review dashboard
└── tests/
    └── test_pipeline.py  # Unit test suite
```

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Main Pipeline
```bash
python main.py ../sdoc-hackathon-bundle
```
This generates `submission.json` matching the `sample_submission.json` format.

### 3. Run Automated Unit Tests
```bash
python -m unittest discover -s tests
```

### 4. Launch Human-in-the-Loop Review Dashboard
```bash
python src/dashboard.py
```
Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.
