#!/usr/bin/env python3
"""
main.py — End-to-end Shipping Document Verification Pipeline
"""
import json
import os
import sys
from pathlib import Path

# Add current directory and src to sys.path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

from loader import Inbox
from src.classifier import EmailClassifier
from src.parser import DocumentParser
from src.extractor import FieldExtractor
from src.comparator import DocumentComparator


def run_pipeline(data_source="sdoc-hackathon-bundle", output_file="submission.json"):
    print(f"Loading dataset from: {data_source}...")
    inbox = Inbox(data_source)

    classifier = EmailClassifier()
    parser = DocumentParser(inbox_instance=inbox)
    extractor = FieldExtractor()
    comparator = DocumentComparator()

    submission = {}
    stats = {
        "categories": {},
        "statuses": {},
        "review_reasons": {},
        "defects": {}
    }

    emails = inbox.emails()
    print(f"Processing {len(emails)} emails...")

    for email in emails:
        eid = email["email_id"]
        cat = classifier.classify(email)

        stats["categories"][cat] = stats["categories"].get(cat, 0) + 1

        if cat != "BL_COMPARISON":
            submission[eid] = {
                "category": cat,
                "status": "OK",
                "review_reason": None,
                "has_defect": False,
                "defect_fields": []
            }
            stats["statuses"]["OK"] = stats["statuses"].get("OK", 0) + 1
            continue

        # BL_COMPARISON email processing
        atts = email.get("attachments", [])

        # 1. Attachment check
        if len(atts) < 2:
            expl, urgency = comparator.get_review_details("missing_attachment")
            submission[eid] = {
                "category": "BL_COMPARISON",
                "status": "NEEDS_REVIEW",
                "review_reason": "missing_attachment",
                "has_defect": False,
                "defect_fields": [],
                "explanation": expl,
                "urgency_score": urgency
            }
            stats["statuses"]["NEEDS_REVIEW"] = stats["statuses"].get("NEEDS_REVIEW", 0) + 1
            stats["review_reasons"]["missing_attachment"] = stats["review_reasons"].get("missing_attachment", 0) + 1
            continue

        # 2. Parse attachments
        parsed_docs = []
        for att in atts:
            text = parser.parse(att)
            doc_type = extractor.identify_doc_type(att, text or "")
            parsed_docs.append({
                "path": att,
                "text": text,
                "type": doc_type
            })

        # Check unreadable
        if any(d["text"] is None for d in parsed_docs):
            expl, urgency = comparator.get_review_details("unreadable")
            submission[eid] = {
                "category": "BL_COMPARISON",
                "status": "NEEDS_REVIEW",
                "review_reason": "unreadable",
                "has_defect": False,
                "defect_fields": [],
                "explanation": expl,
                "urgency_score": urgency
            }
            stats["statuses"]["NEEDS_REVIEW"] = stats["statuses"].get("NEEDS_REVIEW", 0) + 1
            stats["review_reasons"]["unreadable"] = stats["review_reasons"].get("unreadable", 0) + 1
            continue

        # 3. Identify SI and BL docs
        si_doc = next((d for d in parsed_docs if d["type"] == "SI"), None)
        bl_doc = next((d for d in parsed_docs if d["type"] == "BL"), None)

        if not si_doc or not bl_doc:
            expl, urgency = comparator.get_review_details("wrong_doc_type")
            submission[eid] = {
                "category": "BL_COMPARISON",
                "status": "NEEDS_REVIEW",
                "review_reason": "wrong_doc_type",
                "has_defect": False,
                "defect_fields": [],
                "explanation": expl,
                "urgency_score": urgency
            }
            stats["statuses"]["NEEDS_REVIEW"] = stats["statuses"].get("NEEDS_REVIEW", 0) + 1
            stats["review_reasons"]["wrong_doc_type"] = stats["review_reasons"].get("wrong_doc_type", 0) + 1
            continue

        # 4. Extract fields
        si_fields = extractor.extract_fields(si_doc["text"])
        bl_fields = extractor.extract_fields(bl_doc["text"])

        # 5. Compare fields
        status, review_reason, has_defect, defect_fields, explanation, urgency_score = comparator.compare_with_details(
            si_fields, bl_fields
        )

        entry = {
            "category": "BL_COMPARISON",
            "status": status,
            "review_reason": review_reason,
            "has_defect": has_defect,
            "defect_fields": defect_fields
        }
        if status == "NEEDS_REVIEW":
            entry["explanation"] = explanation
            entry["urgency_score"] = urgency_score

        submission[eid] = entry

        stats["statuses"][status] = stats["statuses"].get(status, 0) + 1
        if review_reason:
            stats["review_reasons"][review_reason] = stats["review_reasons"].get(review_reason, 0) + 1
        for f in defect_fields:
            stats["defects"][f] = stats["defects"].get(f, 0) + 1

    # Write output JSON files
    output_path = Path(output_file)
    output_path.write_text(json.dumps(submission, indent=2), encoding="utf-8")
    print(f"Successfully saved submission to: {output_path.absolute()}")

    # Also save to root submission.json and local output.json
    root_sub_path = Path(__file__).parent.parent / "submission.json"
    root_sub_path.write_text(json.dumps(submission, indent=2), encoding="utf-8")

    output_json_path = Path(__file__).parent / "output.json"
    output_json_path.write_text(json.dumps(submission, indent=2), encoding="utf-8")

    # Print summary
    print("\n================ PIPELINE RUN SUMMARY ================")
    print("Categories breakdown:", json.dumps(stats["categories"], indent=2))
    print("Status breakdown:", json.dumps(stats["statuses"], indent=2))
    print("Review reasons:", json.dumps(stats["review_reasons"], indent=2))
    print("Defect fields detected:", json.dumps(stats["defects"], indent=2))
    print("======================================================")

    return submission, stats


if __name__ == "__main__":
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "sdoc-hackathon-bundle"
    run_pipeline(data_dir)

