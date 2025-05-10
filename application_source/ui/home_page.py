import streamlit as st
import time
from services.db_controller import DBController
from services.agent_controller import Agent_Controller  ## only to load and cache at start

st.set_page_config(page_title="Login", layout="wide", initial_sidebar_state="collapsed")
controller = DBController()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user" not in st.session_state:
    st.session_state.user = ""

if "user_name" not in st.session_state:
    st.session_state.user_name = ""

params = st.query_params

# If user is redirected back from Google OAuth
if "code" in params and "state" in params:
    st.session_state.user = params["state"]
    st.session_state.logged_in = True

def login():
    # st.title("🔐 Login")
    cols = st.columns([3, 6, 3])
    divs = 15
    button_col = st.columns(divs)

    with cols[1]:

        st.markdown("<h1 style='text-align: center;'>🔐 Login</h1>", unsafe_allow_html=True)
        userid = st.text_input("User ID :")
        password = st.text_input("Password :", type="password")

        if button_col[int(divs/2)].button("Login"):
            validation = controller.validate_seller(userid)
            if validation:
                st.session_state.logged_in = True
                st.session_state.user = userid
                st.success("Login successful! Redirecting to dashboard...")
                time.sleep(1)
                st.rerun()  # Refresh to trigger navigation
            else:
                st.toast("Invalid username or password")

if st.session_state.logged_in:
    pages = {"Navigation": [
        st.Page("pages_dir/page_dashboard.py", title="Dashboard"),
        st.Page("pages_dir/page_notes.py", title="Meeting Notes")]
    }

    pg = st.navigation(pages)
    pg.run()
else:
    login()
