import os
from datetime import date
from decimal import Decimal
import pandas as pd
import streamlit as st
from supabase import create_client, Client

st.set_page_config(page_title="Chama Yetu", page_icon="💼", layout="wide")


def secret(name, default=None):
    try:
        return st.secrets[name]
    except Exception:
        return os.getenv(name, default)


@st.cache_resource
def client() -> Client:
    url = secret("SUPABASE_URL")
    key = secret("SUPABASE_ANON_KEY")
    if not url or not key:
        st.error("SUPABASE_URL and SUPABASE_ANON_KEY are required in Streamlit secrets.")
        st.stop()
    return create_client(url, key)


sb = client()


def rows(table, filters=None, order=None):
    q = sb.table(table).select("*")
    for k, v in (filters or {}).items():
        q = q.eq(k, v)
    if order:
        q = q.order(order)
    return q.execute().data or []


def add(table, payload):
    data = sb.table(table).insert(payload).execute().data or []
    return data[0] if data else None


def update(table, row_id, payload):
    data = sb.table(table).update(payload).eq("id", row_id).execute().data or []
    return data[0] if data else None


def money(value):
    return f"KES {Decimal(str(value or 0)):,.2f}"


def login():
    st.title("Chama Yetu")
    with st.form("login"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Sign in", type="primary")
    if submit:
        try:
            result = sb.auth.sign_in_with_password({"email": email.strip(), "password": password})
            st.session_state.user = result.user
            st.rerun()
        except Exception as exc:
            st.error(f"Sign-in failed: {exc}")


def session_user():
    if "user" in st.session_state:
        return st.session_state.user
    try:
        session = sb.auth.get_session()
        if session and session.user:
            st.session_state.user = session.user
            return session.user
    except Exception:
        pass
    return None


def profile(user_id):
    data = sb.table("profiles").select("*").eq("id", user_id).limit(1).execute().data or []
    return data[0] if data else None


def group_id_for_user(user_id, p):
    if p and p.get("group_id"):
        return p["group_id"]
    member = sb.table("members").select("group_id").eq("user_id", user_id).limit(1).execute().data or []
    if member:
        return member[0]["group_id"]
    groups = sb.table("groups").select("id").limit(1).execute().data or []
    return groups[0]["id"] if groups else None


def investment_number(group_id):
    try:
        value = sb.rpc("next_investment_number", {"p_group_id": group_id}).execute().data
        if value:
            return value
    except Exception:
        pass
    existing = sb.table("investments").select("investment_number").eq("group_id", group_id).execute().data or []
    year = date.today().year
    nums = []
    for item in existing:
        number = item.get("investment_number") or ""
        try:
            if number.startswith(f"INV-{year}-"):
                nums.append(int(number.rsplit("-", 1)[1]))
        except Exception:
            pass
    return f"INV-{year}-{max(nums, default=0)+1:04d}"


def create_investment(group_id, user_id):
    st.subheader("Create Investment")
    inv_no = investment_number(group_id)
    with st.form("create_investment", clear_on_submit=False):
        a, b, c = st.columns(3)
        with a:
            st.text_input("Investment Number", value=inv_no, disabled=True)
            name = st.text_input("Investment Name *", placeholder="Mansa-X Special Fund - KES")
            investment_class = st.selectbox("Investment Class *", [
                "money_market_fund", "fixed_deposit", "treasury_bill", "treasury_bond",
                "corporate_bond", "listed_equity", "unit_trust", "property",
                "private_equity", "sacco_deposit", "bank_call_deposit", "other"
            ])
            product = st.text_input("Investment Product")
        with b:
            issuer = st.text_input("Issuer / Fund Manager", placeholder="Standard Investment Bank")
            customer_no = st.text_input("Provider Customer Number", placeholder="1067555")
            account_no = st.text_input("Provider Account Number")
            certificate_no = st.text_input("Certificate / Contract Number")
        with c:
            currency = st.selectbox("Currency", ["KES", "USD", "GBP", "EUR"])
            status = st.selectbox("Status", ["draft", "awaiting_funding", "active", "matured", "redeemed", "sold", "closed"])
            opening_date = st.date_input("Account Opening Date", value=None)
            investment_date = st.date_input("Date of Investment", value=None)

        st.markdown("#### Investment and funding details")
        d, e, f = st.columns(3)
        with d:
            value_date = st.date_input("Value Date", value=None)
            settlement_date = st.date_input("Settlement Date", value=None)
            maturity_date = st.date_input("Maturity Date", value=None)
        with e:
            rate = st.number_input("Interest / Coupon Rate (%)", min_value=0.0, value=0.0, step=0.01)
            frequency = st.selectbox("Income Frequency", ["none", "daily", "monthly", "quarterly", "semi_annual", "annual", "at_maturity"])
            funding_method = st.selectbox("Funding Method", ["bank_transfer", "rtgs", "mpesa", "pesalink", "cheque", "other"])
        with f:
            funding_reference = st.text_input("Funding Reference")
            bank_name = st.text_input("Bank")
            beneficiary = st.text_input("Beneficiary Account Number")
        description = st.text_area("Description / Notes")
        submit = st.form_submit_button("Create Investment", type="primary")

    if submit:
        if not name.strip():
            st.error("Investment Name is required.")
            return
        payload = {
            "group_id": group_id, "investment_number": inv_no, "investment_name": name.strip(),
            "investment_class": investment_class, "investment_product": product.strip() or None,
            "issuer_fund_manager": issuer.strip() or None, "provider_customer_number": customer_no.strip() or None,
            "provider_account_number": account_no.strip() or None, "certificate_contract_number": certificate_no.strip() or None,
            "currency_code": currency, "status": status, "account_opening_date": opening_date.isoformat() if opening_date else None,
            "investment_date": investment_date.isoformat() if investment_date else None,
            "value_date": value_date.isoformat() if value_date else None, "settlement_date": settlement_date.isoformat() if settlement_date else None,
            "maturity_date": maturity_date.isoformat() if maturity_date else None, "interest_coupon_rate": rate,
            "income_frequency": frequency, "funding_method": funding_method,
            "funding_reference": funding_reference.strip() or None, "bank_name": bank_name.strip() or None,
            "beneficiary_account_number": beneficiary.strip() or None, "description": description.strip() or None,
            "created_by": user_id
        }
        try:
            record = add("investments", payload)
            if not record:
                raise RuntimeError("The database did not return the new investment")
            st.session_state.selected_investment_id = record["id"]
            st.success(f"Investment {inv_no} created.")
            st.rerun()
        except Exception as exc:
            st.error(f"Investment could not be created: {exc}")


def register(group_id):
    try:
        records = sb.table("vw_investment_register").select("*").eq("group_id", group_id).execute().data or []
    except Exception:
        records = rows("investments", {"group_id": group_id})
    st.subheader("Investment Register")
    if not records:
        st.info("No investments have been created.")
        return
    df = pd.DataFrame(records)
    labels = {}
    for record in records:
        label = f"{record.get('investment_number', '')} | {record.get('investment_name', '')}"
        labels[label] = record.get("investment_id") or record.get("id")
    selected = st.selectbox("Open an investment", list(labels.keys()))
    if st.button("View selected investment", type="primary"):
        st.session_state.selected_investment_id = labels[selected]
        st.rerun()
    fields = [c for c in ["investment_number", "investment_name", "investment_class", "issuer_fund_manager", "investment_date", "current_cost_balance", "current_fair_value", "realised_gain_loss", "status"] if c in df.columns]
    st.dataframe(df[fields], use_container_width=True, hide_index=True)


def transaction_form(group_id, investment, user_id):
    st.markdown("#### Investment transaction")
    tx_types = ["opening_balance", "purchase", "additional_purchase", "sale", "redemption", "maturity", "income_accrual", "income_receipt", "valuation", "impairment", "charge"]
    with st.form("investment_transaction"):
        a, b, c = st.columns(3)
        with a:
            tx_type = st.selectbox("Transaction Type", tx_types)
            tx_date = st.date_input("Transaction Date", value=date.today())
            settlement = st.date_input("Settlement Date", value=None)
        with b:
            quantity = st.number_input("Quantity / Units", min_value=0.0, value=0.0, step=0.0001, format="%.4f")
            unit_price = st.number_input("Unit Price", min_value=0.0, value=0.0, step=0.01)
            gross = st.number_input("Gross Amount", min_value=0.0, value=0.0, step=100.0)
        with c:
            costs = st.number_input("Transaction Costs", min_value=0.0, value=0.0, step=1.0)
            tax = st.number_input("Withholding Tax", min_value=0.0, value=0.0, step=1.0)
            reference = st.text_input("External / Payment Reference")
        description = st.text_area("Transaction description")
        post_now = st.checkbox("Post transaction to the General Ledger", value=False)
        submit = st.form_submit_button("Save Transaction", type="primary")
    if submit:
        net = gross + costs if tx_type in ("opening_balance", "purchase", "additional_purchase") else max(gross - costs - tax, 0)
        payload = {
            "group_id": group_id, "investment_id": investment["id"],
            "transaction_number": f"ITX-{date.today():%Y%m%d}-{pd.Timestamp.now().strftime('%H%M%S%f')}",
            "transaction_type": tx_type, "transaction_date": tx_date.isoformat(),
            "settlement_date": settlement.isoformat() if settlement else None,
            "quantity": quantity or None, "unit_price": unit_price or None,
            "gross_amount": gross, "transaction_cost": costs, "withholding_tax": tax,
            "net_amount": net, "payment_reference": reference.strip() or None,
            "description": description.strip() or None, "status": "approved" if not post_now else "posted",
            "created_by": user_id, "posted_by": user_id if post_now else None,
            "posted_at": pd.Timestamp.now(tz="UTC").isoformat() if post_now else None
        }
        try:
            if post_now:
                response = sb.rpc("post_investment_transaction", {"p_transaction": payload}).execute().data
                st.success(f"Transaction posted. Journal: {response}")
            else:
                add("investment_transactions", payload)
                st.success("Investment transaction saved for approval/posting.")
            st.rerun()
        except Exception as exc:
            st.error(f"Transaction could not be saved: {exc}")


def valuation_form(group_id, investment, user_id):
    st.markdown("#### Value Investment")
    with st.form("valuation"):
        a, b, c = st.columns(3)
        with a:
            valuation_date = st.date_input("Valuation Date", value=date.today())
            quantity = st.number_input("Units Held", min_value=0.0, value=0.0, step=0.0001, format="%.4f")
        with b:
            market_price = st.number_input("Market / Unit Price", min_value=0.0, value=0.0, step=0.01)
            fair_value = st.number_input("Fair Value", min_value=0.0, value=0.0, step=100.0)
        with c:
            source = st.text_input("Valuation Source")
            reference = st.text_input("Valuation Reference")
        notes = st.text_area("Valuation Notes")
        submit = st.form_submit_button("Save Valuation", type="primary")
    if submit:
        try:
            add("investment_valuations", {
                "group_id": group_id, "investment_id": investment["id"], "valuation_date": valuation_date.isoformat(),
                "quantity": quantity or None, "market_unit_price": market_price or None, "fair_value": fair_value,
                "valuation_source": source.strip() or None, "external_reference": reference.strip() or None,
                "notes": notes.strip() or None, "status": "draft", "created_by": user_id
            })
            st.success("Valuation saved as draft.")
            st.rerun()
        except Exception as exc:
            st.error(f"Valuation could not be saved: {exc}")


def investment_detail(group_id, investment_id, user_id):
    result = sb.table("investments").select("*").eq("id", investment_id).eq("group_id", group_id).limit(1).execute().data or []
    if not result:
        st.error("Investment not found or access is not permitted.")
        st.session_state.pop("selected_investment_id", None)
        return
    investment = result[0]
    if st.button("← Back to Investment Register"):
        st.session_state.pop("selected_investment_id", None)
        st.rerun()
    st.title(investment.get("investment_name") or "Investment")
    st.caption(f"{investment.get('investment_number', '')} | {investment.get('issuer_fund_manager') or 'Issuer not recorded'} | {investment.get('status', '')}")

    register_rows = sb.table("vw_investment_register").select("*").eq("investment_id", investment_id).limit(1).execute().data or []
    summary = register_rows[0] if register_rows else {}
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Current Cost", money(summary.get("current_cost_balance")))
    m2.metric("Current Fair Value", money(summary.get("current_fair_value")))
    m3.metric("Unrealised Gain / Loss", money((summary.get("current_fair_value") or 0) - (summary.get("current_cost_balance") or 0)))
    m4.metric("Realised Gain / Loss", money(summary.get("realised_gain_loss")))

    overview, transactions, valuation, ledger = st.tabs(["Overview", "Transactions", "Valuations", "General Ledger"])
    with overview:
        fields = {
            "Investment Number": investment.get("investment_number"), "Investment Class": investment.get("investment_class"),
            "Investment Product": investment.get("investment_product"), "Provider Customer Number": investment.get("provider_customer_number"),
            "Provider Account Number": investment.get("provider_account_number"), "Certificate / Contract Number": investment.get("certificate_contract_number"),
            "Account Opening Date": investment.get("account_opening_date"), "Date of Investment": investment.get("investment_date"),
            "Value Date": investment.get("value_date"), "Settlement Date": investment.get("settlement_date"),
            "Maturity Date": investment.get("maturity_date"), "Currency": investment.get("currency_code"),
            "Interest / Coupon Rate": investment.get("interest_coupon_rate"), "Income Frequency": investment.get("income_frequency"),
            "Funding Method": investment.get("funding_method"), "Funding Reference": investment.get("funding_reference")
        }
        cols = st.columns(2)
        for idx, (label, value) in enumerate(fields.items()):
            cols[idx % 2].write(f"**{label}:** {value if value not in (None, '') else 'Not recorded'}")
    with transactions:
        transaction_form(group_id, investment, user_id)
        tx = rows("investment_transactions", {"investment_id": investment_id}, "transaction_date")
        st.dataframe(pd.DataFrame(tx), use_container_width=True, hide_index=True) if tx else st.info("No transactions recorded.")
    with valuation:
        valuation_form(group_id, investment, user_id)
        vals = rows("investment_valuations", {"investment_id": investment_id}, "valuation_date")
        st.dataframe(pd.DataFrame(vals), use_container_width=True, hide_index=True) if vals else st.info("No valuations recorded.")
    with ledger:
        entries = sb.table("vw_investment_gl_entries").select("*").eq("investment_id", investment_id).execute().data or []
        st.dataframe(pd.DataFrame(entries), use_container_width=True, hide_index=True) if entries else st.info("No posted GL entries for this investment.")


def investments_page(group_id, user_id):
    st.title("Investments")
    try:
        bi = sb.table("vw_investment_bi").select("*").eq("group_id", group_id).limit(1).execute().data or []
        bi = bi[0] if bi else {}
    except Exception:
        bi = {}
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Active Investments", int(bi.get("active_investment_count") or 0))
    c2.metric("Total Cost", money(bi.get("total_cost")))
    c3.metric("Total Fair Value", money(bi.get("total_fair_value")))
    c4.metric("Unrealised Gain / Loss", money(bi.get("unrealised_gain_loss")))
    c5.metric("Realised Gain / Loss", money(bi.get("realised_gain_loss")))
    if st.session_state.get("selected_investment_id"):
        investment_detail(group_id, st.session_state.selected_investment_id, user_id)
        return
    create_tab, register_tab = st.tabs(["Create Investment", "Investment Register"])
    with create_tab:
        create_investment(group_id, user_id)
    with register_tab:
        register(group_id)


def main():
    user = session_user()
    if not user:
        login()
        return
    p = profile(user.id)
    if not p:
        st.error("No Chama Yetu profile is linked to this authenticated account.")
        return
    group_id = group_id_for_user(user.id, p)
    if not group_id:
        st.error("No Chama Yetu group is available for this account.")
        return
    with st.sidebar:
        st.title("Chama Yetu")
        st.write(p.get("full_name") or user.email)
        view = st.radio("View as", ["admin", "member"], horizontal=True, disabled=p.get("role") != "admin")
        page = st.radio("Navigation", ["Dashboard", "Investments"])
        if st.button("Sign out"):
            sb.auth.sign_out()
            st.session_state.clear()
            st.rerun()
    if page == "Investments" and view == "admin":
        investments_page(group_id, user.id)
    elif page == "Investments":
        st.title("Investments")
        st.info("Member investment BI will display approved aggregate information only.")
    else:
        st.title("Dashboard")
        st.info("Use Investments to manage the Investment Register, details, transactions, valuations and GL entries.")


if __name__ == "__main__":
    main()
