import streamlit as st, pandas as pd, plotly.express as px
from datetime import date
from services.db import db,get,add,upsert
from services.auth import login,logout
st.set_page_config(page_title='Chama Yetu',page_icon='💠',layout='wide')
def money(x): return f"KES {float(x or 0):,.2f}"
for k,v in {'user':None,'profile':None,'view':'member'}.items():st.session_state.setdefault(k,v)
if not st.session_state.user:
 st.title('Chama Yetu');st.caption('Members • Investments • Accounting')
 with st.form('login'):
  e=st.text_input('Email');p=st.text_input('Password',type='password');go=st.form_submit_button('Sign in',use_container_width=True)
 if go:
  try: st.session_state.user,st.session_state.profile=login(e,p);st.session_state.view='admin' if st.session_state.profile['role']=='admin' else 'member';st.rerun()
  except Exception as ex:st.error(str(ex))
 st.stop()
P=st.session_state.profile;G=P['group_id'];M=P.get('member_id');is_admin=P.get('role')=='admin'
admin_pages=['Dashboard','Members','Historical Payments','Roles','Loans','Investments','Monthly Returns','Accounting','Reports','Settings']
member_pages=['My Dashboard','My Contributions','My Loans','My Investments','My Returns','My Statement']
with st.sidebar:
 st.header('Chama Yetu');st.write(P.get('full_name'))
 if is_admin:st.session_state.view=st.segmented_control('View as',['admin','member'],default=st.session_state.view)
 page=st.radio('Navigation',admin_pages if st.session_state.view=='admin' else member_pages)
 if st.button('Sign out'):logout();st.session_state.clear();st.rerun()
def data(t,filters=None,order=None):
 try:return get(t,filters,order)
 except Exception as e:st.error(str(e));return []
def frame(x):return pd.DataFrame(x)
def dashboard():
 st.title('Administrator BI')
 mem=data('members',{'group_id':G});pay=data('contribution_payments',{'group_id':G});loans=data('loans',{'group_id':G});inv=data('admin_bi_investments',{'group_id':G})
 a,b,c,d=st.columns(4);a.metric('Members',len(mem));b.metric('Verified contributions',money(sum(float(x.get('amount',0)) for x in pay if x.get('verification_status')=='verified')));c.metric('Active loan principal',money(sum(float(x.get('principal_amount',0)) for x in loans)));d.metric('Investment fair value',money(sum(float(x.get('fair_value',0)) for x in inv)))
 monthly=data('admin_bi_monthly_contributions',{'group_id':G},'reporting_month')
 if monthly:st.plotly_chart(px.bar(frame(monthly),x='reporting_month',y='verified_amount',title='Verified contributions by month'),use_container_width=True)
 if inv:st.plotly_chart(px.bar(frame(inv),x='name',y='net_return',color='investment_class',title='Net returns by investment'),use_container_width=True)
def members():
 st.title('Members')
 with st.form('m'):
  n=st.text_input('Full name');no=st.text_input('Membership number');e=st.text_input('Email');phone=st.text_input('Phone')
  if st.form_submit_button('Create member'):add('members',{'group_id':G,'full_name':n,'membership_number':no,'email':e or None,'phone':phone or None,'status':'active'});st.success('Member created')
 st.dataframe(frame(data('members',{'group_id':G})),use_container_width=True,hide_index=True)
def historical():
 st.title('Historical Payments');f=st.file_uploader('Upload CSV',type=['csv'])
 if f:
  d=pd.read_csv(f);st.dataframe(d,use_container_width=True)
  if st.button('Import as draft batch'):
   batch=add('import_batches',{'group_id':G,'file_name':f.name,'import_type':'contribution_payments','record_count':len(d),'total_amount':float(d['amount'].sum()),'status':'draft','created_by':st.session_state.user.id})[0]
   for _,r in d.iterrows():add('contribution_payments',{'group_id':G,'member_id':r['member_id'],'amount':float(r['amount']),'payment_date':str(r['payment_date']),'payment_method':r.get('payment_method','historical'),'payment_reference':str(r.get('payment_reference','')) or None,'verification_status':'pending','is_historical':True,'import_batch_id':batch['id']})
   st.success('Draft import created for checking and approval')
def roles():st.title('Roles');st.dataframe(frame(data('app_roles',{'group_id':G})),use_container_width=True,hide_index=True);st.dataframe(frame(data('user_group_roles',{'group_id':G})),use_container_width=True,hide_index=True)
def investments():
 st.title('Investments')
 with st.form('i'):
  n=st.text_input('Name');typ=st.selectbox('Class',['money_market_fund','treasury_bill','treasury_bond','listed_equity','reit','venture_capital','private_equity','investment_property']);cost=st.number_input('Cost',min_value=0.0);fv=st.number_input('Fair value',min_value=0.0)
  if st.form_submit_button('Add investment'):add('investments',{'group_id':G,'name':n,'investment_class':typ,'acquisition_cost':cost,'carrying_value':fv or cost,'fair_value':fv or cost,'status':'active'});st.success('Investment added')
 st.dataframe(frame(data('investments',{'group_id':G})),use_container_width=True,hide_index=True)
def settings():
 if not is_admin:st.error('Settings are available only to the administrator.');return
 st.title('Administrator Settings');rows=data('group_settings',{'group_id':G});s=rows[0] if rows else {'group_id':G}
 with st.form('s'):
  mx=st.number_input('Absolute maximum loan',value=float(s.get('max_loan_amount') or 0));mult=st.number_input('Maximum multiple of member balance',value=float(s.get('max_loan_multiple') or 3));rate=st.number_input('Default interest rate %',value=float(s.get('interest_rate') or 12));term=st.number_input('Maximum term months',value=int(s.get('max_term_months') or 24));checker=st.checkbox('Require checker',value=s.get('require_checker',True));approver=st.checkbox('Require approver',value=s.get('require_approver',True))
  if st.form_submit_button('Save settings'):upsert('group_settings',{'group_id':G,'max_loan_amount':mx or None,'max_loan_multiple':mult,'interest_rate':rate,'max_term_months':term,'require_checker':checker,'require_approver':approver});st.success('Settings saved')
def member_dash():
 st.title('My BI Dashboard');x=data('member_bi_summary',{'group_id':G,'member_id':M});s=x[0] if x else {};a,b,c,d=st.columns(4);a.metric('Contributions',money(s.get('total_contributions')));b.metric('Investment balance',money(s.get('investment_balance')));c.metric('Allocated returns',money(s.get('total_returns')));d.metric('Active loan principal',money(s.get('active_loan_principal')))
def generic(title,t,member=False):st.title(title);st.dataframe(frame(data(t,{'group_id':G,**({'member_id':M} if member else {})})),use_container_width=True,hide_index=True)
routes={'Dashboard':dashboard,'Members':members,'Historical Payments':historical,'Roles':roles,'Loans':lambda:generic('Loans','loans'),'Investments':investments,'Monthly Returns':lambda:generic('Monthly Returns','investment_monthly_returns'),'Accounting':lambda:generic('Accounting Journals','journal_headers'),'Reports':lambda:generic('Contribution Report','contribution_payments'),'Settings':settings,'My Dashboard':member_dash,'My Contributions':lambda:generic('My Contributions','contribution_payments',True),'My Loans':lambda:generic('My Loans','loans',True),'My Investments':lambda:generic('My Investments','member_investment_transactions',True),'My Returns':lambda:generic('My Returns','member_return_allocations',True),'My Statement':lambda:generic('My Statement','member_investment_transactions',True)}
routes[page]()
