import streamlit as st
import pandas as pd
import plotly.express as px
from services.db import get, add, upsert
from services.auth import login, logout

st.set_page_config(page_title="Chama Yetu", page_icon="CY", layout="wide")

INTERNAL_COLUMNS = {
    "id", "group_id", "user_id", "member_id", "role_id", "investment_id",
    "loan_id", "loan_product_id", "loan_application_id", "borrower_id",
    "application_id", "contribution_type_id", "schedule_id", "payment_id",
    "journal_id", "account_id", "import_batch_id", "created_by", "updated_by",
    "submitted_by", "verified_by", "approved_by", "decided_by", "disbursed_by",
    "posted_by", "assigned_by", "source_id", "reversal_of", "old_values", "new_values"
}

def safe_frame(rows, preferred=None, rename=None):
    frame = pd.DataFrame(rows or [])
    if frame.empty:
        return frame
    columns = ([c for c in preferred if c in frame.columns] if preferred else
               [c for c in frame.columns if c not in INTERNAL_COLUMNS and not c.endswith("_id")])
    return frame.loc[:, columns].rename(columns=rename or {})

def money(value):
    return f"KES {float(value or 0):,.2f}"

def data(table, filters=None, order=None):
    try:
        return get(table, filters or {}, order)
    except Exception as exc:
        st.error(str(exc))
        return []

for key, default in {"user": None, "profile": None, "view": "member"}.items():
    st.session_state.setdefault(key, default)

if not st.session_state.user:
    st.title("Chama Yetu")
    st.caption("Members | Investments | Accounting")
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in", use_container_width=True)
    if submitted:
        try:
            user, profile = login(email.strip(), password)
            st.session_state.user, st.session_state.profile = user, profile
            st.session_state.view = "admin" if profile.get("role") == "admin" else "member"
            st.rerun()
        except Exception as exc:
            st.error(str(exc))
    st.stop()

profile = st.session_state.profile
GROUP_ID, MEMBER_ID = profile.get("group_id"), profile.get("member_id")
IS_ADMIN = profile.get("role") == "admin"
ADMIN_PAGES = ["Dashboard", "Members", "Historical Payments", "Roles", "Loans", "Investments", "Monthly Returns", "Accounting", "Reports", "Settings"]
MEMBER_PAGES = ["My Dashboard", "My Contributions", "My Loans", "My Investments", "My Returns", "My Statement"]

with st.sidebar:
    st.header("Chama Yetu")
    st.write(profile.get("full_name", "User"))
    if IS_ADMIN:
        st.session_state.view = st.segmented_control("View as", ["admin", "member"], default=st.session_state.view)
    page = st.radio("Navigation", ADMIN_PAGES if st.session_state.view == "admin" else MEMBER_PAGES)
    if st.button("Sign out"):
        logout(); st.session_state.clear(); st.rerun()

def dashboard():
    st.title("Administrator Dashboard")
    members_rows = data("members", {"group_id": GROUP_ID})
    payments = data("contribution_payments", {"group_id": GROUP_ID})
    loans_rows = data("loans", {"group_id": GROUP_ID})
    investment_rows = data("admin_bi_investments", {"group_id": GROUP_ID})
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Members", len(members_rows))
    c2.metric("Verified Contributions", money(sum(float(r.get("amount", 0)) for r in payments if r.get("verification_status") == "verified")))
    c3.metric("Active Loan Principal", money(sum(float(r.get("principal_amount", 0)) for r in loans_rows)))
    c4.metric("Investment Fair Value", money(sum(float(r.get("fair_value", 0)) for r in investment_rows)))
    monthly = data("admin_bi_monthly_contributions", {"group_id": GROUP_ID}, "reporting_month")
    if monthly:
        chart = safe_frame(monthly, ["reporting_month", "verified_amount"], {"reporting_month": "Month", "verified_amount": "Verified Amount"})
        st.plotly_chart(px.bar(chart, x="Month", y="Verified Amount", title="Verified Contributions by Month"), use_container_width=True)

