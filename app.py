import streamlit as st
import pandas as pd
import os
import datetime
import json
import logging
import time

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Alert log file name
ALERTS_LOG_FILE = "alert/alerts.log"

# --- Assumed external functions and variables ---
# You need to ensure these functions are defined or imported correctly if they are not here
# For example:
# my_email = "your_email@example.com"
# my_password = "your_password_app_specific"
# recipient_email = "recipient@example.com"
# github_token = "your_github_token"

def send_drift_notification_email(sender, password, recipient, info):
    """Simulates sending an email."""
    # st.info(f"Sending notification email to {recipient}...") # Can remove this line if not desired in UI
    time.sleep(0.5)
    print(f"Sending email to {recipient} with info: {info}")
    return True

def curl(action, clean_infra, provision_infra, token):
    """Simulates triggering a pipeline."""
    # st.info(f"Triggering pipeline '{action}'...") # Can remove this line
    time.sleep(0.5)
    print(f"Triggering pipeline action: {action}, clean_infra: {clean_infra}, provision_infra: {provision_infra}")
    return True


# --- Functions for Alert Logging and Dashboard (Modified) ---

def log_alert_event(alert_type: str, details: dict = None): # 'status' removed
    """
    Logs an alert event to the ALERTS_LOG_FILE.
    """
    event_data = {
        "timestamp": datetime.datetime.now().isoformat(),
        "alert_type": alert_type,
        "details": details if details else {}
    }
    with open(ALERTS_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(event_data, ensure_ascii=False) + "\n")
    logging.info(f"Logged alert event: Type='{alert_type}'")
    if 'alerts_updated' in st.session_state:
        st.session_state.alerts_updated = True


def load_alert_events():
    """
    Reads all alert events from the ALERTS_LOG_FILE.
    """
    events = []
    if os.path.exists(ALERTS_LOG_FILE):
        with open(ALERTS_LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    # Ensure correct reading of the new JSON structure (without 'status')
                    event = json.loads(line.strip())
                    # Add default 'status' if old log lines still have status, to avoid display errors
                    if 'status' not in event:
                        event['status'] = 'N/A' # Or another default value if needed
                    events.append(event)
                except json.JSONDecodeError:
                    logging.warning(f"Skipping malformed log line in {ALERTS_LOG_FILE}: {line.strip()}")
    # Sort events by timestamp, newest first
    events.sort(key=lambda x: x['timestamp'], reverse=True)
    return events

# Function to display the Alert Dashboard (Modified)
def show_alerts_dashboard():
    st.title("🚨 Alerts Managemnet")

    if 'alerts_updated' not in st.session_state:
        st.session_state.alerts_updated = False

    col1, col2 = st.columns([0.8, 0.15])
    with col1:
        st.write("Click the 'Refresh' button to see the latest alerts.")
        if st.button("🔄 Refresh Dashboard"):
            st.session_state.alerts_updated = True
    # with col2:
    #     if st.button("🔄 Refresh Dashboard"):
    #         st.session_state.alerts_updated = True


    if st.session_state.alerts_updated:
        st.session_state.alerts_updated = False
        st.info("Loading latest alerts...")
        alerts = load_alert_events()
    else:
        alerts = load_alert_events()

    if not alerts:
        st.info("No alerts have been logged yet.")
    else:
        alert_container = st.container(height=600, border=True)
        with alert_container:
            for alert in alerts:
                # Only display a general alert icon
                status_emoji = "🔴" # Keep general alert icon

                # Format timestamp
                date_obj = datetime.datetime.fromisoformat(alert['timestamp'])
                formatted_timestamp = date_obj.strftime("%d/%m/%Y %H:%M:%S")

                # HTML for expander title (status and status-based color removed)
                expander_title_html = (
                    f"{status_emoji} **{alert['alert_type']}** "
                    f"(Time: {formatted_timestamp})"
                )

                with st.expander(expander_title_html, expanded=False):
                    st.json(alert['details'])

# --- LOGIN ---
def login():
    st.title("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == "admin" and password == "123":
            st.session_state["logged_in"] = True
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid username or password. Please try again.")

# ---------- DASHBOARD ----------
def show_dashboard():
    st.title("📊 Model Monitoring Reports")
    base_dir = "reports"
    if not os.path.exists(base_dir):
        st.warning("Folder 'reports' does not exist. Please upload reports first.")
        return

    dashboard_types = sorted([name for name in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, name))])
    if not dashboard_types:
        st.warning("No report types found in the 'reports' folder.")
        return

    dashboard_tabs = st.tabs(dashboard_types)
    for dash_tab, dash_type in zip(dashboard_tabs, dashboard_types):
        with dash_tab:
            report_path = os.path.join(base_dir, dash_type)
            report_files = sorted([f for f in os.listdir(report_path) if f.endswith(".html")], reverse=True)
            sub_tab_names = [os.path.splitext(f)[0] for f in report_files]
            if not report_files:
                st.warning("No reports found in this category.")
            else:
                sub_tabs = st.tabs(sub_tab_names)
                for sub_tab, report_file in zip(sub_tabs, report_files):
                    with sub_tab:
                        with open(os.path.join(report_path, report_file), "r", encoding="utf-8") as f:
                            html_content = f.read()
                        st.components.v1.html(html_content, height=1000, scrolling=True)

