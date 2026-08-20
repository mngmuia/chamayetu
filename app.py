import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from services.db import client, rows, insert, rpc
from services.auth import login, logout
from utils.session import init_session, sign_out
from utils.formatting import money
from components.ui import page_title

st.set_page_config(page_title="Chama Yetu", page_icon="💠", layout="wide")
init_session()

def login_page():
    st.title("Chama Yetu")
    st.caption("Members • Investments • Accounting")
    with st.form("login"):
        email=st.text_input("Email")
        password=st.text_input("Password", type="password")
        submitted=st.form_submit_button("Sign in", use_container_width=True)
    if submitted:
        try:
            user, profile=login(email,password)
            st.session_state.user=user
            st.session_state.profile=profile
            st.session_state.group_id=profile.get("group_id")
            st.session_state.member_id=profile.get("member_id")
            st.session_state.active_view="admin" if profile.get("role") in ("admin","platform_admin") else "member"
            st.rerun()
        except Exception as e: st.error(f"Sign-in failed: {e}")

if not st.session_state.user:
    login_page(); st.stop()

P=st.session_state.profile or {}
role=P.get("role","member")
actual_admin=role in ("admin","platform_admin","treasurer","accountant","investment_officer","credit_officer")
with st.sidebar:
    st.header("Chama Yetu")
    st.write(P.get("full_name") or P.get("email") or "User")
    if actual_admin:
        st.session_state.active_view=st.segmented_control("View as",["admin","member"],default=st.session_state.active_view)
    view=st.session_state.active_view
    admin_pages=["Dashboard","Members","Contributions","Payment Verification","Loans","Investments","Monthly Returns","Return Allocation","Accounting","Bank Reconciliation","Investment Reconciliation","Reports","Audit Log","Settings"]
    member_pages=["My Dashboard","My Contributions","Submit Payment","My Loans","My Investments","My Returns","My Statement"]
    page=st.radio("Navigation",admin_pages if view=="admin" else member_pages)
    if st.button("Sign out",use_container_width=True):
        try: logout()
        finally: sign_out()

G=st.session_state.group_id; M=st.session_state.member_id

def df(data): return pd.DataFrame(data) if data else pd.DataFrame()
def safe_rows(*args,**kwargs):
    try:return rows(*args,**kwargs)
    except Exception as e: st.error(str(e)); return []

def admin_dashboard():
    page_title("Administrator Dashboard","Current verified operational and financial position")
    members=safe_rows("members",filters={"group_id":G,"status":"active"})
    payments=safe_rows("contribution_payments",filters={"group_id":G,"verification_status":"verified"})
    loans=safe_rows("loans",filters={"group_id":G})
    investments=safe_rows("investments",filters={"group_id":G,"status":"active"})
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Active members",len(members)); c2.metric("Verified contributions",money(sum(float(x.get('amount',0)) for x in payments)))
    c3.metric("Loan principal",money(sum(float(x.get('principal',0)) for x in loans))); c4.metric("Investment carrying value",money(sum(float(x.get('carrying_value',0)) for x in investments)))
    rets=safe_rows("investment_monthly_returns",filters={"group_id":G},order="reporting_month")
    if rets:
        d=df(rets); d["reporting_month"]=pd.to_datetime(d["reporting_month"]); st.plotly_chart(px.line(d,x="reporting_month",y="net_return",title="Net investment return"),use_container_width=True)

def members_page():
    page_title("Members")
    with st.form("member"):
        a,b=st.columns(2); full=a.text_input("Full name"); no=b.text_input("Membership number")
        email=a.text_input("Email"); phone=b.text_input("Phone")
        if st.form_submit_button("Add member"):
            try: insert("members",{"group_id":G,"full_name":full,"membership_no":no,"email":email or None,"phone":phone or None,"status":"active"}); st.success("Member added")
            except Exception as e: st.error(str(e))
    st.dataframe(df(safe_rows("members",filters={"group_id":G},order="created_at")),use_container_width=True,hide_index=True)

def contributions_page():
    page_title("Contributions")
    tab1,tab2=st.tabs(["Schedules","Payments"])
    with tab1: st.dataframe(df(safe_rows("contribution_schedules",filters={"group_id":G},order="due_date")),use_container_width=True,hide_index=True)
    with tab2: st.dataframe(df(safe_rows("contribution_payments",filters={"group_id":G},order="payment_date")),use_container_width=True,hide_index=True)

