import pandas as pd
from srcs.dq.handlers.table_handlers.abstract_table_handler import AbstractTableHandler


class XLSXTableHandler(AbstractTableHandler):
    def handle(self, file_path: str) -> pd.DataFrame:
        try:
            df = pd.read_excel(file_path)
            return df
        except Exception as e:
            raise RuntimeError(f"XLSX extraction failed: {file_path}, error: {e}")
