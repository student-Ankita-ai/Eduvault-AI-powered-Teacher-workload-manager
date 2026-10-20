import sys
import os


# Add root directory to python path dynamically
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

import streamlit as st
import pandas as pd
import requests
from utils.ocr_masking import process_and_mask_document
from utils.voice_parser import parse_teacher_voice_command
from utils.tinyfish_sync import execute_tinyfish_portal_automation

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="EduVault AI | Full-Stack Government Teacher Portal",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    .stApp { background-color: #F8FAFC; font-family: 'Segoe UI', sans-serif; color: #1E293B; }
    .gov-top-bar { background: linear-gradient(90deg, #FF9933 0%, #FFFFFF 50%, #128807 100%); height: 5px; width: 100%; }
    .niti-header { background-color: #0A2540; color: white; padding: 16px 24px; display: flex; justify-content: space-between; align-items: center; border-radius: 6px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
    div[data-testid="stMetric"] { background-color: #FFFFFF; border-top: 4px solid #0A2540; border-radius: 8px; padding: 18px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
    div.stButton > button:first-child { background-color: #0A2540; color: #FFFFFF; border-radius: 6px; border: none; padding: 12px 24px; font-weight: 600; }
    div.stButton > button:first-child:hover { background-color: #FF9933; color: #0A2540; }
    .gov-ticker { background-color: #E2E8F0; border-left: 5px solid #FF9933; padding: 12px 18px; border-radius: 4px; margin-bottom: 15px; color: #0F172A; }
    div.stRadio > div { background-color: #0D233A; padding: 8px 15px; border-radius: 4px; display: flex; gap: 15px; align-items: center; }
    div.stRadio > div label { color: #FFFFFF !important; font-weight: 600 !important; }
    section[data-testid="stSidebar"] { display: none; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="gov-top-bar"></div>', unsafe_allow_html=True)
st.markdown("""
    <div class="niti-header">
        <div style="display: flex; align-items: center; gap: 15px;">
            <div style="background-color: #FF9933; padding: 10px; border-radius: 8px; font-size: 24px;">🎓</div>
            <div>
                <h2 style="margin:0; color:#FFFFFF; font-size: 22px; font-weight:700;">EDUVAULT AI — NATIONAL TEACHER WORKLOAD PORTAL</h2>
            </div>
        </div>
        <div style="text-align: right; font-size: 13px; color: #E2E8F0; background: rgba(255,255,255,0.1); padding: 8px 14px; border-radius: 6px;">
            <span>👤 <b>Sunita Sharma (TGT)</b></span><br>
            <span>🏫 <b>Class: 7th-A (Connected to SQLite DB)</b></span>
        </div>
    </div>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="gov-ticker">
        📢 <b>System Status:</b> Connected to FastAPI backend with real-time database synchronization for Academic Session 2026-27.
    </div>
""", unsafe_allow_html=True)

selected_tab = st.radio(
    "Navigation Menu",
    ["🏠 Home Dashboard", "🎙️ Voice AI Assistant", "📂 Vault & PII Masking", "⚡ Portal Direct-Sync (TinyFish)"],
    horizontal=True,
    label_visibility="collapsed"
)
st.divider()

try:
    res = requests.get(f"{API_URL}/students")
    students_df = pd.DataFrame(res.json()) if res.status_code == 200 else pd.DataFrame()
except:
    st.error("⚠️ Could not connect to FastAPI backend server. Please start backend using uvicorn.")
    students_df = pd.DataFrame()

if selected_tab == "🏠 Home Dashboard":
    st.markdown("### Grade 7th-A — Real Database Compliance Directory")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Enrolled Students", len(students_df) if not students_df.empty else 5, "Class 7A")
    c2.metric("Verified Profiles", len(students_df[students_df["overall_status"] == "🟢 Fully Verified"]) if not students_df.empty else 2)
    c3.metric("Action Required", len(students_df[students_df["overall_status"] != "🟢 Fully Verified"]) if not students_df.empty else 3)
    c4.metric("Active Gateway", "FastAPI + DB", "Live")
    
    st.divider()
    if not students_df.empty:
        st.dataframe(students_df[["roll_no", "name", "aadhaar_status", "bank_details", "income_cert", "overall_status", "pending_item"]], use_container_width=True)

elif selected_tab == "🎙️ Voice AI Assistant":
    st.markdown("### 🎙️ Voice-to-Action NLP Database Parser")
    voice_input = st.text_area("Simulated Voice Command:", "Rahul Kumar ne income certificate jama kar diya hai.")
    if st.button("⚡ Process and Update Database"):
        parsed = parse_teacher_voice_command(voice_input)
        update_res = requests.put(f"{API_URL}/students/{parsed['roll_no']}/verify-document?doc_type={parsed['doc_type']}")
        if update_res.status_code == 200:
            st.success(f"✅ Real Database updated for {parsed['entity']}!")
            st.json(update_res.json())

elif selected_tab == "📂 Vault & PII Masking":
    st.markdown("### 🔒 OCR & Automated PII Obfuscation Vault")
    file = st.file_uploader("Upload Student Document Scan (JPG/PNG)", type=["jpg", "png", "jpeg"])
    if file:
        col1, col2 = st.columns(2)
        with col1:
            st.image(file, caption="Original Document", use_container_width=True)
        with col2:
            masked_img = process_and_mask_document(file)
            st.image(masked_img, caption="Secured & PII Masked Version", use_container_width=True)
            st.success("🔒 Automatically redacted as per UIDAI guidelines.")

elif selected_tab == "⚡ Portal Direct-Sync (TinyFish)":
    st.markdown("### ⚡ TinyFish Autonomous Browser Agent Sync")
    portal = st.selectbox("Target Portal:", ["National Scholarship Portal (NSP)", "UDISE+ Portal"])
    if st.button("🚀 Execute Direct Portal Batch Submission"):
        with st.spinner("Running TinyFish headless agent..."):
            result = execute_tinyfish_portal_automation(portal, students_df.to_dict('records') if not students_df.empty else [])
        for log in result["logs"]:
            st.code(log)
        st.success(f"🎉 Batch submission complete! Receipt Token: `{result['receipt_token']}`")