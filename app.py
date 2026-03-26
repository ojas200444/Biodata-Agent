import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import base64
import time

# --- 1. CONFIGURATION ---
SHEET_ID = st.secrets["SHEET_ID"]
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
SCRIPT_URL = st.secrets["SCRIPT_URL"]
DRIVE_FOLDER_ID = st.secrets["DRIVE_FOLDER_ID"]

# Setup Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

# Setup Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).sheet1

# --- 2. THE UI & MOBILE OPTIMIZATION ---
st.set_page_config(page_title="Biodata Agent", page_icon="💍", layout="centered")

# Custom CSS for Mobile Optimization
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        padding-right: 1rem;
        padding-left: 1rem;
    }
    .stButton > button {
        width: 100%;
        border-radius: 12px;
        height: 3.5em;
        font-weight: bold;
    }
    @media (max-width: 480px) {
        h1 {
            font-size: 1.5rem !important;
            text-align: center;
        }
    }
</style>
""", unsafe_allow_code=True)

st.title("💍 Biodata Agent")

# Navigation Buttons
col1, col2 = st.columns(2, gap="small")
with col1:
    sheet_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"
    st.link_button("📊 View Sheet", sheet_url, use_container_width=True)
with col2:
    drive_url = f"https://drive.google.com/drive/u/0/folders/{DRIVE_FOLDER_ID}"
    st.link_button("📁 View Drive", drive_url, use_container_width=True)

st.markdown("---")

# --- 3. UPLOADER LOGIC ---
uploaded_file = st.file_uploader("Upload Biodata (PDF or Image)", type=['pdf', 'jpg', 'png', 'jpeg'])

if uploaded_file:
    file_bytes = uploaded_file.getvalue()
    
    with st.spinner("AI is extracting details..."):
        prompt = "Extract 18 fields separated by |. Fields: Name|DOB|Time|Place|Height|Edu|Occ|Belongs|Lives|Father|Mother|Dada|Dadi|Siblings|S-Self|S-Mama|S-Dadi|S-Nani"
        
        try:
            # A. AI EXTRACTION
            response = model.generate_content([
                prompt, 
                {"mime_type": uploaded_file.type, "data": file_bytes}
            ])
            
            # Clean and parse
            raw_text = response.text.strip().replace('\n', ' ')
            extracted_list = [item.strip() for item in raw_text.split("|")]
            while len(extracted_list) < 18: extracted_list.append("-")
            
            name = extracted_list[0]

            # B. UPLOAD TO DRIVE
            encoded_string = base64.b64encode(file_bytes).decode('utf-8')
            payload = {"base64": encoded_string, "mimeType": uploaded_file.type, "fileName": f"{name}_Bio"}
            drive_response = requests.post(SCRIPT_URL, json=payload)
            drive_link = drive_response.text

            # C. SAVE TO SHEET
            sheet.append_row(extracted_list[:18] + [drive_link])
            
            st.success(f"✅ Success! {name} has been added.")
            st.balloons()

        except Exception as e:
            if "429" in str(e):
                st.error("Gemini is busy. Please wait 45 seconds.")
            else:
                st.error(f"Error: {e}")

st.markdown("---")
st.caption("Tip: Daily limit resets at 12:30 PM IST.")
