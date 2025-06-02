import streamlit as st
import pandas as pd
import os
import datetime
import json
import logging
import time
import matplotlib.pyplot as plt
import plotly.express as px

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Alert log file name
ALERTS_LOG_FILE = "alert/alerts.log" # Ensure this path is correct

# --- Assumed external functions and variables ---
# You need to ensure these functions are defined or imported correctly if they are not here
# For example:
# my_email = "your_email@example.com"
# my_password = "your_password_app_specific"
# recipient_email = "recipient@example.com"
# github_token = "your_github_token"

def send_drift_notification_email(sender, password, recipient, info):
    """Simulates sending an email."""
    time.sleep(0.5)
    print(f"Sending email to {recipient} with info: {info}")
    return True

def curl(action, clean_infra, provision_infra, token):
    """Simulates triggering a pipeline."""
    time.sleep(0.5)
    print(f"Triggering pipeline action: {action}, clean_infra: {clean_infra}, provision_infra: {provision_infra}")
    return True

# --- Functions for Alert Logging and Dashboard ---

def log_alert_event(alert_type: str, details: dict = None):
    """
    Logs an alert event to the ALERTS_LOG_FILE.
    """
    # Ensure the directory exists before writing the file
    os.makedirs(os.path.dirname(ALERTS_LOG_FILE), exist_ok=True)
    
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
                    event = json.loads(line.strip())
                    if 'status' not in event: # Compatibility for old log lines if they exist
                        event['status'] = 'N/A' 
                    events.append(event)
                except json.JSONDecodeError:
                    logging.warning(f"Skipping malformed log line in {ALERTS_LOG_FILE}: {line.strip()}")
    events.sort(key=lambda x: x['timestamp'], reverse=True)
    return events

