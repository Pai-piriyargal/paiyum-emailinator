import re

try:
    from rapidfuzz import fuzz
    def calculate_similarity(s1, s2):
        return fuzz.token_sort_ratio(s1, s2)
except ImportError:
    import difflib
    def calculate_similarity(s1, s2):
        # Fallback ratio using standard library difflib
        s1_words = " ".join(sorted(s1.split()))
        s2_words = " ".join(sorted(s2.split()))
        return difflib.SequenceMatcher(None, s1_words, s2_words).ratio() * 100

UNLOCODE_MAP = {
    "CNNTG": "NANTONG",
    "CNSHA": "SHANGHAI",
    "CNNBO": "NINGBO",
    "CNQGD": "QINGDAO",
    "CNTXG": "TIANJIN",
    "CNXMN": "XIAMEN",
    "PKKHI": "KARACHI",
    "SGSIN": "SINGAPORE",
    "USLAX": "LOS ANGELES",
    "USNYC": "NEW YORK",
    "NLRTM": "ROTTERDAM",
    "DEHAM": "HAMBURG",
    "MYPKG": "PORT KLANG",
    "INBOM": "MUMBAI",
    "INNSA": "NHAVA SHEVA",
    "AEDXB": "DUBAI",
    "JMKIN": "KINGSTON",
    "EGALY": "ALEXANDRIA",
    "ESBCN": "BARCELONA",
    "GBFXT": "FELIXSTOWE",
}


def strip_corporate_suffixes(val_str):
    """
    Strips corporate suffixes (e.g. LTD, INC, CORP, LLC, PLC, PTE, PVT, CO, COMPANY, GMBH, S.A.)
    from company names before text comparison.
    """
    if not val_str:
        return ""
    cleaned = re.sub(
        r"\b(LTD|LIMITED|INC|INCORPORATED|CORP|CORPORATION|LLC|PLC|PTE|PVT|CO|COMPANY|GMBH|S\.A\.)\.?\b",
        "",
        str(val_str),
        flags=re.IGNORECASE
    )
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


class DocumentComparator:
    """
    Compares extracted SI fields vs BL fields for the 7 required fields.
    Evaluates OK, MISMATCH, or NEEDS_REVIEW status with human-readable explanations & urgency.
    """
    REQUIRED_FIELDS = [
        "shipper",
        "consignee",
        "notify_party",
        "port_of_loading",
        "port_of_discharge",
        "container_count",
        "gross_weight_kg"
    ]

    def compare(self, si_fields, bl_fields):
        """
        Compares SI fields against BL fields.
        Returns tuple: (status, review_reason, has_defect, defect_fields)
        """
        res = self.compare_with_details(si_fields, bl_fields)
        return res[0], res[1], res[2], res[3]

    def compare_with_details(self, si_fields, bl_fields):
        """
        Compares SI fields against BL fields.
        Returns tuple: (status, review_reason, has_defect, defect_fields, explanation, urgency_score)
        """
        # Check missing values
        missing_in_si = [f for f in self.REQUIRED_FIELDS if f not in si_fields or si_fields[f] is None]
        missing_in_bl = [f for f in self.REQUIRED_FIELDS if f not in bl_fields or bl_fields[f] is None]

        if missing_in_si or missing_in_bl:
            explanation, urgency = self.get_review_details(
                "missing_value", missing_in_si=missing_in_si, missing_in_bl=missing_in_bl
            )
            return ("NEEDS_REVIEW", "missing_value", False, [], explanation, urgency)

        defect_fields = []

        for field in self.REQUIRED_FIELDS:
            val_si = si_fields[field]
            val_bl = bl_fields[field]

            if not self._values_match(field, val_si, val_bl):
                defect_fields.append(field)

        if defect_fields:
            return ("MISMATCH", None, True, defect_fields, None, None)
        else:
            return ("OK", None, False, [], None, None)

    def get_review_details(self, review_reason, missing_in_si=None, missing_in_bl=None):
        """
        Generates a human-readable explanation and an urgency score (HIGH, MEDIUM, LOW)
        for any case flagged as NEEDS_REVIEW.
        """
        if not review_reason:
            return None, None

        missing_in_si = missing_in_si or []
        missing_in_bl = missing_in_bl or []

        if review_reason == "missing_attachment":
            return (
                "One or more required shipping documents (SI or draft BL) are missing from the email attachments.",
                "HIGH"
            )
        elif review_reason == "unreadable":
            return (
                "One or more email attachments could not be read or parsed due to file corruption or unsupported formatting.",
                "HIGH"
            )
        elif review_reason == "wrong_doc_type":
            return (
                "The email attachments do not contain the required combination of Shipping Instruction (SI) and Bill of Lading (BL).",
                "MEDIUM"
            )
        elif review_reason == "missing_value":
            missing_all = sorted(list(set(missing_in_si + missing_in_bl)))
            missing_str = ", ".join(missing_all) if missing_all else "required fields"
            explanation = f"Mandatory shipment fields ({missing_str}) could not be extracted from the SI or BL document."
            
            critical_fields = {"shipper", "consignee", "container_count", "gross_weight_kg"}
            if any(f in critical_fields for f in missing_all):
                urgency = "HIGH"
            else:
                urgency = "MEDIUM"
            return (explanation, urgency)
        else:
            return (f"Case flagged for review due to reason: {review_reason}.", "MEDIUM")

    def _values_match(self, field_name, val_si, val_bl):
        """Checks equality/similarity for a given field."""
        if val_si is None or val_bl is None:
            return False

        if field_name == "container_count":
            return int(val_si) == int(val_bl)

        elif field_name == "gross_weight_kg":
            return abs(float(val_si) - float(val_bl)) < 0.5

        else:
            # Clean string comparisons
            s1 = self._clean_str(val_si)
            s2 = self._clean_str(val_bl)

            if s1 == s2:
                return True

            # Party name suffix normalization (shipper, consignee, notify_party)
            if field_name in ["shipper", "consignee", "notify_party"]:
                s1_stripped = strip_corporate_suffixes(s1)
                s2_stripped = strip_corporate_suffixes(s2)
                if s1_stripped == s2_stripped:
                    return True
                if calculate_similarity(s1_stripped, s2_stripped) >= 90:
                    return True

            # Port code equivalence check e.g. "NANTONG, CHINA (CNNTG)" vs "NANTONG, CHINA"
            if "port" in field_name:
                s1_clean = re.sub(r"\s*\([A-Z0-9]+\)", "", s1).strip()
                s2_clean = re.sub(r"\s*\([A-Z0-9]+\)", "", s2).strip()
                if s1_clean == s2_clean:
                    return True

                # UN/LOCODE lookup checking
                locodes_s1 = re.findall(r"\b([A-Z]{5})\b", s1)
                locodes_s2 = re.findall(r"\b([A-Z]{5})\b", s2)

                for code in locodes_s1:
                    mapped = UNLOCODE_MAP.get(code)
                    if mapped and (mapped in s2 or mapped in s2_clean):
                        return True
                for code in locodes_s2:
                    mapped = UNLOCODE_MAP.get(code)
                    if mapped and (mapped in s1 or mapped in s1_clean):
                        return True

            # Similarity threshold (90+) for slight spacing / typo variations
            similarity = calculate_similarity(s1, s2)
            return similarity >= 90

    def _clean_str(self, val):
        val_str = str(val).upper().strip()
        # Remove common non-essential qualifiers
        val_str = re.sub(r"\(NON-NEGOTIABLE\)", "", val_str)
        val_str = re.sub(r"\s+", " ", val_str)
        return val_str.strip()

