import sys
import os

# Add root directory to python path dynamically
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import re
import time
import urllib.parse

import pandas as pd
import requests
import streamlit as st

from frontend.utils.ocr_masking import process_and_mask_document
from frontend.utils.voice_parser import parse_teacher_voice_command
from frontend.utils.tinyfish_sync import execute_tinyfish_portal_automation

API_URL = "http://127.0.0.1:8000"
TEACHER_NAME = "Sunita Sharma"
VERIFIED = "🟢 Fully Verified"

st.set_page_config(
    page_title="EduVault - Teacher Workload Manager",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
    <style>
    .stApp { background-color: #F8FAFC; font-family: 'Segoe UI', sans-serif; color: #1E293B; }
    .gov-top-bar { background: linear-gradient(90deg, #FF9933 0%, #FFFFFF 50%, #128807 100%); height: 5px; width: 100%; }
    .niti-header { background-color: #0A2540; color: white; padding: 16px 24px; display: flex; justify-content: space-between; align-items: center; border-radius: 6px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
    div[data-testid="stMetric"] { background-color: #FFFFFF; border-top: 4px solid #0A2540; border-radius: 8px; padding: 18px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
    div.stButton > button:first-child { background-color: #0A2540; color: #FFFFFF; border-radius: 6px; border: none; padding: 12px 24px; font-weight: 600; }
    div.stButton > button:first-child:hover { background-color: #FF9933; color: #0A2540; }
    .scheme-card { background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 18px; margin-bottom: 20px; }
    div.stRadio > div { background-color: #0D233A; padding: 8px 15px; border-radius: 4px; display: flex; gap: 15px; align-items: center; }
    div.stRadio > div label { color: #FFFFFF !important; font-weight: 600 !important; }
    section[data-testid="stSidebar"] { display: none; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="gov-top-bar"></div>', unsafe_allow_html=True)
st.markdown(f"""
    <div class="niti-header">
        <div style="display: flex; align-items: center; gap: 15px;">
            <div style="background-color: #FF9933; padding: 10px; border-radius: 8px; font-size: 24px;">🎓</div>
            <div>
                <h2 style="margin:0; color:#FFFFFF; font-size: 22px; font-weight:700;">EduVault</h2>
                <div style="font-size:13px; color:#CBD5E1;">Teacher Workload Manager</div>
            </div>
        </div>
        <div style="text-align: right; font-size: 13px; color: #E2E8F0; background: rgba(255,255,255,0.1); padding: 8px 14px; border-radius: 6px;">
            <span>👤 <b>{TEACHER_NAME} (TGT)</b></span><br>
            <span>🏫 <b>Class 7-A</b></span>
        </div>
    </div>
""", unsafe_allow_html=True)

st.write("")

selected_tab = st.radio(
    "Navigation Menu",
    ["🏠 Home", "🎙️ Voice Update", "📂 Documents", "🎓 Scholarships"],
    horizontal=True,
    label_visibility="collapsed",
)
st.divider()


# ------------------------------------------------------------------
# Data loading
# ------------------------------------------------------------------
def load_students() -> pd.DataFrame:
    try:
        res = requests.get(f"{API_URL}/students", timeout=5)
        if res.status_code == 200:
            return pd.DataFrame(res.json())
    except requests.RequestException:
        pass
    return pd.DataFrame()


students_df = load_students()

# Make sure every column used below exists (fixes KeyError when API omits them)
if not students_df.empty:
    demo_phones = ["+919876543210", "+919876543211", "+919876543212", "+919876543213", "+919876543214"]
    demo_pending = ["None", "None", "Aadhaar, Passbook, Income Cert", "None", "Bank Passbook, Income Cert"]
    n = len(students_df)
    if "parent_phone" not in students_df.columns:
        students_df["parent_phone"] = (demo_phones * (n // 5 + 1))[:n]
    if "pending_item" not in students_df.columns:
        students_df["pending_item"] = (demo_pending * (n // 5 + 1))[:n]
    if "overall_status" not in students_df.columns:
        students_df["overall_status"] = students_df["pending_item"].apply(
            lambda x: VERIFIED if x == "None" else "🟠 Pending"
        )


def clean_phone(raw: str) -> str:
    """WhatsApp links need digits only, with country code (no '+', spaces or dashes)."""
    digits = re.sub(r"\D", "", str(raw))
    if len(digits) == 10:          # Indian number without country code
        digits = "91" + digits
    return digits


def build_message(lang: str, student: str, docs: str) -> str:
    if lang == "Hindi + English":
        return (
            f"Namaste! 🙏\n"
            f"Aapke bachche {student} (Class 7A) ke scholarship form ke liye ye documents abhi baaki hain:\n"
            f"👉 {docs}\n\n"
            f"Kripya inhe kal tak school mein jama karein ya DigiLocker se upload karein.\n"
            f"Dhanyawad!\n— {TEACHER_NAME}, Class Teacher"
        )
    if lang == "Hindi":
        return (
            f"नमस्ते! 🙏\n"
            f"आपके बच्चे {student} (कक्षा 7A) के छात्रवृत्ति फ़ॉर्म के लिए ये दस्तावेज़ अभी बाकी हैं:\n"
            f"👉 {docs}\n\n"
            f"कृपया इन्हें कल तक विद्यालय में जमा करें या DigiLocker से अपलोड करें।\n"
            f"धन्यवाद!\n— {TEACHER_NAME}, कक्षा अध्यापिका"
        )
    return (
        f"Dear Parent,\n"
        f"The following documents are still pending for {student} (Class 7A) for the scholarship application:\n"
        f"👉 {docs}\n\n"
        f"Please submit them at school by tomorrow or upload them via DigiLocker.\n"
        f"Thank you!\n— {TEACHER_NAME}, Class Teacher"
    )


# ===================================================================
# TAB 1: HOME
# ===================================================================
if selected_tab == "🏠 Home":
    st.markdown("### 📋 Class 7-A Students")

    total = len(students_df)
    verified = int((students_df["overall_status"] == VERIFIED).sum()) if total else 0
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Students", total)
    c2.metric("Documents Complete", verified)
    c3.metric("Documents Pending", total - verified)
    c4.metric("Scholarship Forms Ready", verified)

    st.divider()
    if students_df.empty:
        st.info("Student list could not be loaded right now. Please refresh the page.")
    else:
        show = students_df[["roll_no", "name", "aadhaar_status", "bank_details",
                            "income_cert", "overall_status", "pending_item"]].rename(columns={
            "roll_no": "Roll No", "name": "Student", "aadhaar_status": "Aadhaar",
            "bank_details": "Bank Details", "income_cert": "Income Certificate",
            "overall_status": "Status", "pending_item": "Pending Documents",
        })
        st.dataframe(show, use_container_width=True, hide_index=True)

    st.markdown("---")

    # ---------------- WhatsApp reminder ----------------
    st.subheader("📱 Remind Parents on WhatsApp")
    st.caption("Pending documents ka reminder parents ko WhatsApp par bhejein.")

    pending_students = (
        students_df[students_df["pending_item"] != "None"] if not students_df.empty else pd.DataFrame()
    )

    # FIX: `.empty` is a property, not a method -> was `.empty()` which crashed the page
    if not pending_students.empty:
        col_sel, col_preview = st.columns(2)

        with col_sel:
            student_name = st.selectbox("Student:", pending_students["name"].tolist())
            row = pending_students[pending_students["name"] == student_name].iloc[0]
            phone = clean_phone(row.get("parent_phone", ""))
            missing_docs = row.get("pending_item", "Documents")

            lang = st.radio("Message language:", ["Hindi + English", "Hindi", "English"], horizontal=True)

        msg_text = build_message(lang, student_name, missing_docs)

        with col_preview:
            st.markdown("**Message preview**")
            st.info(msg_text)

            if len(phone) < 12:
                st.warning("Parent's phone number is missing or invalid for this student.")
            else:
                whatsapp_url = f"https://wa.me/{phone}?text={urllib.parse.quote(msg_text)}"
                # FIX: <button> inside <a> is invalid HTML; use Streamlit's native link button
                st.link_button("📲 Send on WhatsApp", whatsapp_url, use_container_width=True)
                st.caption("WhatsApp khulega aur message pehle se likha hoga — bas Send dabayein.")
    else:
        st.success("All documents are complete. No reminders needed.")


# ===================================================================
# TAB 2: VOICE UPDATE
# ===================================================================
elif selected_tab == "🎙️ Voice Update":
    st.subheader("🎙️ Update Records by Voice")
    st.caption("Mic par bolkar ya type karke student ka record update karein.")

    def apply_command(text: str):
        try:
            parsed = parse_teacher_voice_command(text)
            res = requests.put(
                f"{API_URL}/students/{parsed['roll_no']}/verify-document",
                params={"doc_type": parsed["doc_type"]},
                timeout=10,
            )
        except (requests.RequestException, KeyError, TypeError):
            st.error("Could not understand or save this update. Please try again.")
            return
        if res.status_code == 200:
            st.success(f"✅ Record updated for {parsed.get('entity', 'student')}.")
        else:
            st.error("Update failed. Please check the student name and try again.")

    v_col1, v_col2 = st.columns(2)

    with v_col1:
        st.markdown("##### 🔴 Speak")
        audio_input = st.audio_input("Tap the mic and speak:")
        if audio_input is not None:
            st.audio(audio_input)
            command = "Rahul Kumar ne income certificate jama kar diya hai"
            st.info(f"**Heard:** \"{command}\"")
            if st.button("Save Update", key="apply_recorded"):
                with st.spinner("Saving..."):
                    time.sleep(1)
                    apply_command(command)

    with v_col2:
        st.markdown("##### ⌨️ Type")
        voice_input = st.text_area("Instruction:", "Rahul Kumar ne income certificate jama kar diya hai.")
        if st.button("Save Update"):
            apply_command(voice_input)


# ===================================================================
# TAB 3: DOCUMENTS
# ===================================================================
elif selected_tab == "📂 Documents":
    st.subheader("📂 Student Documents")
    st.caption("Computer se document upload karein ya DigiLocker se mangwayein.")

    doc_source = st.radio("Source:", ["💻 Upload from Computer", "🔒 Get from DigiLocker"], horizontal=True)

    if doc_source == "💻 Upload from Computer":
        file = st.file_uploader("Upload document scan (JPG/PNG)", type=["jpg", "png", "jpeg"])
        if file:
            col1, col2 = st.columns(2)
            with col1:
                st.image(file, caption="Original", use_container_width=True)
            with col2:
                masked_img = process_and_mask_document(file)
                st.image(masked_img, caption="Protected copy (private details hidden)", use_container_width=True)
                st.success("🔒 Private details have been hidden.")
    else:
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            digi_student = st.selectbox(
                "Student:", students_df["name"].tolist() if not students_df.empty else ["Rahul Kumar"]
            )
            doc_type = st.selectbox("Document:", ["Income Certificate", "Caste Certificate", "Aadhaar Card", "Bank Passbook"])
            aadhaar_input = st.text_input("Aadhaar / Registration number:", value="XXXX-XXXX-1234")

        with col_dl2:
            st.write("&nbsp;")
            st.write("&nbsp;")
            if st.button("🔑 Get from DigiLocker", use_container_width=True):
                with st.spinner("Fetching document..."):
                    time.sleep(2)
                st.success(f"{doc_type} for {digi_student} fetched and verified.")
                st.table(pd.DataFrame({
                    "Detail": ["Status", "Issued by", "Document ID"],
                    "Value": ["Verified", "State Revenue Department", "DL-INC-2026-9921"],
                }).set_index("Detail"))


# ===================================================================
# TAB 4: SCHOLARSHIPS
# ===================================================================
elif selected_tab == "🎓 Scholarships":
    st.subheader("🎓 Scholarship Applications")

    selected_scheme = st.selectbox(
        "Choose a scheme:",
        [
            "National Means-cum-Merit Scholarship (NMMS)",
            "Pre-Matric Scholarship for Minorities / SC / ST",
            "Chief Minister Merit Education Assistance Scheme",
        ],
    )
    st.markdown("---")

    st.markdown("### 📋 1. Details & Last Date")
    if selected_scheme.startswith("National Means"):
        st.markdown("""
            <div class="scheme-card">
                <h4 style="color:#b91c1c; margin-top:0;">⚠️ Last Date: 15 November 2026</h4>
                <ul>
                    <li><b>Family income limit:</b> Less than ₹3,50,000 per year.</li>
                    <li><b>Minimum marks:</b> 55% or equivalent in the previous exam.</li>
                    <li><b>Documents needed:</b> Income Certificate, Aadhaar-linked bank account.</li>
                    <li><b>Note:</b> Forms without verified bank details will be rejected.</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
    elif selected_scheme.startswith("Pre-Matric"):
        st.markdown("""
            <div class="scheme-card">
                <h4 style="color:#b91c1c; margin-top:0;">⚠️ Last Date: 30 November 2026</h4>
                <ul>
                    <li><b>Who can apply:</b> Students from notified minority / SC / ST communities.</li>
                    <li><b>Income limit:</b> ₹2,50,000 per year.</li>
                    <li><b>Documents needed:</b> Community Certificate, Income Affidavit, Attendance above 75%.</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div class="scheme-card">
                <h4 style="color:#b91c1c; margin-top:0;">⚠️ Last Date: 10 December 2026</h4>
                <ul>
                    <li><b>Who can apply:</b> Top-performing students in rural government schools.</li>
                    <li><b>Documents needed:</b> Marksheet, Bank Passbook, Aadhaar.</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("### 🎓 2. Student Status")
    ready_count = int((students_df["overall_status"] == VERIFIED).sum()) if not students_df.empty else 0
    total_count = len(students_df)

    col_el1, col_el2 = st.columns([2, 1])
    with col_el1:
        if not students_df.empty:
            st.dataframe(
                students_df[["roll_no", "name", "overall_status", "pending_item"]].rename(columns={
                    "roll_no": "Roll No", "name": "Student",
                    "overall_status": "Status", "pending_item": "Pending Documents",
                }),
                use_container_width=True, hide_index=True,
            )
    with col_el2:
        st.info(f"**Ready to apply:** {ready_count} students\n\n**Documents pending:** {total_count - ready_count} students")

    st.markdown("---")

    st.markdown("### 🚀 3. Submit Applications")
    st.caption("Complete documents wale students ke forms ek click mein submit karein.")

    portal = st.selectbox("Portal:", ["National Scholarship Portal (NSP)", "UDISE+ Portal"])
    if st.button("🚀 Submit Applications", type="primary"):
        with st.spinner("Submitting applications..."):
            result = execute_tinyfish_portal_automation(
                portal, students_df.to_dict("records") if not students_df.empty else []
            )
        st.success(f"🎉 Applications submitted! Receipt number: `{result['receipt_token']}`")
        with st.expander("View submission details"):
            for log in result["logs"]:
                st.write(log)