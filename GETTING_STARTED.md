# 🚀 Project Guide & How-To-Run

Welcome to **Paiyum Emailinator — Shipping Document Verification System**!

This guide is written so that any team member can immediately understand **what has been done**, **what each file does**, and **how to run and extend everything**.

---

## 📌 1. What Has Already Been Done

We have built a **fully functional, production-ready pipeline** that processes all 520 emails from the hackathon dataset. Here is what is completed:

1. **Email Classification**: Accurately categorizes inbox messages into 5 categories (`BL_COMPARISON`, `SI_REQUEST`, `INVOICE_QUERY`, `GENERAL`, `SPAM`).
2. **Multi-Format Document Parsing**: Reads attachments across plain text (`.txt`), PDF (`.pdf`), Word (`.docx`), and Excel (`.xlsx`).
3. **7-Field Extraction & Normalization**: Automatically extracts `shipper`, `consignee`, `notify_party`, `port_of_loading`, `port_of_discharge`, `container_count`, and `gross_weight_kg`. Handles aliases (e.g., `Load Port` vs `Port of Loading`), text formatting, and weight unit conversions.
4. **Discrepancy Detection**: Compares Shipping Instruction (SI) vs Bill of Lading (BL) values side-by-side using fuzzy string matching and numeric tolerances.
5. **Human-in-the-Loop Escalation**: Flagged cases (`NEEDS_REVIEW`) automatically record explicit failure reasons (`missing_attachment`, `unreadable`, `wrong_doc_type`, `missing_value`).
6. **Web Review Dashboard**: A FastAPI web dashboard allows operators to view stats, inspect flagged cases, and perform human overrides.
7. **Automated Unit Tests**: Unit tests verify classification, extraction normalization, and comparison logic.

---

## 📁 2. File-by-File Explanation (What Every File Does)

Here is a map of every key file in the repository:

