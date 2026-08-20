"""Safe frontend presentation helpers for Chama Yetu."""
import pandas as pd

INTERNAL_COLUMNS = {
    "id", "group_id", "user_id", "member_id", "role_id", "investment_id",
    "loan_id", "application_id", "contribution_type_id", "schedule_id",
    "payment_id", "journal_id", "account_id", "import_batch_id",
    "created_by", "updated_by", "submitted_by", "verified_by", "approved_by",
    "decided_by", "disbursed_by", "posted_by", "assigned_by", "source_id",
    "reversal_of", "old_values", "new_values"
}

def public_frame(rows, preferred=None, rename=None):
    data = pd.DataFrame(rows or [])
    if data.empty:
        return data
    if preferred:
        columns = [column for column in preferred if column in data.columns]
    else:
        columns = [column for column in data.columns if column not in INTERNAL_COLUMNS and not column.endswith("_id")]
    data = data.loc[:, columns].copy()
    return data.rename(columns=rename or {})

MEMBER_COLUMNS = ["membership_number", "full_name", "email", "phone", "status", "date_joined"]
MEMBER_LABELS = {
    "membership_number": "Member Code", "full_name": "Full Name",
    "email": "Email", "phone": "Phone", "status": "Status",
    "date_joined": "Date Joined"
}
