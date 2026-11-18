import pdfplumber
from docx import Document


def extract_resume_text(file_path):

    # PDF
    if file_path.lower().endswith(".pdf"):
        text = ""

        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""

        return text

    # DOCX
    elif file_path.lower().endswith(".docx"):

        doc = Document(file_path)

        text = "\n".join(
            paragraph.text
            for paragraph in doc.paragraphs
        )

        return text

    else:
        raise ValueError(
            f"Unsupported file format: {file_path}"
        )