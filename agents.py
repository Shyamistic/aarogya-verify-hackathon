import re
import requests
import fitz  # PyMuPDF
import pytesseract
import cv2
import numpy as np
from crewai import Agent, Task, Crew, Process
# CORRECT
# CORRECT
from crewai.tools import BaseTool


# --- Tool 1: NPI Registry API Tool ---
class NPIAPI(BaseTool):
    name: str = "NPI Registry API"
    description: str = "A tool to look up provider data from the NPI registry using their NPI number."

    def _run(self, npi_number: str) -> dict:
        try:
            response = requests.get(f"http://127.0.0.1:5000/lookup/{npi_number}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "message": f"API call failed: {e}"}

# --- Tool 2: PDF License OCR Tool (Your Differentiator) ---
class PDFLicenseTool(BaseTool):
    name: str = "PDF License OCR Tool"
    description: str = "A tool to extract text from a scanned PDF provider license."

    def _run(self, pdf_path: str) -> dict:
        try:
            doc = fitz.open(pdf_path)
            full_text = ""
            for page in doc:
                # Render page to an image
                pix = page.get_pixmap(dpi=300)
                img_data = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
                
                # Convert to grayscale for better OCR
                gray_img = cv2.cvtColor(img_data, cv2.COLOR_BGR2GRAY)
                
                # Run Tesseract OCR
                text = pytesseract.image_to_string(gray_img)
                full_text += text
            
            doc.close()

            # Simple regex to find the license number
            license_match = re.search(r"License No: (\S+)", full_text, re.IGNORECASE)
            license_no = license_match.group(1) if license_match else None
            
            return {"status": "success", "full_text": full_text, "extracted_license": license_no}
        
        except Exception as e:
            return {"status": "error", "message": f"PDF processing failed: {e}"}


# --- Initialize Tools ---
npi_tool = NPIAPI()
pdf_tool = PDFLicenseTool()

# --- AGENT DEFINITIONS ---

# 1. DataValidation Agent
validation_agent = Agent(
    role='Data Validation Specialist',
    goal=f"Cross-reference provider data from the NPI registry using their NPI number.",
    backstory="You are a meticulous agent who queries external databases. Your job is to fetch the 'source of truth' data from the NPI registry.",
    tools=[npi_tool],
    verbose=True
)

# 2. InformationEnrichment Agent (Your Star Player)
enrichment_agent = Agent(
    role='Unstructured Data Analyst',
    goal=f"Extract key information from unstructured provider license PDFs.",
    backstory="You specialize in using OCR and AI to read scanned documents. Your job is to find the provider's license number from a PDF.",
    tools=[pdf_tool],
    verbose=True
)

# 3. QualityAssurance Agent
qa_agent = Agent(
    role='Quality Assurance Auditor',
    goal=(
        "Compare all data sources (Input CSV, NPI API, PDF), "
        "calculate a confidence score, and flag discrepancies."
    ),
    backstory=(
        "You are the final auditor. You receive data from all other agents. "
        "You must compare every field, create a final 'verified' profile, "
        "list all discrepancies, and provide a 'Confidence Score' for the data."
    ),
    verbose=True,
    allow_delegation=False
)


# --- TASK DEFINITIONS ---
# We will define tasks dynamically in the Streamlit app, as they depend on runtime data.