def members():
    st.title("Members")
    with st.form("member_form", clear_on_submit=True):
        left, right = st.columns(2)
        full_name, code = left.text_input("Full Name"), right.text_input("Member Code")
        email, phone = left.text_input("Email"), right.text_input("Phone")
        if st.form_submit_button("Create member"):
            if not full_name.strip() or not code.strip():
                st.error("Full Name and Member Code are required.")
            else:
                add("members", {"group_id": GROUP_ID, "full_name": full_name.strip(), "membership_number": code.strip().upper(), "email": email.strip().lower() or None, "phone": phone.strip() or None, "status": "active"})
                st.success("Member created"); st.rerun()
    display = safe_frame(data("members", {"group_id": GROUP_ID}, "membership_number"),
        ["membership_number", "full_name", "email", "phone", "status", "date_joined"],
        {"membership_number": "Member Code", "full_name": "Full Name", "email": "Email", "phone": "Phone", "status": "Status", "date_joined": "Date Joined"})
    st.dataframe(display, use_container_width=True, hide_index=True)

def historical_payments():
    st.title("Historical Payments")
    display = safe_frame(data("contribution_payments", {"group_id": GROUP_ID, "is_historical": True}, "payment_date"),
        ["payment_date", "payment_reference", "payment_method", "amount", "verification_status", "source_document", "notes"],
        {"payment_date": "Payment Date", "payment_reference": "Receipt Reference", "payment_method": "Payment Method", "amount": "Amount (KES)", "verification_status": "Status", "source_document": "Source Document", "notes": "Source Period"})
    st.dataframe(display, use_container_width=True, hide_index=True)

def roles():
    st.title("Roles")
    display = safe_frame(data("app_roles", {"group_id": GROUP_ID}, "name"), ["code", "name", "description", "active"], {"code": "Role Code", "name": "Role Name", "description": "Description", "active": "Active"})
    st.dataframe(display, use_container_width=True, hide_index=True)

def loans():
    st.title("Loans")
    display = safe_frame(data("loans", {"group_id": GROUP_ID}), ["principal_amount", "annual_interest_rate", "interest_method", "term_months", "disbursement_date", "total_amount_repayable", "status"])
    st.dataframe(display, use_container_width=True, hide_index=True)

def investments():
    st.title("Investments")
    with st.form("investment_form", clear_on_submit=True):
        left, centre, right = st.columns(3)
        name = left.text_input("Investment Name")
        investment_class = centre.selectbox("Investment Class", ["money_market_fund", "treasury_bill", "treasury_bond", "listed_equity", "reit", "venture_capital", "private_equity", "investment_property"])
        issuer = right.text_input("Issuer / Fund Manager")
        cost = left.number_input("Acquisition Cost", min_value=0.0)
        fair_value = centre.number_input("Current Fair Value", min_value=0.0)
        if st.form_submit_button("Add investment"):
            add("investments", {"group_id": GROUP_ID, "name": name.strip(), "investment_class": investment_class, "issuer": issuer.strip() or None, "acquisition_cost": cost, "carrying_value": fair_value or cost, "fair_value": fair_value or cost, "status": "active"})
            st.success("Investment added"); st.rerun()
    display = safe_frame(data("investments", {"group_id": GROUP_ID}, "investment_number"),
        ["investment_number", "name", "investment_class", "issuer", "currency_code", "acquisition_date", "acquisition_cost", "carrying_value", "fair_value", "status"],
        {"investment_number": "Investment No.", "name": "Investment", "investment_class": "Class", "issuer": "Issuer / Manager", "currency_code": "Currency", "acquisition_date": "Acquisition Date", "acquisition_cost": "Cost", "carrying_value": "Carrying Value", "fair_value": "Fair Value", "status": "Status"})
    st.dataframe(display, use_container_width=True, hide_index=True)

def monthly_returns():
    st.title("Monthly Returns")
    display = safe_frame(data("investment_monthly_returns", {"group_id": GROUP_ID}, "reporting_month"), ["reporting_month", "gross_return", "direct_expenses", "shared_expenses", "tax_amount", "other_deductions", "net_return", "distributable_return", "status"])
    st.dataframe(display, use_container_width=True, hide_index=True)

def accounting():
    st.title("Accounting")
    display = safe_frame(data("journal_headers", {"group_id": GROUP_ID}, "journal_date"), ["journal_no", "journal_date", "description", "status", "posted_at"])
    st.dataframe(display, use_container_width=True, hide_index=True)