def verify_page():
    page_title("Payment Verification")
    pending=safe_rows("contribution_payments",filters={"group_id":G,"verification_status":"pending"},order="created_at")
    st.dataframe(df(pending),use_container_width=True,hide_index=True)
    if pending:
        labels={f"{x.get('mpesa_reference')} | {money(x.get('amount'))}":x for x in pending}; choice=st.selectbox("Payment",list(labels)); action=st.radio("Decision",["verified","rejected"],horizontal=True); note=st.text_input("Verification note")
        if st.button("Submit decision"):
            try: rpc("verify_contribution_payment",{"p_payment_id":labels[choice]["id"],"p_status":action,"p_note":note}); st.success("Decision recorded"); st.rerun()
            except Exception as e: st.error(str(e))

def loans_page():
    page_title("Loans")
    st.dataframe(df(safe_rows("loan_applications",filters={"group_id":G},order="created_at")),use_container_width=True,hide_index=True)
    st.subheader("Active loans"); st.dataframe(df(safe_rows("loans",filters={"group_id":G},order="created_at")),use_container_width=True,hide_index=True)

def investments_page():
    page_title("Investment Register")
    with st.form("investment"):
        a,b,c=st.columns(3); name=a.text_input("Investment name"); cls=b.selectbox("Class",["fixed_deposit","treasury_bill","treasury_bond","listed_equity","reit","venture_capital","private_equity","investment_property","money_market_fund","other"]); currency=c.text_input("Currency",value="KES")
        cost=a.number_input("Acquisition cost",min_value=0.0); fair=b.number_input("Current fair value",min_value=0.0); acquired=c.date_input("Acquisition date",value=date.today())
        if st.form_submit_button("Add investment"):
            try: insert("investments",{"group_id":G,"name":name,"investment_class":cls,"currency":currency,"acquisition_cost":cost,"carrying_value":fair or cost,"fair_value":fair or cost,"acquisition_date":str(acquired),"status":"active"}); st.success("Investment added")
            except Exception as e: st.error(str(e))
    st.dataframe(df(safe_rows("investments",filters={"group_id":G},order="created_at")),use_container_width=True,hide_index=True)

def returns_page():
    page_title("Monthly Investment Returns")
    inv=safe_rows("investments",filters={"group_id":G,"status":"active"})
    if not inv: st.info("Add an active investment first."); return
    labels={x["name"]:x["id"] for x in inv}
    with st.form("return"):
        name=st.selectbox("Investment",list(labels)); month=st.date_input("Reporting month",value=date.today().replace(day=1)); gross=st.number_input("Gross return",min_value=0.0); direct=st.number_input("Direct expenses",min_value=0.0); tax=st.number_input("Tax",min_value=0.0); other=st.number_input("Other deductions",min_value=0.0)
        if st.form_submit_button("Save draft"):
            try: insert("investment_monthly_returns",{"group_id":G,"investment_id":labels[name],"reporting_month":str(month),"gross_return":gross,"direct_expenses":direct,"tax_amount":tax,"other_deductions":other,"net_return":gross-direct-tax-other,"status":"draft"}); st.success("Draft return recorded")
            except Exception as e: st.error(str(e))
    st.dataframe(df(safe_rows("investment_monthly_returns",filters={"group_id":G},order="reporting_month")),use_container_width=True,hide_index=True)

def allocation_page():
    page_title("Member Return Allocation")
    month=st.date_input("Reporting month",value=date.today().replace(day=1))
    st.info("The posting function freezes eligible balances, allocates approved distributable return proportionately and creates member ledger entries.")
    if st.button("Calculate and post allocation",type="primary"):
        try: result=rpc("post_monthly_return_allocation",{"p_group_id":G,"p_reporting_month":str(month)}); st.success(f"Batch posted: {result}")
        except Exception as e: st.error(str(e))
    st.dataframe(df(safe_rows("member_return_allocations",filters={"group_id":G},order="created_at")),use_container_width=True,hide_index=True)

