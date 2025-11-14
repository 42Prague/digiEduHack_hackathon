import pdfplumber
import mammoth
import markdown
from bs4 import BeautifulSoup


def convert_to_text(input_path):
    """
    Converts PDF, DOCX, or MD into a single string.
    Returns the extracted plain text.
    """
    ext = input_path.lower().split(".")[-1]
    text = ""

    # PDF → Text
    if ext == "pdf":
        with pdfplumber.open(input_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
                text += "\n"

    # DOCX → Text (Mammoth)
    elif ext == "docx":
        with open(input_path, "rb") as f:
            result = mammoth.extract_raw_text(f)
            text = result.value

    # MD → Text
    elif ext == "md":
        with open(input_path, "r", encoding="utf-8") as f:
            md = f.read()

        # Convert markdown → HTML → plain text
        html = markdown.markdown(md)
        text = BeautifulSoup(html, "html.parser").get_text()

    else:
        raise ValueError("Unsupported file type. Use PDF, DOCX, or MD.")

    return text
