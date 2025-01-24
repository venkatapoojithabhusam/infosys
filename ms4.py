import streamlit 
import requests
import PyPDF2
from io import BytesIO
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

# Configuration for APIs
REGULATORY_API_URL = "https://console.groq.com/keys"  # Replace with your Regulatory API URL
REGULATORY_API_KEY = "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"  # Replace with your API key
RISK_ANALYSIS_API_URL = "https://console.groq.com/keys"  # Replace with your Risk Analysis API URL
RISK_ANALYSIS_API_KEY = "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"  # Replace with your API key

# Email Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "your_email@gmail.com"  # Replace with your email address
EMAIL_PASSWORD = "your_password"  # Replace with your email password

# Google Sheets Configuration
SCOPES = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
GOOGLE_SHEET_CREDENTIALS_FILE = "google_sheets_credentials.json"  # Replace with your credentials file
GOOGLE_SHEET_NAME = "DocumentTracking"

def initialize_google_sheets():
    """
    Initialize Google Sheets API client.
    """
    creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_SHEET_CREDENTIALS_FILE, SCOPES)
    client = gspread.authorize(creds)
    return client.open(GOOGLE_SHEET_NAME).sheet1

def log_to_google_sheets(sheet, document_name, risk_summary, flagged_changes, email_sent):
    """
    Log details of the document analysis to Google Sheets.
    """
    sheet.append_row([document_name, json.dumps(risk_summary), json.dumps(flagged_changes), email_sent])

def fetch_real_time_updates():
    headers = {"Authorization": f"Bearer {REGULATORY_API_KEY}", "Content-Type": "application/json"}
    try:
        response = requests.get(REGULATORY_API_URL, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching regulatory updates: {e}")
        return []

def analyze_risks(text, regulations):
    headers = {"Authorization": f"Bearer {RISK_ANALYSIS_API_KEY}", "Content-Type": "application/json"}
    data = {"text": text, "regulations": regulations}
    try:
        response = requests.post(RISK_ANALYSIS_API_URL, json=data, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error analyzing risks: {e}")
        return {}

def detect_hidden_obligations(text):
    hidden_obligations = []
    keywords = ["must", "required to", "obligated to", "shall", "responsible for"]
    for keyword in keywords:
        if keyword in text.lower():
            hidden_obligations.append(keyword)
    return hidden_obligations

def track_changes_in_regulations(regulations, contracts):
    flagged_contracts = []
    for contract in contracts:
        for regulation in regulations:
            if regulation["title"] in contract:
                flagged_contracts.append({"contract": contract, "regulation": regulation})
    return flagged_contracts

def extract_text_from_pdf(uploaded_file):
    try:
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return ""

def send_email(recipient_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = recipient_email
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        st.success(f"Email sent to {recipient_email} successfully!")
    except Exception as e:
        st.error(f"Failed to send email: {e}")

def plot_summary(risk_details, hidden_obligations):
    """
    Visualize risk details and hidden obligations using matplotlib and seaborn.
    """
    fig, ax = plt.subplots(1, 2, figsize=(15, 5))

    # Risk details pie chart
    risk_types = [item["risk_type"] for item in risk_details]
    risk_counts = pd.Series(risk_types).value_counts()
    ax[0].pie(risk_counts, labels=risk_counts.index, autopct='%1.1f%%', startangle=90)
    ax[0].set_title("Risk Distribution")

    # Hidden obligations bar chart
    obligations_counts = pd.Series(hidden_obligations).value_counts()
    sns.barplot(x=obligations_counts.index, y=obligations_counts.values, ax=ax[1])
    ax[1].set_title("Hidden Obligations")
    ax[1].set_ylabel("Frequency")

    st.pyplot(fig)

# Streamlit app
st.title("Risk Detection & Regulatory Tracker")

uploaded_file = st.file_uploader("Upload a document (PDF or Text file)", type=["txt", "pdf"])
google_sheet = initialize_google_sheets()

if uploaded_file:
    document_name = uploaded_file.name
    text = extract_text_from_pdf(uploaded_file) if uploaded_file.type == "application/pdf" else uploaded_file.read().decode("utf-8")

    if text:
        st.subheader("Uploaded Document Preview:")
        st.write(text[:1000] + "...")

        st.subheader("Real-Time Regulatory Updates:")
        regulations = fetch_real_time_updates()
        st.write(f"Fetched {len(regulations)} updates." if regulations else "No updates available.")

        if st.button("Analyze Risks"):
            with st.spinner("Analyzing..."):
                risk_details = analyze_risks(text, regulations)
                hidden_obligations = detect_hidden_obligations(text)

            plot_summary(risk_details, hidden_obligations)

            flagged_contracts = track_changes_in_regulations(regulations, [text])
            st.subheader("Flagged Changes in Regulations:")
            st.json(flagged_contracts if flagged_contracts else "No changes flagged.")

            recipient_email = st.text_input("Email to receive analysis:")
            if st.button("Send Email") and recipient_email:
                body = f"Risk Details:\n{json.dumps(risk_details)}\n\nHidden Obligations:\n{hidden_obligations}"
                send_email(recipient_email, f"Analysis Results for {document_name}", body)

            log_to_google_sheets(google_sheet, document_name, risk_details, flagged_contracts, "Yes" if recipient_email else "No")
