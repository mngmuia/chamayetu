import streamlit as st

def page_title(title, subtitle=None):
    st.title(title)
    if subtitle: st.caption(subtitle)

def status_badge(value):
    colours={"verified":"green","approved":"green","posted":"green","pending":"orange","rejected":"red","overdue":"red"}
    return f":{colours.get(str(value).lower(),'blue')}[{value}]"