# Function to display the Alert Dashboard (Modified with Statistics and Filters)
def show_alerts_dashboard():
    st.title("🚨 Alerts Management")

    if 'alerts_updated' not in st.session_state:
        st.session_state.alerts_updated = False

    col_btn_refresh, col_empty = st.columns([0.2, 0.8])
    with col_btn_refresh:
        if st.button("🔄 Refresh Dashboard"):
            st.session_state.alerts_updated = True

    # Load all alerts
    alerts = load_alert_events()

    if not alerts:
        st.info("No alerts have been logged yet.")
        return # Exit if no alerts to prevent errors with DataFrame operations
    
    df_alerts = pd.DataFrame(alerts)
    df_alerts['timestamp_dt'] = pd.to_datetime(df_alerts['timestamp'])
    df_alerts['date'] = df_alerts['timestamp_dt'].dt.date
    df_alerts['hour'] = df_alerts['timestamp_dt'].dt.hour

    st.markdown("---")
    st.subheader("⚙️ Filter Alerts")

    # --- Filtering Controls ---
    col_filter1, col_filter2, col_filter3 = st.columns([0.3, 0.4, 0.3])
    
    with col_filter1:
        # Filter by Alert Type
        all_alert_types = sorted(df_alerts['alert_type'].unique().tolist())
        selected_alert_types = st.multiselect(
            "Select Alert Type(s):", 
            options=all_alert_types, 
            default=all_alert_types
        )

    with col_filter2:
        # Search by Keyword in Details
        search_query = st.text_input("Search in Alert Details (keyword):").lower()

    with col_filter3:
        # Filter by Date Range
        today = datetime.date.today()
        # Calculate min and max dates from available data
        min_date_in_data = df_alerts['date'].min()
        max_date_in_data = df_alerts['date'].max()

        # Adjust default start date to be within the data range
        default_start_date = today - datetime.timedelta(days=7)
        if default_start_date < min_date_in_data:
            default_start_date = min_date_in_data
        
        # Ensure default end date is not beyond max_date_in_data
        default_end_date = today
        if default_end_date > max_date_in_data:
            default_end_date = max_date_in_data

        # Ensure that default_start_date does not exceed default_end_date
        if default_start_date > default_end_date:
            default_start_date = default_end_date # Fallback if start date is after end date

        date_range = st.date_input(
            "Select Date Range:",
            # Ensure default value is within min_value and max_value
            value=(default_start_date, default_end_date), 
            min_value=min_date_in_data,
            max_value=max_date_in_data
        )
        
        # Ensure date_range has two dates selected
        start_date = None
        end_date = None
        if len(date_range) == 2:
            start_date = date_range[0]
            end_date = date_range[1]
        elif len(date_range) == 1: # If only one date is selected, assume it's the start date
            start_date = date_range[0]
            end_date = date_range[0] # End date is same as start date

    # --- Apply Filters ---
    filtered_df_alerts = df_alerts.copy()

    # Apply Alert Type filter
    if selected_alert_types:
        filtered_df_alerts = filtered_df_alerts[filtered_df_alerts['alert_type'].isin(selected_alert_types)]
    
    # Apply Search Query filter
    if search_query:
        # Search in the 'details' column, converted to string for keyword search
        filtered_df_alerts = filtered_df_alerts[
            filtered_df_alerts['details'].astype(str).str.lower().str.contains(search_query)
        ]

    # Apply Date Range filter
    if start_date and end_date:
        filtered_df_alerts = filtered_df_alerts[
            (filtered_df_alerts['date'] >= start_date) & 
            (filtered_df_alerts['date'] <= end_date)
        ]

    st.info(f"Showing {len(filtered_df_alerts)} alerts based on current filters.")

    st.markdown("---")
    st.subheader("📊 Alert Statistics (Filtered Data)")

    if not filtered_df_alerts.empty:
        col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
        with col_kpi1:
            st.metric("Total Alerts (Filtered)", len(filtered_df_alerts))
        with col_kpi2:
            alerts_24h_filtered = filtered_df_alerts[filtered_df_alerts['timestamp_dt'] > (datetime.datetime.now() - datetime.timedelta(days=1))]
            st.metric("Alerts in Last 24 Hours (Filtered)", len(alerts_24h_filtered))
        with col_kpi3:
            most_common_alert_filtered = filtered_df_alerts['alert_type'].mode().get(0, "N/A")
            st.metric("Most Frequent Alert Type (Filtered)", most_common_alert_filtered)

        st.markdown("---")
        st.subheader("📈 Alert Trends and Breakdown (Filtered Data)")

        tab_type, tab_time = st.tabs(["Alert Type Breakdown", "Alerts Over Time"])

        with tab_type:
            alert_type_counts = filtered_df_alerts['alert_type'].value_counts().reset_index()
            alert_type_counts.columns = ['Alert Type', 'Count']
            st.dataframe(alert_type_counts, hide_index=True, use_container_width=True)

            fig_pie = px.pie(alert_type_counts, values='Count', names='Alert Type', title='Distribution of Alert Types (Filtered)')
            st.plotly_chart(fig_pie, use_container_width=True)

        with tab_time:
            # Daily trends for filtered data
            daily_alerts_filtered = filtered_df_alerts.groupby('date').size().reset_index(name='Count')
            daily_alerts_filtered['date'] = pd.to_datetime(daily_alerts_filtered['date'])
            daily_alerts_filtered = daily_alerts_filtered.sort_values('date')

            fig_line_daily = px.line(daily_alerts_filtered, x='date', y='Count', title='Daily Alert Count Trend (Filtered)')
            st.plotly_chart(fig_line_daily, use_container_width=True)

            # Hourly trends for filtered data (for a recent period, e.g., last 24h of filtered data)
            if not alerts_24h_filtered.empty:
                hourly_alerts_filtered = alerts_24h_filtered.groupby('hour').size().reset_index(name='Count')
                all_hours = pd.DataFrame({'hour': range(24)})
                hourly_alerts_filtered = pd.merge(all_hours, hourly_alerts_filtered, on='hour', how='left').fillna(0)
                hourly_alerts_filtered = hourly_alerts_filtered.sort_values('hour')

                fig_bar_hourly = px.bar(hourly_alerts_filtered, x='hour', y='Count', title='Hourly Alert Count (Last 24 Hours - Filtered)')
                st.plotly_chart(fig_bar_hourly, use_container_width=True)
            else:
                st.info("Not enough recent data (within filtered range) to display hourly trends.")
    else:
        st.warning("No alerts found matching the applied filters for statistics and trends.")

    st.markdown("---")
    st.subheader("📜 Recent Alerts Log (Filtered Data)")
    alert_container = st.container(height=600, border=True)
    with alert_container:
        if not filtered_df_alerts.empty:
            # Iterate through the filtered DataFrame to display alerts
            for index, alert in filtered_df_alerts.iterrows():
                status_emoji = "🔴" 
                date_obj = alert['timestamp_dt'] # Use the datetime object directly
                formatted_timestamp = date_obj.strftime("%d/%m/%Y %H:%M:%S")

                expander_title_html = (
                    f"{status_emoji} **{alert['alert_type']}** "
                    f"(Time: {formatted_timestamp})"
                )
                with st.expander(expander_title_html, expanded=False):
                    st.json(alert['details'])
        else:
            st.info("No alerts found matching the applied filters.")


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

# --- Simulate Drift Detection (Optional: Add this back if you want to generate alerts from the UI) ---
# def simulate_drift_detection_and_log_alert():
#     st.subheader("Generate New Alerts")
#     if st.button("Mô phỏng Drift Detection (Tạo Alert Mới)"):
#         fail_infor = {
#             "error_type": "Data Drift",
#             "details": "Phân phối cột 'customer_age' đã thay đổi đáng kể.",
#             "impact": "High",
#             "threshold_breaches": ["customer_age (PSI > 0.2)", "transaction_amount (JS Div > 0.1)"]
#         }
#         log_alert_event("Drift Detected", fail_infor)
#         st.success("New 'Drift Detected' alert logged!")
#         # You might want to simulate email/curl actions here too
#         # send_drift_notification_email(my_email, my_password, recipient_email, fail_infor)
#         # curl("train", clean_infra='false', provision_infra='true', token=github_token)
#         st.session_state.alerts_updated = True # Trigger dashboard refresh

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
            # If you want to keep the alert generation button visible, uncomment this:
            # st.markdown("---")
            # simulate_drift_detection_and_log_alert()
        elif menu == "🔓 Logout":
            st.session_state["logged_in"] = False
            st.success("Logged out successfully.")
            st.rerun()

if __name__ == "__main__":
    # Create the 'alert' directory if it doesn't exist
    os.makedirs(os.path.dirname(ALERTS_LOG_FILE), exist_ok=True)
    main()