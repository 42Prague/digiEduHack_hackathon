from srcs.dq.handlers.text_handlers.abstract_text_handler import AbstractTextHandler


class TxtTextHandler(AbstractTextHandler):
    def handle(self, file_path: str) -> str:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            raise RuntimeError(f"Text extraction failed: {file_path}, error: {e}")
