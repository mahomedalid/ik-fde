from datetime import date

# Simplified interview rule, NOT a production Regulation E compliance decision.
# No credit-posting field, exceptions, or bank holiday calendar is modeled.
# Return the dispute_ids that are BREACHED:
#   more than 10 business days (Mon-Fri) elapsed between filed_date and TODAY,
#   AND status is not 'resolved'.
#
# The CSV is a synthetic messy export. Inspect it before you trust it.
# Ask the interviewer to pin down boundaries, invalid rows, and duplicate IDs.

TODAY = date(2026, 6, 29)  # hardcode for deterministic grading

def flag_reg_e(path: str) -> list:
    # drive your AI assistant to implement this.
    ...

if __name__ == "__main__":
    print(flag_reg_e("disputes_messy.csv"))