# ---------- LOAD & EDIT CSV ----------
def csv_editor():
    st.title("📁 Validate Model Results")

    load_option = st.radio(
        "Choose how to load the CSV file:",
        ("Upload from computer", "Choose from 'results' folder")
    )

    df = None
    selected_file_name = None

    if load_option == "Upload from computer":
        uploaded_file = st.file_uploader("Drag and drop a CSV file here", type=["csv"])
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                selected_file_name = uploaded_file.name
                st.success(f"File loaded successfully: {uploaded_file.name}")
            except Exception as e:
                st.error(f"Error loading file: {e}")
        else:
            st.info("Please upload a CSV file to get started.")
            return

    elif load_option == "Choose from 'results' folder":
        results_dir = "results"
        if not os.path.exists(results_dir):
            st.warning("⚠️ Folder 'results' not found. Please create this folder if you want to select files from here.")
            return

        csv_files = [f for f in os.listdir(results_dir) if f.endswith(".csv")]
        if not csv_files:
            st.info("📭 No CSV files found in the 'results' folder.")
            return

        selected_file = st.selectbox("Select a CSV file", options=csv_files)
        if selected_file:
            file_path = os.path.join(results_dir, selected_file)
            df = pd.read_csv(file_path)
            selected_file_name = selected_file

    if df is not None:
        filtered_df = df.copy()

        if 'label' in df.columns:
            st.subheader("🔍 Filter by 'label'")
            label_values = df['label'].dropna().unique().tolist()
            selected_labels = st.multiselect(
                "Select label values to view",
                options=label_values,
                default=label_values
            )

            if selected_labels:
                filtered_df = df[df['label'].isin(selected_labels)]
            else:
                st.info("No labels selected, showing all data.")
                filtered_df = df.copy()
        elif 'Label' in df.columns:
            st.subheader("🔍 Filter by 'Label'")
            label_values = df['Label'].dropna().unique().tolist()
            selected_labels = st.multiselect(
                "Select Label values to view",
                options=label_values,
                default=label_values
            )

            if selected_labels:
                filtered_df = df[df['Label'].isin(selected_labels)]
            else:
                st.info("No Labels selected, showing all data.")
                filtered_df = df.copy()
        else:
            st.info("ℹ️ CSV file does not have a 'label' or 'Label' column. No label filter will be applied.")

        st.subheader("✏️ Edit data:")
        edited_df = st.data_editor(filtered_df, num_rows="dynamic", use_container_width=True)

        csv = edited_df.to_csv(index=False).encode("utf-8")
        download_file_name = f"edited_{selected_file_name}" if selected_file_name else "edited_data.csv"

        st.download_button(
            "⬇️ Download edited CSV",
            csv,
            file_name=download_file_name,
            mime="text/csv"
        )


# ---------- MAIN APP ----------
def main():
    st.set_page_config(page_title="Dashboard Application", layout="wide")

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        login()
    else:
        menu = st.sidebar.radio("📌 Menu", ["📊 Model Monitoring Reports", "📁 Validate Results", "🚨 Alerts", "🔓 Logout"])

        if menu == "📊 Model Monitoring Reports":
            show_dashboard()
        elif menu == "📁 Validate Results":
            csv_editor()
        elif menu == "🚨 Alerts":
            show_alerts_dashboard()
            # st.markdown("---")
            
        elif menu == "🔓 Logout":
            st.session_state["logged_in"] = False
            st.success("Logged out successfully.")
            st.rerun()

if __name__ == "__main__":
    main()
