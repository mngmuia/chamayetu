import streamlit as st
from supabase import create_client

@st.cache_resource
def client():
    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_ANON_KEY")
    if not url or not key:
        raise RuntimeError("Add SUPABASE_URL and SUPABASE_ANON_KEY to Streamlit secrets.")
    return create_client(url, key)

def rows(table, columns="*", filters=None, order=None, limit=500):
    q = client().table(table).select(columns)
    for k, v in (filters or {}).items(): q = q.eq(k, v)
    if order: q = q.order(order, desc=True)
    return q.limit(limit).execute().data or []

def insert(table, payload):
    return client().table(table).insert(payload).execute().data

def update(table, payload, record_id):
    return client().table(table).update(payload).eq("id", record_id).execute().data

def rpc(name, params):
    return client().rpc(name, params).execute().data
