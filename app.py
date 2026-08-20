import streamlit as st
import pandas as pd
import plotly.express as px
from services.db import get, add, upsert
from services.auth import login, logout

st.set_page_config(page_title="Chama Yetu", page_icon="CY", layout="wide")

# -----------------------------------------------------------------------------
# Display helpers: never expose database UUIDs/control columns on the frontend.
# -----------------------------------------------------------------------------
INTERNAL_COLUMNS = {
    "id", "group_id", "user_id", "member_id", "role_id", "investment_id",
    "loan_id", "loan_product_id", "loan_application_id", "borrower_id",
    "application_id", "contribution_type_id", "schedule_id", "payment_id",
    "journal_id", "account_id", "import_batch_id", "created_by", "updated_by",
    "submitted_by", "verified_by", "approved_by", "decided_by", "disbursed_by",
    "posted_by", "assigned_by", "source_id", "reversal_of", "old_values",
    "new_values"
}

def safe_frame(rows, preferred=None, rename=None):
    frame = pd.DataFrame(rows or [])
    if frame.empty:
        return frame
    if preferred:
        columns = [column for column in preferred if column in frame.columns]
    else:
        columns = [
            column for column in frame.columns
            if column not in INTERNAL_COLUMNS and not column.endswith("_id")
        ]
    return frame.loc[:, columns].rename(columns=rename or {})

def money(value):
    return f"KES {float(value or 0):,.2f}"

def data(table, filters=None, order=None):
    try:
        return get(table, filters or {}, order)
    except Exception as exc:
        st.error(str(exc))
        return []

# -----------------------------------------------------------------------------
# Session and authentication
# -----------------------------------------------------------------------------
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
            st.session_state.user = user
            st.session_state.profile = profile
            st.session_state.view = "admin" if profile.get("role") == "admin" else "member"
            st.rerun()
        except Exception as exc:
            st.error(str(exc))
    st.stop()

profile = st.session_state.profile
GROUP_ID = profile.get("group_id")
MEMBER_ID = profile.get("member_id")
IS_ADMIN = profile.get("role") == "admin"

ADMIN_PAGES = [
    "Dashboard", "Members", "Historical Payments", "Roles", "Loans",
    "Investments", "Monthly Returns", "Accounting", "Reports", "Settings"
]
MEMBER_PAGES = [
    "My Dashboard", "My Contributions", "My Loans", "My Investments",
    "My Returns", "My Statement"
]

with st.sidebar:
    st.header("Chama Yetu")
    st.write(profile.get("full_name", "User"))
    if IS_ADMIN:
        st.session_state.view = st.segmented_control(
            "View as", ["admin", "member"], default=st.session_state.view
        )
    page = st.radio(
        "Navigation",
        ADMIN_PAGES if st.session_state.view == "admin" else MEMBER_PAGES,
    )
    if st.button("Sign out"):
        logout()
        st.session_state.clear()
        st.rerun()

# -----------------------------------------------------------------------------
# Administrator pages
# -----------------------------------------------------------------------------
def dashboard():
    st.title("Administrator Dashboard")
    members_rows = data("members", {"group_id": GROUP_ID})
    payment_rows = data("contribution_payments", {"group_id": GROUP_ID})
    loan_rows = data("loans", {"group_id": GROUP_ID})
    investment_rows = data("admin_bi_investments", {"group_id": GROUP_ID})

    verified = sum(
        float(row.get("amount", 0)) for row in payment_rows
        if row.get("verification_status") == "verified"
    )
    active_principal = sum(float(row.get("principal_amount", 0)) for row in loan_rows)
    fair_value = sum(float(row.get("fair_value", 0)) for row in investment_rows)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Members", len(members_rows))
    c2.metric("Verified Contributions", money(verified))
    c3.metric("Active Loan Principal", money(active_principal))
    c4.metric("Investment Fair Value", money(fair_value))

    monthly = data("admin_bi_monthly_contributions", {"group_id": GROUP_ID}, "reporting_month")
    if monthly:
        chart_data = safe_frame(
            monthly,
            preferred=["reporting_month", "verified_amount", "pending_count", "contributing_members"],
            rename={"reporting_month": "Month", "verified_amount": "Verified Amount"},
        )
        st.plotly_chart(
            px.bar(chart_data, x="Month", y="Verified Amount", title="Verified Contributions by Month"),
            use_container_width=True,
        )

    if investment_rows:
        chart_data = safe_frame(
            investment_rows,
            preferred=["name", "investment_class", "net_return"],
            rename={"name": "Investment", "investment_class": "Class", "net_return": "Net Return"},
        )
        st.plotly_chart(
            px.bar(chart_data, x="Investment", y="Net Return", color="Class", title="Net Returns by Investment"),
            use_container_width=True,
        )


