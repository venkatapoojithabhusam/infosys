import streamlit as st
import requests
import PyPDF2
from io import BytesIO
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configuration for APIs
REGULATORY_API_URL = "https://console.groq.com/keys"  # Replace with your Regulatory API URL
REGULATORY_API_KEY = "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"  # Replace with your API key
RISK_ANALYSIS_API_URL = "https://console.groq.com/keys"  # Replace with your Risk Analysis API URL
RISK_ANALYSIS_API_KEY = "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"  # Replace with your API key

# Email Configuration
SMTP_SERVER = "smtp.gmail.com"  # Replace with your SMTP server
SMTP_PORT = 587  # Replace with your SMTP port
EMAIL_ADDRESS = "your_email@gmail.com"  # Replace with your email address
EMAIL_PASSWORD = "your_password"  # Replace with your email password

def fetch_real_time_updates():
    """
    Function to fetch real-time regulatory updates.
    """
    headers = {
        "Authorization": f"Bearer {REGULATORY_API_KEY}",
        "Content-Type": "application/json",
    }
    try:
        response = requests.get(REGULATORY_API_URL, headers=headers)
        response.raise_for_status()
        return response.json()  # Returns a list of regulatory updates
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching regulatory updates: {e}")
        return []

def analyze_risks(text, regulations):
    """
    Function to cross-verify clauses against regulatory updates.
    """
    headers = {
        "Authorization": f"Bearer {RISK_ANALYSIS_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "text": text,
        "regulations": regulations,
    }
    try:
        response = requests.post(RISK_ANALYSIS_API_URL, json=data, headers=headers)
        response.raise_for_status()
        return response.json()  # Returns risk analysis details
    except requests.exceptions.RequestException as e:
        st.error(f"Error analyzing risks: {e}")
        return {}

def detect_hidden_obligations(text):
    """
    Algorithm to detect hidden obligations or dependencies in text.
    """
    hidden_obligations = []
    keywords = ["must", "required to", "obligated to", "shall", "responsible for"]
    for keyword in keywords:
        if keyword in text.lower():
            hidden_obligations.append(keyword)
    return hidden_obligations

def track_changes_in_regulations(regulations, contracts):
    """
    Tracker that monitors regulatory changes and applies them to relevant contracts.
    """
    flagged_contracts = []
    for contract in contracts:
        for regulation in regulations:
            if regulation["title"] in contract:
                flagged_contracts.append({"contract": contract, "regulation": regulation})
    return flagged_contracts

def extract_text_from_pdf(uploaded_file):
    """
    Function to extract text from a PDF file.
    """
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
    """
    Function to send an email with the provided details.
    """
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = recipient_email
        msg["Subject"] = subject

        # Add body
        msg.attach(MIMEText(body, "plain"))

        # Connect to the server and send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        st.success(f"Email sent to {recipient_email} successfully!")
    except Exception as e:
        st.error(f"Failed to send email: {e}")

# Streamlit app
st.title("Risk Detection & Regulatory Tracker")

# File upload
uploaded_file = st.file_uploader("Upload a document (PDF or Text file)", type=["txt", "pdf"])

if uploaded_file is not None:
    # Check file type
    if uploaded_file.type == "application/pdf":
        # Extract text from PDF
        text = extract_text_from_pdf(uploaded_file)
    else:
        # Read the uploaded text file
        text = uploaded_file.read().decode("utf-8")

    if text:
        # Display the uploaded text or extracted text
        st.subheader("Uploaded Document:")
        st.write(text[:1000] + "...")  # Show the first 1000 characters of the document for preview

        # Fetch real-time updates
        st.subheader("Real-Time Regulatory Updates:")
        regulations = fetch_real_time_updates()
        if regulations:
            st.write(f"Fetched {len(regulations)} regulatory updates.")
        else:
            st.warning("No regulatory updates available or error occurred.")

        # Analyze risks
        if st.button("Analyze Risks"):
            with st.spinner("Analyzing risks..."):
                risk_details = analyze_risks(text, regulations)
                hidden_obligations = detect_hidden_obligations(text)

            if risk_details or hidden_obligations:
                st.success("Risk analysis complete!")
                st.subheader("Detected Risks:")
                st.json(risk_details)  # Display risks in a structured format

                st.subheader("Hidden Obligations/Dependencies:")
                if hidden_obligations:
                    st.write(hidden_obligations)
                else:
                    st.write("No hidden obligations detected.")

                # Input email after analysis
                recipient_email = st.text_input("Enter your email to receive the results:")
                if recipient_email and st.button("Send Email"):
                    email_body = (
                        f"Risk Analysis Results:\n{json.dumps(risk_details, indent=2)}\n\n"
                        f"Hidden Obligations/Dependencies:\n{hidden_obligations}\n\n"
                        f"Regulation Tracking:\n{json.dumps(flagged_contracts, indent=2)}"
                    )
                    send_email(recipient_email, "Risk Detection & Regulatory Tracker Results", email_body)
                elif not recipient_email:
                    st.warning("Please enter a valid email address.")

            else:
                st.warning("No risks detected or error occurred.")

        # Track changes in regulations
        st.subheader("Regulation Tracking:")
        contracts = [text]  # Example: List of uploaded contracts
        flagged_contracts = track_changes_in_regulations(regulations, contracts)
        if flagged_contracts:
            st.write("Contracts flagged for regulatory changes:")
            st.json(flagged_contracts)
        else:
            st.write("No contracts flagged for regulatory changes.")

    else:
        st.error("Unable to extract any text from the document.")
else:
    st.info("Please upload a document to proceed.")