def accounting_page():
    page_title("Accounting")
    tabs=st.tabs(["Trial Balance","Journals","Chart of Accounts"])
    with tabs[0]:
        try: st.dataframe(df(rpc("trial_balance",{"p_group_id":G})),use_container_width=True,hide_index=True)
        except Exception as e: st.error(str(e))
    with tabs[1]: st.dataframe(df(safe_rows("journal_headers",filters={"group_id":G},order="journal_date")),use_container_width=True,hide_index=True)
    with tabs[2]: st.dataframe(df(safe_rows("chart_of_accounts",filters={"group_id":G},order="account_code")),use_container_width=True,hide_index=True)

def reconciliation(kind):
    page_title(kind)
    table="bank_reconciliations" if kind.startswith("Bank") else "investment_reconciliations"
    st.dataframe(df(safe_rows(table,filters={"group_id":G},order="created_at")),use_container_width=True,hide_index=True)
    st.caption("Import and matching are controlled by the database reconciliation tables and approval status.")

def reports_page():
    page_title("Reports")
    report=st.selectbox("Report",["Members","Contributions","Loans","Investments","Member allocations","General ledger"])
    mapping={"Members":"members","Contributions":"contribution_payments","Loans":"loans","Investments":"investments","Member allocations":"member_return_allocations","General ledger":"journal_lines"}
    data=safe_rows(mapping[report],filters={"group_id":G})
    d=df(data); st.dataframe(d,use_container_width=True,hide_index=True)
    st.download_button("Download CSV",d.to_csv(index=False).encode(),file_name=f"{report.lower().replace(' ','_')}.csv",mime="text/csv")

def audit_page(): page_title("Audit Log"); st.dataframe(df(safe_rows("audit_logs",filters={"group_id":G},order="created_at")),use_container_width=True,hide_index=True)
def settings_page(): page_title("Settings"); st.json({k:v for k,v in P.items() if k not in ("id","user_id")})

def member_dashboard():
    page_title("My Dashboard")
    contrib=safe_rows("member_investment_transactions",filters={"group_id":G,"member_id":M})
    loans=safe_rows("loans",filters={"group_id":G,"member_id":M})
    alloc=safe_rows("member_return_allocations",filters={"group_id":G,"member_id":M})
    a,b,c=st.columns(3); a.metric("Investment balance",money(sum(float(x.get('amount',0)) for x in contrib))); b.metric("Loan principal",money(sum(float(x.get('principal',0)) for x in loans))); c.metric("Allocated returns",money(sum(float(x.get('net_return_allocated',0)) for x in alloc)))

def my_table(title,table): page_title(title); st.dataframe(df(safe_rows(table,filters={"group_id":G,"member_id":M},order="created_at")),use_container_width=True,hide_index=True)
def submit_payment():
    page_title("Submit Payment Reference")
    with st.form("pay"):
        ref=st.text_input("M-Pesa reference").upper(); amount=st.number_input("Amount",min_value=1.0); dt=st.date_input("Payment date")
        if st.form_submit_button("Submit"):
            try: insert("contribution_payments",{"group_id":G,"member_id":M,"mpesa_reference":ref,"amount":amount,"payment_date":str(dt),"payment_method":"mpesa","verification_status":"pending"}); st.success("Submitted for verification")
            except Exception as e: st.error(str(e))

def statement():
    page_title("My Statement")
    data=safe_rows("member_investment_transactions",filters={"group_id":G,"member_id":M},order="transaction_date"); d=df(data); st.dataframe(d,use_container_width=True,hide_index=True); st.download_button("Download statement",d.to_csv(index=False).encode(),"my_statement.csv","text/csv")

routes={"Dashboard":admin_dashboard,"Members":members_page,"Contributions":contributions_page,"Payment Verification":verify_page,"Loans":loans_page,"Investments":investments_page,"Monthly Returns":returns_page,"Return Allocation":allocation_page,"Accounting":accounting_page,"Bank Reconciliation":lambda:reconciliation("Bank Reconciliation"),"Investment Reconciliation":lambda:reconciliation("Investment Reconciliation"),"Reports":reports_page,"Audit Log":audit_page,"Settings":settings_page,"My Dashboard":member_dashboard,"My Contributions":lambda:my_table("My Contributions","contribution_schedules"),"Submit Payment":submit_payment,"My Loans":lambda:my_table("My Loans","loans"),"My Investments":lambda:my_table("My Investments","member_investment_transactions"),"My Returns":lambda:my_table("My Returns","member_return_allocations"),"My Statement":statement}
routes[page]()
