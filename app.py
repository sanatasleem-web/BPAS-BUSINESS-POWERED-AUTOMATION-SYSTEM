import streamlit as st
import requests
import pandas as pd
import time

# --- CONFIGURATION ---
st.set_page_config(
    page_title="CogniDesk HR+",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)
API_URL = "http://127.0.0.1:8000"

# --- STYLING ---
st.markdown("""
<style>
    .stMetric {
        border-radius: 10px;
        padding: 15px;
        background-color: #f0f2f6;
        border: 1px solid #ddd;
    }
</style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
def login_user(username, password):
    try:
        response = requests.post(f"{API_URL}/token", data={"username": username, "password": password}, timeout=5)
        if response.status_code == 200:
            token_data = response.json()
            profile_res = requests.get(f"{API_URL}/employees/{username}", timeout=5)
            if profile_res.status_code == 200:
                st.session_state.profile = profile_res.json()
            return token_data["access_token"], st.session_state.profile.get("designation", "employee")
        else:
            st.error("Invalid username or password.")
            return None, None
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        st.error("Connection Error: Could not connect to the backend.")
        return None, None
        
def get_all_employee_data():
    try:
        res = requests.get(f"{API_URL}/employees", timeout=5)
        return res.json() if res.status_code == 200 else []
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        st.error("Connection Error: Failed to fetch employee data.")
        return []

def get_all_tickets():
    try:
        res = requests.get(f"{API_URL}/tickets/", timeout=5)
        return res.json() if res.status_code == 200 else []
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return []

def submit_ticket(query):
    try:
        res = requests.post(f"{API_URL}/tickets/", json={"query": query}, timeout=60)
        return res.json() if res.status_code == 201 else None
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return None

# --- UI SECTIONS ---
def show_login_page():
    st.image("https://www.onepointltd.com/wp-content/uploads/2020/03/inno2.png", width=200)
    st.title("Welcome to CogniDesk HR+ 🤖")
    
    with st.form("login_form"):
        username = st.text_input("Username", value="employee")
        password = st.text_input("Password", type="password", value="emppassword")
        submitted = st.form_submit_button("Login 🚀")

        if submitted:
            token, role = login_user(username, password)
            if token and role:
                st.success("Login Successful!")
                st.balloons()
                time.sleep(1.5)
                st.session_state.logged_in = True
                st.session_state.token = token
                st.session_state.role = "admin" if username == "admin" else "employee"
                st.rerun()

def show_employee_view():
    profile = st.session_state.profile
    st.sidebar.title(f"Welcome, {profile['name']}")
    st.sidebar.info(f"**Designation:** {profile['designation']}")
    
    tab1, tab2 = st.tabs(["My Profile 👤", "Helpdesk AI 💬"])
    
    with tab1:
        st.header("My Employee Profile")
        st.divider()
        col1, col2, col3 = st.columns(3)
        col1.markdown(f"**Employee ID:** `{profile['id']}`")
        col2.markdown(f"**Email:** `{profile['email']}`")
        # --- NEW: Displaying Experience ---
        col3.markdown(f"**Experience:** `{profile['experience_years']} Years`")
        st.divider()
        st.subheader("Payroll, Attendance & Leave")
        m1, m2, m3 = st.columns(3)
        m1.metric("Salary (Annual INR)", f"₹{profile['salary']:,}")
        m2.metric("Attendance", f"{profile['attendance_percentage']}%")
        m3.metric("Leaves Taken (YTD)", f"{profile['leaves_taken']} days")
        
    with tab2:
        st.header("AI-Powered Helpdesk")
        query = st.text_area("Your Query:", placeholder="e.g., How do I reset my password?", height=150)
        if st.button("Submit Ticket ✉️", type="primary"):
            if query:
                with st.spinner("AI is thinking..."):
                    ticket = submit_ticket(query)
                    if ticket:
                        st.success("Response from AI Agent:")
                        st.info(f"Status: {ticket['status'].capitalize()}")
                        st.markdown(f"> {ticket['response']}")
                    else:
                        st.error("Failed to submit ticket.")

def show_admin_view():
    profile = st.session_state.profile
    st.sidebar.title(f"Welcome, {profile['name']}")
    st.sidebar.info(f"**Role:** {profile['designation']}")

    tab1, tab2 = st.tabs(["Employee Management 🧑‍🤝‍🧑", "Helpdesk Analytics 📊"])

    with tab1:
        st.header("Employee Management Dashboard")
        employee_df = pd.DataFrame(get_all_employee_data())
        
        # --- NEW: Added experience_years to the display ---
        display_cols = ['id', 'name', 'designation', 'email', 'salary', 'experience_years', 'attendance_percentage', 'leaves_taken']
        employee_df = employee_df[display_cols]
        
        search_query = st.text_input("Search by Name or Designation")
        if search_query:
            employee_df = employee_df[
                employee_df["name"].str.contains(search_query, case=False) |
                employee_df["designation"].str.contains(search_query, case=False)
            ]
        
        st.dataframe(employee_df, use_container_width=True, height=500)
    
    with tab2:
        st.header("Helpdesk Ticket Analytics")
        # (No changes in this section)
        tickets = get_all_tickets()
        if tickets:
            df = pd.DataFrame(tickets)
            col1, col2, col3, col4 = st.columns(4)
            status_counts = df['status'].value_counts()
            col1.metric("Total Tickets", len(df))
            col2.metric("✅ Closed by AI", status_counts.get('closed', 0))
            col3.metric("⚠️ Escalated", status_counts.get('escalated', 0))
            col4.metric("🔵 Open", status_counts.get('open', 0))
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("No tickets found.")

# --- MAIN APP LOGIC ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    show_login_page()
else:
    if st.sidebar.button("Logout 👋"):
        st.session_state.logged_in = False
        st.session_state.pop("token", None)
        st.session_state.pop("role", None)
        st.session_state.pop("profile", None)
        st.rerun()
        
    if st.session_state.role == "admin":
        show_admin_view()
    else:
        show_employee_view()