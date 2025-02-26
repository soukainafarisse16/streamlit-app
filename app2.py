import os
import re
import streamlit as st
import pandas as pd
import pytesseract
from io import BytesIO
from pdf2image import convert_from_bytes
from pytesseract import image_to_string
import openai  

openai.api_key = os.getenv("OPENAI_API_KEY")



# Set up Streamlit app
st.set_page_config(page_title="PDF to Excel Converter", page_icon="📄", layout="wide")
st.title("📄 AI-Powered PDF to Excel Extractor & Email Generator")

# Ensure Tesseract is set up (Only for Windows users)
if os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Function to extract text from PDF
POPPLER_PATH = r"C:\Users\sfarisse\poppler-24.08.0-0\poppler-24.08.0\Library\bin"
def extract_text_from_pdf(pdf_file):
    pages = convert_from_bytes(pdf_file.read(), poppler_path=POPPLER_PATH)
    #pages = convert_from_bytes(pdf_file.read())
    text = ""
    for i, page in enumerate(pages):
        page_text = image_to_string(page)
        text += f"--- Page {i+1} ---\n" + page_text + "\n"
    return text

# Function to parse extracted text
def parse_candidates(ocr_text):
    candidates = []
    pattern = re.compile(
        r"(?P<name>[A-Z][a-z]+(?:\s[A-Z][a-z]+)*)\s-\s\d+°\n"
        r"(?P<title>.*?)\n\n"
        r"(?P<location>.*?)(?:\s-\s(?P<industry>.*?))\n\n"
        r"(?P<company_line>.*?)\n?\n"
    )
    for match in pattern.finditer(ocr_text):
        candidate = match.groupdict()
        company_line = candidate.get('company_line', '')

        # Extract the company name from the company line
        company_match = re.search(r"(?:presso|for|at)\s(.*?)(?:\s\d{4}|$)", company_line)
        if company_match:
            candidate["company"] = company_match.group(1).strip()
        else:
            candidate["company"] = "Not Available"
        
        candidates.append(candidate)
        del candidate['company_line']
    return candidates

# Function to generate AI-powered insights
def generate_chatgpt_insight(name, title, company, location, industry):
    prompt = f"""
    Candidate Name: {name}
    Job Title: {title}
    Company: {company}
    Location: {location}
    Industry: {industry}

    Provide a brief AI-generated insight about this candidate based on the given data.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "You are an AI assistant providing candidate insights."},
                      {"role": "user", "content": prompt}],
            max_tokens=50
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return "AI Insight Unavailable"

# Function to generate a customized email
def generate_email(name, email):
    email_template = f"""
    <p>Buongiorno {name},</p>

    <p>Sono Riccardo Funicella, Business Manager della Divisione Engineering di ALTEN Italia.</p>

    <p>Alten è una società di consulenza che offre un'ampia varietà di servizi nel mondo Ingegneristico e Tecnologico. Allego di seguito la presentazione dei servizi nel quale potrà trovare la nostra Value Proposition che comprende servizi di:</p>

    <ul>
        <li>R&D, Production and Maintenance</li>
        <li>Regulatory and Quality</li>
        <li>Engineering and Project Management</li>
    </ul>

    <p>Ad oggi collaboriamo con diverse realtà sia in Italia che a livello globale, tuttavia stiamo provando ad ampliare le collaborazioni con le principali aziende presenti in Italia.</p>

    <p>A questo proposito, le propongo alcune date per fissare un incontro:</p>

    <ul>
        <li>-----</li>
        <li>-----</li>
        <li>------</li>
    </ul>

    <p>In attesa di un gentile riscontro, le lascio i miei riferimenti in firma.</p>

    <p>Grazie mille,</p>
    """
    return email_template.strip()


# Sidebar for PDF upload
st.sidebar.title("📂 Upload PDF File")
uploaded_file = st.sidebar.file_uploader("Choose a PDF", type=["pdf"])

if uploaded_file:
    with st.spinner("⏳ Processing your file... Please wait."):

        # Extract text from PDF
        extracted_text = extract_text_from_pdf(uploaded_file)

        # Debugging: Show extracted text
        st.text_area("Extracted Text (Preview)", extracted_text[:2000], height=200)

        # Parse extracted text
        parsed_data = parse_candidates(extracted_text)

    if parsed_data:
        df = pd.DataFrame(parsed_data)

        # Ensure all required columns exist
        required_columns = ["name", "title", "company", "location", "industry"]
    

       
        df["Email"] = ""  

        # Add AI-generated insights
        df["ChatGPT Insights"] = df.apply(lambda row: generate_chatgpt_insight(
            row["name"], row["title"], row["company"], row["location"], row["industry"]
        ), axis=1)

        
        df["Generated Email"] = df.apply(lambda row: generate_email(row["name"], row["Email"]), axis=1)

        # Show extracted data with AI insights and email
        st.success(f"✅ Extraction complete! Found {len(parsed_data)} candidates.")
        st.dataframe(df)

        # Save Excel file
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False)
            writer.close()

        # Provide download button
        st.download_button(
            label="📥 Download Excel File",
            data=output.getvalue(),
            file_name="candidates_with_emails.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    else:
        st.error("⚠️ No candidates found. Try another file.")
