import streamlit as st

def init_session():
    defaults = {"user": None, "profile": None, "active_view": "member", "group_id": None, "member_id": None}
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)

def sign_out():
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()