def reports():
    st.title("Reports")
    report = st.selectbox("Report", ["Members", "Contributions", "Loans", "Investments", "Monthly Returns"])
    mapping = {
        "Members": ("members", ["membership_number", "full_name", "email", "phone", "status", "date_joined"]),
        "Contributions": ("contribution_payments", ["payment_date", "payment_reference", "payment_method", "amount", "verification_status"]),
        "Loans": ("loans", ["principal_amount", "annual_interest_rate", "term_months", "total_amount_repayable", "status"]),
        "Investments": ("investments", ["investment_number", "name", "investment_class", "issuer", "acquisition_cost", "carrying_value", "fair_value", "status"]),
        "Monthly Returns": ("investment_monthly_returns", ["reporting_month", "gross_return", "direct_expenses", "shared_expenses", "tax_amount", "net_return", "status"]),
    }
    table, columns = mapping[report]
    display = safe_frame(data(table, {"group_id": GROUP_ID}), columns)
    st.dataframe(display, use_container_width=True, hide_index=True)
    st.download_button("Download CSV", display.to_csv(index=False).encode(), f"{report.lower().replace(' ', '_')}.csv", "text/csv")

def settings():
    if not IS_ADMIN:
        st.error("Settings are available only to the administrator."); return
    st.title("Administrator Settings")
    rows = data("group_settings", {"group_id": GROUP_ID}); current = rows[0] if rows else {}
    with st.form("settings_form"):
        max_loan = st.number_input("Absolute Maximum Loan", min_value=0.0, value=float(current.get("max_loan_amount") or 0))
        max_multiple = st.number_input("Maximum Multiple of Member Balance", min_value=0.0, value=float(current.get("max_loan_multiple") or 3))
        interest_rate = st.number_input("Default Interest Rate (%)", min_value=0.0, value=float(current.get("interest_rate") or 12))
        max_term = st.number_input("Maximum Term (Months)", min_value=1, value=int(current.get("max_term_months") or 24))
        checker = st.checkbox("Require Checker", value=bool(current.get("require_checker", True)))
        approver = st.checkbox("Require Approver", value=bool(current.get("require_approver", True)))
        if st.form_submit_button("Save settings"):
            upsert("group_settings", {"group_id": GROUP_ID, "max_loan_amount": max_loan or None, "max_loan_multiple": max_multiple, "interest_rate": interest_rate, "max_term_months": max_term, "require_checker": checker, "require_approver": approver})
            st.success("Settings saved")

def my_dashboard():
    st.title("My Dashboard")
    rows = data("member_bi_summary", {"group_id": GROUP_ID, "member_id": MEMBER_ID}); summary = rows[0] if rows else {}
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Contributions", money(summary.get("total_contributions")))
    c2.metric("Investment Balance", money(summary.get("investment_balance")))
    c3.metric("Allocated Returns", money(summary.get("total_returns")))
    c4.metric("Active Loan Principal", money(summary.get("active_loan_principal")))

def member_table(title, table, columns, member_field="member_id"):
    st.title(title)
    st.dataframe(safe_frame(data(table, {"group_id": GROUP_ID, member_field: MEMBER_ID}), columns), use_container_width=True, hide_index=True)

def my_statement():
    st.title("My Statement")
    display = safe_frame(data("member_investment_transactions", {"group_id": GROUP_ID, "member_id": MEMBER_ID}, "transaction_date"), ["transaction_date", "transaction_type", "description", "amount"])
    st.dataframe(display, use_container_width=True, hide_index=True)
    st.download_button("Download Statement", display.to_csv(index=False).encode(), "my_statement.csv", "text/csv")

ROUTES = {
    "Dashboard": dashboard, "Members": members, "Historical Payments": historical_payments,
    "Roles": roles, "Loans": loans, "Investments": investments,
    "Monthly Returns": monthly_returns, "Accounting": accounting,
    "Reports": reports, "Settings": settings, "My Dashboard": my_dashboard,
    "My Contributions": lambda: member_table("My Contributions", "contribution_payments", ["payment_date", "payment_reference", "payment_method", "amount", "verification_status"]),
    "My Loans": lambda: member_table("My Loans", "loans", ["principal_amount", "annual_interest_rate", "interest_method", "term_months", "total_amount_repayable", "status"], "borrower_id"),
    "My Investments": lambda: member_table("My Investments", "member_investment_transactions", ["transaction_date", "transaction_type", "description", "amount"]),
    "My Returns": lambda: member_table("My Returns", "member_return_allocations", ["reporting_month", "applicable_balance", "allocation_pct", "net_return_allocated", "reinvested_amount", "payable_amount"]),
    "My Statement": my_statement,
}
ROUTES[page]()
