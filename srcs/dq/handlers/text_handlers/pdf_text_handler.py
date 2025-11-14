from PyPDF2 import PdfReader
from srcs.dq.handlers.text_handlers.abstract_text_handler import AbstractTextHandler


class PDFTextHandler(AbstractTextHandler):
    def handle(self, file_path: str) -> str:
        try:
            reader = PdfReader(file_path)
            text = []
            for page in reader.pages:
                text.append(page.extract_text() or "")
            return "\n".join(text)
        except Exception as e:
            raise RuntimeError(f"PDF extraction failed: {file_path}, error: {e}")
