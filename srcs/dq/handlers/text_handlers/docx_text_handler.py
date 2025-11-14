from docx import Document
from srcs.dq.handlers.text_handlers.abstract_text_handler import AbstractTextHandler


class DocxTextHandler(AbstractTextHandler):
    def handle(self, file_path: str) -> str:
        try:
            doc = Document(file_path)
            text = []
            for para in doc.paragraphs:
                text.append(para.text)
            return "\n".join(text)
        except Exception as e:
            raise RuntimeError(f"DOCX extraction failed: {file_path}, error: {e}")
