import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Pflegefachmann Dashboard", layout="wide")

st.title("🏥 Pflegefachmann Application Dashboard")
st.markdown("Monitor your automated application progress in real-time.")

CLINICS_FILE = "clinics.csv"
SENT_FILE = "applications_sent.csv"

# Load Data
def load_data():
    clinics_df = pd.DataFrame()
    sent_df = pd.DataFrame()
    
    if os.path.exists(CLINICS_FILE):
        try:
            clinics_df = pd.read_csv(CLINICS_FILE)
        except Exception:
            pass
            
    if os.path.exists(SENT_FILE):
        try:
            sent_df = pd.read_csv(SENT_FILE)
        except Exception:
            pass
            
    return clinics_df, sent_df

clinics_df, sent_df = load_data()

# Calculate Metrics
total_found = len(clinics_df) if not clinics_df.empty else 0
total_processed = len(sent_df) if not sent_df.empty else 0

total_sent = 0
total_failed = 0

if not sent_df.empty and "Status" in sent_df.columns:
    total_sent = len(sent_df[sent_df["Status"] == "Sent"])
    total_failed = len(sent_df[sent_df["Status"] == "Failed"])

remaining = total_found - total_sent - total_failed
if remaining < 0: remaining = 0

# Display Key Metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("🏥 Clinics Found", total_found)
col2.metric("✅ Successfully Sent", total_sent)
col3.metric("❌ Failed", total_failed)
col4.metric("⏳ Still Pending", remaining)

st.divider()

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📬 Application History")
    if not sent_df.empty:
        # Style the dataframe based on status
        def color_status(val):
            color = '#28a745' if val == 'Sent' else '#dc3545'
            return f'color: {color}; font-weight: bold;'
            
        st.dataframe(
            sent_df.sort_values(by="Date Sent", ascending=False).style.map(color_status, subset=['Status']),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No applications sent yet. Run the python script!")

with col_right:
    st.subheader("⏳ Still Pending")
    if not clinics_df.empty:
        if not sent_df.empty and "Email" in sent_df.columns:
            # Filter out already processed emails
            processed_emails = sent_df["Email"].tolist()
            pending_df = clinics_df[~clinics_df["Email"].isin(processed_emails)]
        else:
            pending_df = clinics_df
            
        if pending_df.empty:
            st.success("All found clinics have been emailed!")
        else:
            st.dataframe(pending_df, use_container_width=True, hide_index=True)
    else:
        st.warning("No clinics found yet. Run Phase 1 of the python script!")

# Sidebar Instructions
with st.sidebar:
    st.header("How to run:")
    st.markdown("""
    1. **Scrape Clinics:**
       Run `python pflegefachmann_bewerbung.py` to find new hospitals.
    2. **Review:**
       Open `clinics.csv` and remove bad emails.
    3. **Send:**
       Run `python pflegefachmann_bewerbung.py` again to start sending.
    4. **Monitor Refresh:**
       Just click the refresh button in your browser to see new emails pop up here!
    """)
