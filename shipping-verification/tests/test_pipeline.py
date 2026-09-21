import unittest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from classifier import EmailClassifier
from extractor import FieldExtractor
from comparator import DocumentComparator

class TestShippingPipeline(unittest.TestCase):
    def setUp(self):
        self.classifier = EmailClassifier()
        self.extractor = FieldExtractor()
        self.comparator = DocumentComparator()

    def test_classifier(self):
        email_spam = {"subject": "Increase your shipping revenue with this ONE weird trick", "body": "", "attachments": []}
        email_bl = {"subject": "TO CONFIRM DOCS _ 5RSG-00133", "body": "Attached draft BL", "attachments": ["a.txt", "b.txt"]}
        email_si = {"subject": "REQUEST SI _ 5RFR-37631", "body": "Please provide SI", "attachments": []}

        self.assertEqual(self.classifier.classify(email_spam), "SPAM")
        self.assertEqual(self.classifier.classify(email_bl), "BL_COMPARISON")
        self.assertEqual(self.classifier.classify(email_si), "SI_REQUEST")

    def test_extractor_normalization(self):
        self.assertEqual(self.extractor.normalize_value("container_count", "6 x 40'HC"), 6)
        self.assertEqual(self.extractor.normalize_value("gross_weight_kg", "131,058 KG"), 131058.0)
        self.assertEqual(self.extractor.normalize_value("shipper", "  April Far East  "), "APRIL FAR EAST")

    def test_comparator_ok(self):
        si = {
            "shipper": "APRIL FAR EAST",
            "consignee": "EAST BRIGHT FZ-LLC",
            "notify_party": "EAST BRIGHT FZ-LLC",
            "port_of_loading": "NANTONG, CHINA (CNNTG)",
            "port_of_discharge": "KARACHI, PAKISTAN (PKKHI)",
            "container_count": 6,
            "gross_weight_kg": 131058.0
        }
        bl = dict(si)
        bl["port_of_loading"] = "NANTONG, CHINA"  # Equivalent port representation

        status, reason, has_defect, defect_fields = self.comparator.compare(si, bl)
        self.assertEqual(status, "OK")
        self.assertFalse(has_defect)
        self.assertEqual(defect_fields, [])

    def test_comparator_mismatch(self):
        si = {
            "shipper": "APRIL FAR EAST",
            "consignee": "EAST BRIGHT FZ-LLC",
            "notify_party": "EAST BRIGHT FZ-LLC",
            "port_of_loading": "NANTONG, CHINA",
            "port_of_discharge": "KARACHI, PAKISTAN",
            "container_count": 6,
            "gross_weight_kg": 131058.0
        }
        bl = dict(si)
        bl["consignee"] = "UAB NOVAKOPA"  # Mismatched consignee

        status, reason, has_defect, defect_fields = self.comparator.compare(si, bl)
        self.assertEqual(status, "MISMATCH")
        self.assertTrue(has_defect)
        self.assertIn("consignee", defect_fields)

    def test_corporate_suffix_stripping(self):
        si = {
            "shipper": "APRIL FAR EAST LTD",
            "consignee": "EAST BRIGHT INC",
            "notify_party": "EAST BRIGHT CORP",
            "port_of_loading": "NANTONG, CHINA",
            "port_of_discharge": "KARACHI, PAKISTAN",
            "container_count": 6,
            "gross_weight_kg": 131058.0
        }
        bl = {
            "shipper": "APRIL FAR EAST INC",
            "consignee": "EAST BRIGHT LLC",
            "notify_party": "EAST BRIGHT COMPANY",
            "port_of_loading": "NANTONG, CHINA",
            "port_of_discharge": "KARACHI, PAKISTAN",
            "container_count": 6,
            "gross_weight_kg": 131058.0
        }
        status, reason, has_defect, defect_fields = self.comparator.compare(si, bl)
        self.assertEqual(status, "OK")
        self.assertFalse(has_defect)

    def test_unlocode_lookup(self):
        si = {
            "shipper": "APRIL FAR EAST",
            "consignee": "EAST BRIGHT",
            "notify_party": "EAST BRIGHT",
            "port_of_loading": "CNNTG",  # Maps to NANTONG
            "port_of_discharge": "KARACHI, PAKISTAN (PKKHI)",
            "container_count": 6,
            "gross_weight_kg": 131058.0
        }
        bl = {
            "shipper": "APRIL FAR EAST",
            "consignee": "EAST BRIGHT",
            "notify_party": "EAST BRIGHT",
            "port_of_loading": "NANTONG PORT, CHINA",
            "port_of_discharge": "KARACHI",
            "container_count": 6,
            "gross_weight_kg": 131058.0
        }
        status, reason, has_defect, defect_fields = self.comparator.compare(si, bl)
        self.assertEqual(status, "OK")

    def test_needs_review_explanation_and_urgency(self):
        expl_att, urg_att = self.comparator.get_review_details("missing_attachment")
        self.assertEqual(urg_att, "HIGH")
        self.assertIn("missing", expl_att)

        expl_unread, urg_unread = self.comparator.get_review_details("unreadable")
        self.assertEqual(urg_unread, "HIGH")

        expl_val, urg_val = self.comparator.get_review_details(
            "missing_value", missing_in_si=["consignee"]
        )
        self.assertEqual(urg_val, "HIGH")
        self.assertIn("consignee", expl_val)

        status, reason, has_defect, defect_fields, expl, urgency = self.comparator.compare_with_details(
            {"shipper": None}, {"shipper": "APRIL"}
        )
        self.assertEqual(status, "NEEDS_REVIEW")
        self.assertEqual(reason, "missing_value")
        self.assertEqual(urgency, "HIGH")
        self.assertIsNotNone(expl)

if __name__ == "__main__":
    unittest.main()

