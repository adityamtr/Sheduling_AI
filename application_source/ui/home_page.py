import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="AI Assistant",
    layout="wide",
    initial_sidebar_state="collapsed"  # This hides the sidebar initially
)


pages = {"Navigation":[
        st.Page("pages_dir/page_dashboard.py", title="Dashboard"),
        st.Page("pages_dir/page_notes.py", title="Meeting Notes")]
}

pg = st.navigation(pages)
pg.run()