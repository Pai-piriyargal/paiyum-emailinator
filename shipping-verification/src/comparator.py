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

class DocumentComparator:
    """
    Compares extracted SI fields vs BL fields for the 7 required fields.
    Evaluates OK, MISMATCH, or NEEDS_REVIEW status.
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
        # Check missing values
        missing_in_si = [f for f in self.REQUIRED_FIELDS if f not in si_fields or si_fields[f] is None]
        missing_in_bl = [f for f in self.REQUIRED_FIELDS if f not in bl_fields or bl_fields[f] is None]

        if missing_in_si or missing_in_bl:
            return ("NEEDS_REVIEW", "missing_value", False, [])

        defect_fields = []

        for field in self.REQUIRED_FIELDS:
            val_si = si_fields[field]
            val_bl = bl_fields[field]

            if not self._values_match(field, val_si, val_bl):
                defect_fields.append(field)

        if defect_fields:
            return ("MISMATCH", None, True, defect_fields)
        else:
            return ("OK", None, False, [])

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

            # Port code equivalence check e.g. "NANTONG, CHINA (CNNTG)" vs "NANTONG, CHINA"
            if "port" in field_name:
                s1_clean = re.sub(r"\s*\([A-Z0-9]+\)", "", s1).strip()
                s2_clean = re.sub(r"\s*\([A-Z0-9]+\)", "", s2).strip()
                if s1_clean == s2_clean:
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
