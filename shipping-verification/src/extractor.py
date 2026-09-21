import re

class FieldExtractor:
    """
    Extracts the 7 shipping fields from text documents:
    - shipper
    - consignee
    - notify_party
    - port_of_loading
    - port_of_discharge
    - container_count
    - gross_weight_kg
    """
    def __init__(self):
        self.alias_map = {
            "shipper": [
                "shipper/exporter", "shipper", "exporter", "seller", "shipper name", "company name"
            ],
            "consignee": [
                "consignee (non-negotiable)", "consignee", "to the order of", "buyer", "consignee name", "consignee address"
            ],
            "notify_party": [
                "notify party", "notify", "notify_party", "notify party name", "also notify"
            ],
            "port_of_loading": [
                "port of loading (pol)", "port of loading", "pol", "load port", "loading port", "place of receipt", "port of receipt"
            ],
            "port_of_discharge": [
                "discharge port", "port of discharge", "pod", "port of discharge (pod)", "dest port", "destination port", "place of delivery", "final destination"
            ],
            "container_count": [
                "no. of containers or packages", "no. of containers", "total containers", "container count", "containers", "quantity", "container cnt", "no of containers", "packages / containers", "units"
            ],
            "gross_weight_kg": [
                "gross weight (kg)", "gross wt (kgs)", "gross weight", "gross wt", "gross weight(kg)", "total gross weight", "gross weight (kgs)", "weight", "gw"
            ]
        }

    def identify_doc_type(self, path_or_name, text_content=""):
        """
        Determines whether document is 'SI' or 'BL'.
        Returns 'SI', 'BL', or 'UNKNOWN'.
        """
        lower_path = str(path_or_name).lower()
        lower_text = text_content[:500].lower() if text_content else ""

        if "_si" in lower_path or "shipping_instruction" in lower_path or "shipping instruction" in lower_text:
            return "SI"
        elif "_bl" in lower_path or "bill_of_lading" in lower_path or "bill of lading" in lower_text or "draft bl" in lower_text:
            return "BL"
        return "UNKNOWN"

    def extract_fields(self, text):
        """
        Extracts raw and normalized values for the 7 key fields from document text.
        Returns dict of { field_name: value }
        """
        if not text:
            return {}

        extracted = {}
        lines = text.splitlines()
        kv_pairs = {}

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line or line.startswith("="):
                i += 1
                continue

            if ":" in line or "-" in line:
                parts = re.split(r"[:\-]", line, maxsplit=1)
                key = parts[0].strip().lower()
                val = parts[1].strip()

                # Multi-line block check (e.g., address under header)
                if not val and i + 1 < len(lines):
                    next_line = lines[i+1].strip()
                    if next_line and not ((":" in next_line or "-" in next_line) and len(re.split(r"[:\-]", next_line)[0].strip()) < 35):
                        i += 1
                        val = next_line

                kv_pairs[key] = val
            i += 1

        # Match mapped fields using partial prefix & exact alias matching
        for field_name, aliases in self.alias_map.items():
            found_val = None
            for alias in aliases:
                # Direct match or key starts with alias
                for k, v in kv_pairs.items():
                    if k == alias or k.startswith(alias):
                        if v:
                            found_val = v
                            break
                if found_val:
                    break

            # Fallback regex search if not found in key-value pairs
            if not found_val:
                found_val = self._regex_fallback(field_name, text)

            if found_val:
                extracted[field_name] = self.normalize_value(field_name, found_val)

        # Resolve SAME AS CONSIGNEE for notify_party
        if "notify_party" in extracted and extracted["notify_party"]:
            val_str = str(extracted["notify_party"]).upper()
            if "SAME AS CONSIGNEE" in val_str or "SAME AS ABOVE" in val_str:
                if "consignee" in extracted and extracted["consignee"]:
                    extracted["notify_party"] = extracted["consignee"]

        return extracted

    def _regex_fallback(self, field_name, text):
        """Regex fallback for fields when standard line key-value fails."""
        if field_name == "container_count":
            m = re.search(r"(?:total containers|container count|containers|units)\s*[:\-]?\s*(\d+)", text, re.IGNORECASE)
            if m:
                return m.group(1)
        elif field_name == "gross_weight_kg":
            m = re.search(r"(?:gross weight|gross wt|gw)\s*(?:\([^\)]+\))?\s*[:\-]?\s*([\d,]+(?:\.\d+)?\s*(?:kg|kgs|lbs|mt)?)", text, re.IGNORECASE)
            if m:
                return m.group(1)
        return None

    def normalize_value(self, field_name, val):
        """
        Normalizes extracted field values into standard representation.
        Handles unit conversions (LBS/MT -> KG).
        """
        if val is None:
            return None

        val_str = str(val).strip()

        if field_name == "container_count":
            # Extract container number, e.g. "20' Dry Standard x 4" -> 4 or "6 x 40'HC" -> 6
            m = re.search(r"(\d+)\s*(?:x|units|containers|ctns|40ft|20ft)?", val_str, re.IGNORECASE)
            return int(m.group(1)) if m else None

        elif field_name == "gross_weight_kg":
            # Extract numeric weight and unit (convert LBS / MT to KG)
            clean = val_str.replace(",", "")
            m = re.search(r"(\d+(?:\.\d+)?)\s*(kg|kgs|kilograms|lbs|pound|mt|metric tons)?", clean, re.IGNORECASE)
            if m:
                weight = float(m.group(1))
                unit = m.group(2).lower() if m.group(2) else "kg"

                if unit in ["lbs", "pound"]:
                    weight = weight * 0.453592  # LBS to KG
                elif unit in ["mt", "metric tons"]:
                    weight = weight * 1000.0   # MT to KG

                return round(weight, 2)
            return None

        else:
            # Clean text fields: upper case, collapse extra whitespace
            val_clean = re.sub(r"\s+", " ", val_str).strip().upper()
            return val_clean if val_clean else None