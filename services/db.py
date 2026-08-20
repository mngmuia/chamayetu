import streamlit as st
from supabase import create_client

@st.cache_resource
def db():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_ANON_KEY"])

def get(table, filters=None, order=None, limit=1000):
    q = db().table(table).select("*")
    for key, value in (filters or {}).items():
        if value is not None:
            q = q.eq(key, value)
    if order:
        q = q.order(order, desc=True)
    return q.limit(limit).execute().data or []

def add(table, row):
    return db().table(table).insert(row).execute().data or []

def upsert(table, row):
    return db().table(table).upsert(row).execute().data or []
