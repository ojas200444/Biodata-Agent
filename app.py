import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import base64
import time

# --- 1. CONFIGURATION ---
SHEET_ID = "1nUAV3pz38oaztATwLHIv0cYb5xHOvo5xrY9N2PHq5Rw"
GEMINI_API_KEY = "AIzaSyAaMLayWCGGxOuztzdjh6FX14muXY6H2uw"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzS1FYtwLNSDQEkgcLVud3-w9X1uYOrt22WZpKgMRCCXeJQ6uvY8EIrh0nw1bDeCgvc/exec"
DRIVE_FOLDER_ID = "1XD9v-Wyv_c5RrcQ3m0OmY76GcbONZ2H2"

# Setup Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# Setup Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).sheet1

# --- 2. THE UI ---
st.set_page_config(page_title="Biodata Agent", page_icon="💍")
st.title("💍 Biodata Agent")

# --- NEW: NAVIGATION BUTTONS ---
col1, col2 = st.columns(2)
with col1:
    # This button opens your Google Sheet
    sheet_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"
    st.link_button("📊 View Sheet", sheet_url, use_container_width=True)
with col2:
    # This button opens your Drive Folder
    drive_url = f"https://drive.google.com/drive/u/0/folders/{DRIVE_FOLDER_ID}"
    st.link_button("📁 View Uploads Folder", drive_url, use_container_width=True)

st.markdown("---")

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

            # B. UPLOAD TO DRIVE (Using your Apps Script)
            encoded_string = base64.b64encode(file_bytes).decode('utf-8')
            payload = {"base64": encoded_string, "mimeType": uploaded_file.type, "fileName": f"{name}_Bio"}
            drive_response = requests.post(SCRIPT_URL, json=payload)
            drive_link = drive_response.text

            # C. SAVE TO SHEET
            sheet.append_row(extracted_list[:18] + [drive_link])
            
            st.success(f"✅ Success! {name} has been added to the tracker.")
            st.balloons()

        except Exception as e:
            if "429" in str(e):
                st.error("Gemini is busy. Please wait 45 seconds and try again.")
            else:
                st.error(f"Error: {e}")

st.markdown("---")
st.caption("Tip: Your daily limit (RPD) resets every day at 12:30 PM IST.")