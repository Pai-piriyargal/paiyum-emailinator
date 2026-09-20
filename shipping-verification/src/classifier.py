import re

class EmailClassifier:
    """
    Classifies inbox emails into 5 categories:
    - BL_COMPARISON
    - SI_REQUEST
    - INVOICE_QUERY
    - GENERAL
    - SPAM
    """
    def __init__(self):
        self.spam_keywords = [
            r"\bweird trick\b", r"\blottery\b", r"\bwinner\b", r"\bmillion dollars\b",
            r"\bcrypto\b", r"\bcasino\b", r"\bseo ranking\b", r"\bweight loss\b",
            r"\bdiscount code\b", r"\bclick here\b", r"\burgent action required\b",
            r"\bverify your bank account\b"
        ]

        self.si_request_keywords = [
            r"\brequest si\b", r"\bsi needed\b", r"\bplease provide si\b",
            r"\bsubmit si\b", r"\bneed si\b", r"\bsi request\b", r"\bsi required\b",
            r"\bsubmit si & aed\b", r"\bsi submission\b"
        ]

        self.bl_comparison_keywords = [
            r"\bto confirm docs\b", r"\brequest bl draft\b", r"\bdraft bl\b",
            r"\bcheck bl\b", r"\bcheck details and confirm\b", r"\battached are the si and draft bl\b",
            r"\bbl comparison\b", r"\bconfirm bl\b", r"\bbl draft request\b",
            r"\bamend bl\b", r"\bverify docs\b", r"\bcheck draft\b"
        ]

        self.invoice_keywords = [
            r"\binvoice\b", r"\bfreight charge\b", r"\blocal charge\b", r"\btelex release charge\b",
            r"\bdemurrage\b", r"\bd&d charge\b", r"\bbilling\b", r"\btariff\b", r"\breceipt\b",
            r"\btotal freight\b", r"\bpayment terms\b"
        ]

    def classify(self, email_record):
        subject = email_record.get("subject", "").lower()
        body = email_record.get("body", "").lower()
        attachments = email_record.get("attachments", [])
        combined_text = f"{subject} {body}"

        # 1. SPAM check
        for pattern in self.spam_keywords:
            if re.search(pattern, combined_text):
                return "SPAM"

        # 2. SI_REQUEST check (high priority if explicitly asking for SI submission)
        for pattern in self.si_request_keywords:
            if re.search(pattern, combined_text):
                return "SI_REQUEST"

        # 3. BL_COMPARISON check
        for pattern in self.bl_comparison_keywords:
            if re.search(pattern, combined_text):
                return "BL_COMPARISON"

        # If attachments contain both SI and BL references, likely BL_COMPARISON
        att_str = " ".join(attachments).lower()
        if ("si" in att_str or "shipping_instruction" in att_str) and ("bl" in att_str or "bill_of_lading" in att_str):
            return "BL_COMPARISON"

        # 4. INVOICE_QUERY check
        for pattern in self.invoice_keywords:
            if re.search(pattern, combined_text):
                return "INVOICE_QUERY"

        # 5. Default to GENERAL
        return "GENERAL"
