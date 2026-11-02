import streamlit as st
import streamlit.components.v1 as components
import sqlite3
import pandas as pd
import subprocess
import os

st.set_page_config(page_title="Contractor Payroll Dashboard", layout="wide")

st.title("Contractor Payroll & Performance")

# ==========================================
# SIDEBAR: PIPELINE CONTROLS
# ==========================================
st.sidebar.header("Admin Controls")
st.sidebar.write("Run the pipeline to generate fresh data and update the database.")

if st.sidebar.button("Run Full Data Pipeline"):
    # Step 1: Generate Raw Data
    with st.spinner("Generating raw data..."):
        subprocess.run(["python3", "01_generate_raw_data.py"], check=True)
    
    # Step 2: Process SQL & Exports
    with st.spinner("Processing SQL & Exports..."):
        subprocess.run(["python3", "02_run_pipeline.py"], check=True)
        
    # Step 3: Run Tests
    with st.spinner("Running Warehouse Checks..."):
        test_result = subprocess.run(["python", "03_run_tests.py"], capture_output=True, text=True)
        if "FAILED" in test_result.stdout:
            st.sidebar.error("Tests failed! Check logs.")
        else:
            st.sidebar.success("Pipeline complete and tests passed!")

# ==========================================
# MAIN PAGE: NATIVE STREAMLIT DATA VIEWS
# ==========================================
st.subheader("Data Warehouse Overview")

db_path = "data/contractorpay.db"

if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Audit Exceptions (Flagged Timesheets)**")
            df_audit = pd.read_sql_query("SELECT * FROM fact_audit_exceptions", conn)
            st.dataframe(df_audit, use_container_width=True)
            
        with col2:
            st.write("**Executive KPI Summary**")
            df_kpi = pd.read_sql_query("SELECT * FROM v_executive_kpi_summary", conn)
            st.dataframe(df_kpi, use_container_width=True)
            
        conn.close()
    except Exception as e:
        st.error(f"Error reading database: {e}")
else:
    st.info("Database not found. Please click 'Run Full Data Pipeline' in the sidebar to generate data.")

st.divider()

# ==========================================
# TABLEAU EMBED
# ==========================================
st.subheader("Tableau Visualizations")

# Replace these with your actual published Tableau URLs
tableau_url_1 = "https://public.tableau.com/views/ExecutiveKPIAgencyPerformanceSummary/ExecutiveKPIAgencyPerformanceSummary?:language=en-GB&publish=yes&:sid=&:redirect=auth&:display_count=n&:origin=viz_share_link"
tableau_url_2 = "https://public.tableau.com/views/OperationalComplianceExceptions/OperationalComplianceExceptionsSummary?:language=en-GB&publish=yes&:sid=&:redirect=auth&:display_count=n&:origin=viz_share_link"

# Create tabs for the two dashboards
tab1, tab2 = st.tabs(["Agency Performance", "Contractor Overview"])

with tab1:
    components.html(f'''
        <iframe src="{tableau_url_1}" 
        width="100%" 
        height="800" 
        frameborder="0"></iframe>
    ''', height=800)

with tab2:
    components.html(f'''
        <iframe src="{tableau_url_2}" 
        width="100%" 
        height="800" 
        frameborder="0"></iframe>
    ''', height=800)
