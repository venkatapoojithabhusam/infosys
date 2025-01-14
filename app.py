import streamlit as st
import requests
import PyPDF2
from io import BytesIO

# Define the Groq API configuration
GROQ_API_URL = "https://console.groq.com/playground"  # Replace with your Groq Web Server URL
GROQ_API_KEY = "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"  # Replace with your API key

def summarize_with_groq(text):
    """
    Function to send text to the Groq API for summarization.
    """
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {"text": text, "operation": "summarize"}

    try:
        response = requests.post(GROQ_API_URL, json=data, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors
        response_json = response.json()
        if "summary" in response_json:
            return response_json["summary"]
        else:
            return "API did not return a summary."
    except requests.exceptions.RequestException as e:
        return f"Error: {e}"

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

# Streamlit app
st.title("Document Summarizer")

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

        # Summarize button
        if st.button("Summarize"):
            # Call Groq API to summarize text
            with st.spinner("Summarizing using Groq API..."):
                summary = summarize_with_groq(text)
            if summary.startswith("Error:"):
                st.error(summary)
            else:
                st.success("Summarization complete!")
                
                # Display the summary
                st.subheader("Summary:")
                st.write(summary)
    else:
        st.error("Unable to extract any text from the document.")
