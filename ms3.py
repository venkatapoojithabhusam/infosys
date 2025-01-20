import streamlit as st
import requests
import PyPDF2
import json
from io import BytesIO
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr

# Configuration for APIs
REGULATORY_API_URL = "https://console.groq.com/keys"  # Replace with your API URL
REGULATORY_API_KEY = "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"  # Replace with your API key
SUMMARIZATION_API_URL = "https://console.groq.com/keys"  # Replace with your Summarization API URL
SUMMARIZATION_API_KEY = "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"  # Replace with your API key

# Email Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "your_email@gmail.com"
EMAIL_PASSWORD = "your_email_password"

def fetch_real_time_updates():
    """
    Fetches real-time regulatory updates from the configured API.
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

def summarize_text_in_chunks(text, chunk_size=1000):
    """
    Summarizes the document in chunks using the Summarization API.
    """
    headers = {
        "Authorization": f"Bearer {SUMMARIZATION_API_KEY}",
        "Content-Type": "application/json",
    }
    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
    summarized_chunks = []
    for idx, chunk in enumerate(chunks):
        try:
            response = requests.post(SUMMARIZATION_API_URL, json={"text": chunk}, headers=headers)
            response.raise_for_status()
            summary = response.json().get("summary", "").strip()
            if summary:
                summarized_chunks.append(summary)
            else:
                st.warning(f"Chunk {idx + 1}: No summary generated, skipping.")
        except requests.exceptions.RequestException as e:
            st.error(f"Error summarizing chunk {idx + 1}: {e}")
            summarized_chunks.append(f"[Error in chunk {idx + 1}]")
    return summarized_chunks if summarized_chunks else ["[Error: No summaries generated]"]

def extract_key_clauses(text, keywords):
    """
    Extracts key clauses from the document based on specific keywords.
    """
    key_clauses = []
    for keyword in keywords:
        if keyword.lower() in text.lower():
            key_clauses.append(keyword)
    return key_clauses

def extract_text_from_pdf(uploaded_file):
    """
    Extracts text from a PDF file.
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
    Sends an email with the given details.
    """
    if not body.strip():
        st.error("Email body is empty. Ensure valid summarization data before sending.")
        return

    try:
        msg = MIMEMultipart()
        msg["From"] = formataddr(("Risk Tracker", EMAIL_ADDRESS))
        msg["To"] = recipient_email
        msg["Subject"] = subject

        # Add body
        msg.attach(MIMEText(body, "plain"))

        # Connect to the SMTP server and send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        st.success(f"Email sent to {recipient_email} successfully!")
    except Exception as e:
        st.error(f"Failed to send email: {e}")

# Streamlit app
st.set_page_config(page_title="Risk & Regulatory Tracker", layout="wide")
st.title("📄 Risk Detection & Regulatory Tracker")

# Sidebar layout
with st.sidebar:
    st.header("Upload & Settings")
    uploaded_file = st.file_uploader("Upload a document (PDF or Text file)", type=["txt", "pdf"])
    recipient_email = st.text_input("Recipient Email", help="Enter the email to send the summarized report.")
    send_email_button = st.button("Send Email")

# Main layout
if uploaded_file is not None:
    # Extract text
    if uploaded_file.type == "application/pdf":
        text = extract_text_from_pdf(uploaded_file)
    else:
        text = uploaded_file.read().decode("utf-8")

    if text:
        # Document Preview
        st.subheader("Uploaded Document Preview:")
        st.write(text[:500] + "...")  # Show a snippet of the document

        # Summarization
        st.subheader("Document Summary:")
        with st.spinner("Summarizing document..."):
            summarized_chunks = summarize_text_in_chunks(text)
        for i, chunk in enumerate(summarized_chunks, 1):
            st.write(f"**Chunk {i}:** {chunk}")

        # Key Clauses Extraction
        st.subheader("Key Clauses:")
        keywords = ["must", "required to", "shall", "responsible for"]
        key_clauses = extract_key_clauses(text, keywords)
        if key_clauses:
            st.write(key_clauses)
        else:
            st.write("No key clauses found.")

        # Real-time Regulatory Updates
        st.subheader("Real-Time Regulatory Updates:")
        regulations = fetch_real_time_updates()
        if regulations:
            st.write(f"Fetched {len(regulations)} regulatory updates.")
            for update in regulations:
                st.write(f"- {update}")
        else:
            st.warning("No regulatory updates available or error occurred.")

        # Email functionality
        if send_email_button and recipient_email:
            email_body = (
                f"Document Summary:\n{''.join(summarized_chunks)}\n\n"
                f"Key Clauses:\n{', '.join(key_clauses) if key_clauses else 'No key clauses found.'}\n\n"
                f"Regulatory Updates:\n{json.dumps(regulations, indent=2) if regulations else 'No updates available.'}"
            )
            send_email(recipient_email, "Risk Detection & Regulatory Tracker Results", email_body)
        elif send_email_button:
            st.warning("Please enter a valid email address.")
    else:
        st.error("Unable to extract any text from the document.")
else:
    st.info("Please upload a document to proceed.")