def members():
    st.title("Members")
    with st.form("member_form", clear_on_submit=True):
        left, right = st.columns(2)
        full_name = left.text_input("Full Name")
        membership_number = right.text_input("Member Code")
        email = left.text_input("Email")
        phone = right.text_input("Phone")
        if st.form_submit_button("Create member"):
            if not full_name.strip() or not membership_number.strip():
                st.error("Full Name and Member Code are required.")
            else:
                try:
                    add("members", {
                        "group_id": GROUP_ID,
                        "full_name": full_name.strip(),
                        "membership_number": membership_number.strip().upper(),
                        "email": email.strip().lower() or None,
                        "phone": phone.strip() or None,
                        "status": "active",
                    })
                    st.success("Member created")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

    rows = data("members", {"group_id": GROUP_ID}, "membership_number")
    display = safe_frame(
        rows,
        preferred=["membership_number", "full_name", "email", "phone", "status", "date_joined"],
        rename={
            "membership_number": "Member Code", "full_name": "Full Name",
            "email": "Email", "phone": "Phone", "status": "Status",
            "date_joined": "Date Joined",
        },
    )
    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Member Code": st.column_config.TextColumn(width="small"),
            "Full Name": st.column_config.TextColumn(width="medium"),
            "Email": st.column_config.TextColumn(width="medium"),
            "Phone": st.column_config.TextColumn(width="small"),
            "Status": st.column_config.TextColumn(width="small"),
            "Date Joined": st.column_config.DateColumn(format="DD MMM YYYY"),
        },
    )


def historical_payments():
    st.title("Historical Payments")
    st.caption("Historical records are displayed without database identifiers.")
    rows = data("contribution_payments", {"group_id": GROUP_ID, "is_historical": True}, "payment_date")
    display = safe_frame(
        rows,
        preferred=["payment_date", "payment_reference", "payment_method", "amount", "verification_status", "source_document", "notes"],
        rename={
            "payment_date": "Payment Date", "payment_reference": "Receipt Reference",
            "payment_method": "Payment Method", "amount": "Amount (KES)",
            "verification_status": "Status", "source_document": "Source Document",
            "notes": "Source Period",
        },
    )
    st.dataframe(display, use_container_width=True, hide_index=True)


def roles():
    st.title("Roles")
    role_rows = data("app_roles", {"group_id": GROUP_ID}, "name")
    role_display = safe_frame(
        role_rows,
        preferred=["code", "name", "description", "active"],
        rename={"code": "Role Code", "name": "Role Name", "description": "Description", "active": "Active"},
    )
    st.dataframe(role_display, use_container_width=True, hide_index=True)


def loans():
    st.title("Loans")
    rows = data("loans", {"group_id": GROUP_ID})
    display = safe_frame(
        rows,
        preferred=["principal_amount", "annual_interest_rate", "interest_method", "term_months", "disbursement_date", "repayment_start_date", "total_amount_repayable", "status"],
        rename={
            "principal_amount": "Principal (KES)", "annual_interest_rate": "Interest Rate (%)",
            "interest_method": "Interest Method", "term_months": "Term (Months)",
            "disbursement_date": "Disbursement Date", "repayment_start_date": "Repayment Start",
            "total_amount_repayable": "Total Repayable (KES)", "status": "Status",
        },
    )
    st.dataframe(display, use_container_width=True, hide_index=True)


