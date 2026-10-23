"""Log in, register and log out (criterion 5)."""

import streamlit as st

from pawmatch import auth
from webui.components import show_errors
from webui.state import PAGES, current_user, database, sign_in, sign_out


user = current_user()
if user:
    st.title("My account")
    st.write(f"Signed in as **{user.name}** ({user.email}).")
    if user.is_admin:
        st.caption("Staff account: the Manage animals page is in the menu.")
    if st.button("Log out", icon=":material/logout:"):
        sign_out()
        st.switch_page(PAGES["home"])
    st.stop()

st.title("Welcome to PawMatch")
login_tab, register_tab = st.tabs(["Log in", "Register"])

with login_tab, st.form("login"):
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.form_submit_button("Log in", type="primary"):
        with database() as conn:
            found, errors = auth.login(conn, email, password)
        if found:
            sign_in(found)
            st.switch_page(PAGES["home"])
        show_errors(errors)

with register_tab, st.form("register"):
    name = st.text_input("Full name", max_chars=50)
    new_email = st.text_input("Email address")
    age = st.text_input("Age", help="You must be 18 or over to adopt.")
    new_password = st.text_input("Password (at least 8 characters)", type="password")
    confirm = st.text_input("Confirm password", type="password")
    if st.form_submit_button("Create account", type="primary"):
        with database() as conn:
            created, errors = auth.register(conn, name, new_email, age, new_password, confirm)
        if created:
            sign_in(created)
            st.switch_page(PAGES["questionnaire"])
        show_errors(errors)