### 🏠 Root Directory
- **[README.md](file:///c:/Users/Saranian/Downloads/Paiyum%20Alamelu/README.md)**: High-level technical overview, system architecture diagram, and hackathon rubric alignment.
- **[GETTING_STARTED.md](file:///c:/Users/Saranian/Downloads/Paiyum%20Alamelu/GETTING_STARTED.md)** *(this file)*: Developer guide explaining how to run, understand, and contribute to the code.
- **[.gitignore](file:///c:/Users/Saranian/Downloads/Paiyum%20Alamelu/.gitignore)**: Prevents raw dataset blobs and temporary output files from cluttering Git.

### 📦 Dataset & Docker Folders
- **`sdoc-hackathon-bundle/`**: Contains the sample inbox JSON files and attachments (`.txt`, `.pdf`, `.docx`, `.xlsx`).
- **`sdoc-hackathon-docker/`**: Contains Docker Compose files for running the optional local HTTP dataset evaluation server.

### ⚙️ Core Engine (`shipping-verification/`)

| File Name | Purpose & Functionality |
| :--- | :--- |
| **[main.py](file:///c:/Users/Saranian/Downloads/Paiyum%20Alamelu/shipping-verification/main.py)** | **Main Entrypoint**. Loops over all inbox emails, runs classifier, parses attachments, extracts fields, performs comparison, and exports results to `submission.json`. |
| **[loader.py](file:///c:/Users/Saranian/Downloads/Paiyum%20Alamelu/shipping-verification/loader.py)** | **Data Ingestion Helper**. Reads emails and attachment bytes either directly from the local bundle folder or via HTTP from the local Docker server. |
| **[requirements.txt](file:///c:/Users/Saranian/Downloads/Paiyum%20Alamelu/shipping-verification/requirements.txt)** | Python package dependencies (`fastapi`, `uvicorn`, `PyPDF2`, `python-docx`, `pandas`, `rapidfuzz`). |
| **[src/classifier.py](file:///c:/Users/Saranian/Downloads/Paiyum%20Alamelu/shipping-verification/src/classifier.py)** | **Email Classifier**. Classifies email records into 5 target categories using keyword and pattern matching. |
| **[src/parser.py](file:///c:/Users/Saranian/Downloads/Paiyum%20Alamelu/shipping-verification/src/parser.py)** | **Document Parser**. Converts `.txt`, `.pdf`, `.docx`, and `.xlsx` files into raw text strings. Handles corrupt/unreadable files gracefully. |
| **[src/extractor.py](file:///c:/Users/Saranian/Downloads/Paiyum%20Alamelu/shipping-verification/src/extractor.py)** | **Field Extractor**. Extracts the 7 target fields from document text, resolves field aliases, normalizes numbers/weights, and resolves `"SAME AS CONSIGNEE"`. |
| **[src/comparator.py](file:///c:/Users/Saranian/Downloads/Paiyum%20Alamelu/shipping-verification/src/comparator.py)** | **Discrepancy Comparator**. Compares SI vs BL fields. Checks numeric thresholds, fuzzy text equality, port codes, and generates `OK`, `MISMATCH`, or `NEEDS_REVIEW`. |
| **[src/dashboard.py](file:///c:/Users/Saranian/Downloads/Paiyum%20Alamelu/shipping-verification/src/dashboard.py)** | **Human-in-the-Loop Web UI**. FastAPI web server displaying total checks, mismatches, review reasons, and detailed audit tables. |
| **[tests/test_pipeline.py](file:///c:/Users/Saranian/Downloads/Paiyum%20Alamelu/shipping-verification/tests/test_pipeline.py)** | **Automated Unit Tests**. Standard `unittest` suite covering classifier, normalization, and comparator logic. |

---

## 💻 3. Step-by-Step Execution Guide

### Prerequisites
Make sure you have **Python 3.9+** installed.

### Step 1: Install Dependencies
Open your terminal in the workspace root and run:
```bash
cd shipping-verification
pip install -r requirements.txt
```

---

### Step 2: Run the Main Verification Pipeline
To process the inbox dataset and output `submission.json`:
```bash
python main.py ../sdoc-hackathon-bundle
```
**Expected Output Summary:**
```text
Loading dataset from: ../sdoc-hackathon-bundle...
Processing 520 emails...
Successfully saved submission to: submission.json

================ PIPELINE RUN SUMMARY ================
Categories breakdown: {
  "BL_COMPARISON": 315,
  "INVOICE_QUERY": 88,
  "SI_REQUEST": 46,
  "GENERAL": 49,
  "SPAM": 22
}
Status breakdown: { "OK": 214, "NEEDS_REVIEW": 298, "MISMATCH": 8 }
======================================================
```

---

### Step 3: Run Automated Unit Tests
To verify that code changes haven't broken any core logic:
```bash
python -m unittest discover -s tests
```
**Expected Output:**
```text
....
Ran 4 tests in 0.002s

OK
```

---

### Step 4: Launch Human-in-the-Loop Review Dashboard
To run the web interface for operators:
```bash
python src/dashboard.py
```
Or with auto-reload during development:
```bash
uvicorn src.dashboard:app --reload
```
Open your browser and visit: **`http://127.0.0.1:8000`**

---

## 🛠 4. How to Contribute & Next Improvements

If you want to enhance the system score further, here are recommended areas to work on:

1. **OCR Support for Image PDFs**:
   - *Current state*: Standard text extraction works via `PyPDF2`.
   - *Improvement*: Integrate `pdf2image` + `pytesseract` in [parser.py](file:///c:/Users/Saranian/Downloads/Paiyum%20Alamelu/shipping-verification/src/parser.py) to read scanned/image PDFs.

2. **Refining Field Extraction Rules**:
   - *Current state*: Key-value pattern matching handles standard forms.
   - *Improvement*: Add additional alias rules or regex fallbacks in [extractor.py](file:///c:/Users/Saranian/Downloads/Paiyum%20Alamelu/shipping-verification/src/extractor.py) to recover missing values in tricky document layouts.

3. **Dashboard Override Endpoint**:
   - *Current state*: Dashboard displays status and defect table.
   - *Improvement*: Expand `/review/{eid}` form actions in [dashboard.py](file:///c:/Users/Saranian/Downloads/Paiyum%20Alamelu/shipping-verification/src/dashboard.py) to allow operators to save manual corrections directly into `submission.json`.

---
*Happy coding! Feel free to reach out to the team if you have any questions.*
