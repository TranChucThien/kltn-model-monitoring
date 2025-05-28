import streamlit as st
import os

st.title("📊 Dashboard Tổng hợp")

base_dir = "reports"
dashboard_types = sorted([name for name in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, name))])

dashboard_tabs = st.tabs(dashboard_types)

for dash_tab, dash_type in zip(dashboard_tabs, dashboard_types):
    with dash_tab:
        report_path = os.path.join(base_dir, dash_type)
        report_files = sorted([f for f in os.listdir(report_path) if f.endswith(".html")], reverse=True)
        sub_tab_names = [os.path.splitext(f)[0] for f in report_files]

        if not report_files:
            st.warning("Không có báo cáo nào.")
        else:
            sub_tabs = st.tabs(sub_tab_names)
            for sub_tab, report_file in zip(sub_tabs, report_files):
                with sub_tab:
                    with open(os.path.join(report_path, report_file), "r", encoding="utf-8") as f:
                        html_content = f.read()
                    st.components.v1.html(html_content, height=1000,  width=1200, scrolling=True)
