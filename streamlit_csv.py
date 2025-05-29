import streamlit as st
import pandas as pd
import os

# ---------- LOGIN ----------
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
        # Drag and drop file uploader
        uploaded_file = st.file_uploader("Drag and drop a CSV file here", type=["csv"])
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                selected_file_name = uploaded_file.name
                # File successfully loaded
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
        # Initialize filtered_df with the original df
        filtered_df = df.copy() 
        
        # Check and apply filter by 'label'
        if 'label' in df.columns:
            st.subheader("🔍 Filter by 'label'")
            label_values = df['label'].dropna().unique().tolist()
            selected_labels = st.multiselect(
                "Select label values to view", 
                options=label_values, 
                default=label_values # Select all by default
            )
            
            # Apply filter if labels are selected
            if selected_labels:
                filtered_df = df[df['label'].isin(selected_labels)]
            else:
                # If no label is selected, display the original DataFrame
                st.info("No labels selected, showing all data.")
                filtered_df = df.copy() # If none selected, show all
        elif 'Label' in df.columns:
            st.subheader("🔍 Filter by 'Label'")
            label_values = df['Label'].dropna().unique().tolist()
            selected_labels = st.multiselect(
                "Select Label values to view", 
                options=label_values, 
                default=label_values # Select all by default
            )
            
            # Apply filter if labels are selected
            if selected_labels:
                filtered_df = df[df['Label'].isin(selected_labels)]
            else:
                # If no label is selected, display the original DataFrame
                st.info("No Labels selected, showing all data.")
                filtered_df = df.copy() # If none selected, show all
        else:
            st.info("ℹ️ CSV file does not have a 'label' or 'Label' column. No label filter will be applied.")

        # st.subheader("📄 Data after filtering:")
        # # Check if filtered_df is not empty before displaying
        # if not filtered_df.empty:
        #     st.dataframe(filtered_df, use_container_width=True)
        # else:
        #     st.warning("No data matches the selected filter.")

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
        menu = st.sidebar.radio("📌 Menu", ["📊 Model Monitoring Reports", "📁 Validate Results", "🔓 Logout"])
        
        if menu == "📊 Model Monitoring Reports":
            show_dashboard()
        elif menu == "📁 Validate Results":
            csv_editor()
        elif menu == "🔓 Logout":
            st.session_state["logged_in"] = False
            st.success("Logged out successfully.")
            st.rerun()

if __name__ == "__main__":
    main()