def investments():
    st.title("Investments")
    with st.form("investment_form", clear_on_submit=True):
        left, centre, right = st.columns(3)
        name = left.text_input("Investment Name")
        investment_class = centre.selectbox("Investment Class", [
            "money_market_fund", "treasury_bill", "treasury_bond", "listed_equity",
            "reit", "venture_capital", "private_equity", "investment_property"
        ])
        issuer = right.text_input("Issuer / Fund Manager")
        cost = left.number_input("Acquisition Cost", min_value=0.0)
        fair_value = centre.number_input("Current Fair Value", min_value=0.0)
        if st.form_submit_button("Add investment"):
            try:
                add("investments", {
                    "group_id": GROUP_ID, "name": name.strip(),
                    "investment_class": investment_class, "issuer": issuer.strip() or None,
                    "acquisition_cost": cost, "carrying_value": fair_value or cost,
                    "fair_value": fair_value or cost, "status": "active",
                })
                st.success("Investment added")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    rows = data("investments", {"group_id": GROUP_ID})
    display = safe_frame(
        rows,
        preferred=["name", "investment_class", "issuer", "currency_code", "acquisition_date", "acquisition_cost", "carrying_value", "fair_value", "status"],
        rename={
            "name": "Investment", "investment_class": "Class", "issuer": "Issuer / Manager",
            "currency_code": "Currency", "acquisition_date": "Acquisition Date",
            "acquisition_cost": "Cost", "carrying_value": "Carrying Value",
            "fair_value": "Fair Value", "status": "Status",
        },
    )
    st.dataframe(display, use_container_width=True, hide_index=True)


def monthly_returns():
    st.title("Monthly Returns")
    rows = data("investment_monthly_returns", {"group_id": GROUP_ID}, "reporting_month")
    display = safe_frame(
        rows,
        preferred=["reporting_month", "gross_return", "direct_expenses", "shared_expenses", "tax_amount", "other_deductions", "net_return", "distributable_return", "status"],
        rename={
            "reporting_month": "Reporting Month", "gross_return": "Gross Return",
            "direct_expenses": "Direct Expenses", "shared_expenses": "Shared Expenses",
            "tax_amount": "Tax", "other_deductions": "Other Deductions",
            "net_return": "Net Return", "distributable_return": "Distributable Return",
            "status": "Status",
        },
    )
    st.dataframe(display, use_container_width=True, hide_index=True)


def accounting():
    st.title("Accounting")
    rows = data("journal_headers", {"group_id": GROUP_ID}, "journal_date")
    display = safe_frame(
        rows,
        preferred=["journal_no", "journal_date", "description", "status", "posted_at"],
        rename={
            "journal_no": "Journal No.", "journal_date": "Journal Date",
            "description": "Description", "status": "Status", "posted_at": "Posted At",
        },
    )
    st.dataframe(display, use_container_width=True, hide_index=True)


def reports():
    st.title("Reports")
    report = st.selectbox("Report", ["Members", "Contributions", "Loans", "Investments", "Monthly Returns"])
    mapping = {
        "Members": ("members", ["membership_number", "full_name", "email", "phone", "status", "date_joined"]),
        "Contributions": ("contribution_payments", ["payment_date", "payment_reference", "payment_method", "amount", "verification_status"]),
        "Loans": ("loans", ["principal_amount", "annual_interest_rate", "term_months", "total_amount_repayable", "status"]),
        "Investments": ("investments", ["name", "investment_class", "issuer", "acquisition_cost", "carrying_value", "fair_value", "status"]),
        "Monthly Returns": ("investment_monthly_returns", ["reporting_month", "gross_return", "direct_expenses", "shared_expenses", "tax_amount", "net_return", "status"]),
    }
    table, columns = mapping[report]
    report_rows = data(table, {"group_id": GROUP_ID})
    display = safe_frame(report_rows, preferred=columns)
    st.dataframe(display, use_container_width=True, hide_index=True)
    st.download_button(
        "Download CSV", display.to_csv(index=False).encode("utf-8"),
        file_name=f"{report.lower().replace(' ', '_')}.csv", mime="text/csv"
    )


def settings():
    if not IS_ADMIN:
        st.error("Settings are available only to the administrator.")
        return
    st.title("Administrator Settings")
    rows = data("group_settings", {"group_id": GROUP_ID})
    settings_row = rows[0] if rows else {"group_id": GROUP_ID}
    with st.form("settings_form"):
        max_loan = st.number_input("Absolute Maximum Loan", min_value=0.0, value=float(settings_row.get("max_loan_amount") or 0))
        max_multiple = st.number_input("Maximum Multiple of Member Balance", min_value=0.0, value=float(settings_row.get("max_loan_multiple") or 3))
        interest_rate = st.number_input("Default Interest Rate (%)", min_value=0.0, value=float(settings_row.get("interest_rate") or 12))
        max_term = st.number_input("Maximum Term (Months)", min_value=1, value=int(settings_row.get("max_term_months") or 24))
        require_checker = st.checkbox("Require Checker", value=bool(settings_row.get("require_checker", True)))
        require_approver = st.checkbox("Require Approver", value=bool(settings_row.get("require_approver", True)))
        if st.form_submit_button("Save settings"):
            upsert("group_settings", {
                "group_id": GROUP_ID,
                "max_loan_amount": max_loan or None,
                "max_loan_multiple": max_multiple,
                "interest_rate": interest_rate,
                "max_term_months": max_term,
                "require_checker": require_checker,
                "require_approver": require_approver,
            })
            st.success("Settings saved")

# -----------------------------------------------------------------------------
# Member pages
# -----------------------------------------------------------------------------
def my_dashboard():
    st.title("My Dashboard")
    rows = data("member_bi_summary", {"group_id": GROUP_ID, "member_id": MEMBER_ID})
    summary = rows[0] if rows else {}
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Contributions", money(summary.get("total_contributions")))
    c2.metric("Investment Balance", money(summary.get("investment_balance")))
    c3.metric("Allocated Returns", money(summary.get("total_returns")))
    c4.metric("Active Loan Principal", money(summary.get("active_loan_principal")))


def member_table(title, table, columns, rename=None, member_field="member_id"):
    st.title(title)
    rows = data(table, {"group_id": GROUP_ID, member_field: MEMBER_ID})
    display = safe_frame(rows, preferred=columns, rename=rename)
    st.dataframe(display, use_container_width=True, hide_index=True)


def my_statement():
    st.title("My Statement")
    rows = data("member_investment_transactions", {"group_id": GROUP_ID, "member_id": MEMBER_ID}, "transaction_date")
    display = safe_frame(
        rows,
        preferred=["transaction_date", "transaction_type", "description", "amount"],
        rename={"transaction_date": "Date", "transaction_type": "Transaction", "description": "Description", "amount": "Amount (KES)"},
    )
    st.dataframe(display, use_container_width=True, hide_index=True)
    st.download_button("Download Statement", display.to_csv(index=False).encode("utf-8"), "my_statement.csv", "text/csv")

ROUTES = {
    "Dashboard": dashboard,
    "Members": members,
    "Historical Payments": historical_payments,
    "Roles": roles,
    "Loans": loans,
    "Investments": investments,
    "Monthly Returns": monthly_returns,
    "Accounting": accounting,
    "Reports": reports,
    "Settings": settings,
    "My Dashboard": my_dashboard,
    "My Contributions": lambda: member_table(
        "My Contributions", "contribution_payments",
        ["payment_date", "payment_reference", "payment_method", "amount", "verification_status"],
        {"payment_date": "Payment Date", "payment_reference": "Reference", "payment_method": "Method", "amount": "Amount (KES)", "verification_status": "Status"},
    ),
    "My Loans": lambda: member_table(
        "My Loans", "loans",
        ["principal_amount", "annual_interest_rate", "interest_method", "term_months", "total_amount_repayable", "status"],
        {"principal_amount": "Principal", "annual_interest_rate": "Interest Rate", "interest_method": "Method", "term_months": "Term", "total_amount_repayable": "Total Repayable", "status": "Status"},
        member_field="borrower_id",
    ),
    "My Investments": lambda: member_table(
        "My Investments", "member_investment_transactions",
        ["transaction_date", "transaction_type", "description", "amount"],
        {"transaction_date": "Date", "transaction_type": "Transaction", "description": "Description", "amount": "Amount (KES)"},
    ),
    "My Returns": lambda: member_table(
        "My Returns", "member_return_allocations",
        ["reporting_month", "applicable_balance", "allocation_pct", "net_return_allocated", "reinvested_amount", "payable_amount"],
        {"reporting_month": "Month", "applicable_balance": "Applicable Balance", "allocation_pct": "Allocation %", "net_return_allocated": "Net Return", "reinvested_amount": "Reinvested", "payable_amount": "Payable"},
    ),
    "My Statement": my_statement,
}

ROUTES[page]()
