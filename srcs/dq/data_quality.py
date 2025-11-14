from srcs.dq.handlers.text_handlers.pdf_text_handler import PDFTextHandler
from srcs.dq.handlers.text_handlers.docx_text_handler import DocxTextHandler
from srcs.dq.handlers.text_handlers.txt_text_handler import TxtTextHandler

from srcs.dq.handlers.table_handlers.csv_table_handler import CSVTableHandler
from srcs.dq.handlers.table_handlers.xlsx_table_handler import XLSXTableHandler
from srcs.dq.handlers.table_handlers.json_table_handler import JSONTableHandler

from srcs.dq.handlers.audio_handlers.generic_audio_handler import GenericAudioHandler

from srcs.dq.wrapper import process_df

from srcs.dq.agent import call_agent, prompt
from srcs.dq.db_manager import MongoDBManager


class DataQualityProcessor:
    """
    Handles data quality pipeline: file type detection, transcription, summarization, table cleaning, mapping.
    Does NOT handle DB saving.
    """
    # Registry mapping file extensions to handler methods
    _audio_handlers = {
        '.wav': GenericAudioHandler,
        '.mp3': GenericAudioHandler,
        '.m4a': GenericAudioHandler,
    }
    _text_handlers = {
        '.pdf': PDFTextHandler,
        '.docx': DocxTextHandler,
        '.txt': TxtTextHandler,
        '.md': TxtTextHandler,
    }
    _table_handlers = {
        '.csv': CSVTableHandler,
        '.xlsx': XLSXTableHandler,
        '.json': JSONTableHandler,
    }

    def __init__(self):
        self.db_manager = MongoDBManager()
        self.result = {}

    def process(self, filename: str, metadata: dict) -> dict:
        """
        Parameters:
        - filename: Name of the file being processed.
        - metadata: Additional metadata about the file.
            - Region: str
            - School: str
            - Activity: str
            - Ingestion time: str
        """
        fname = filename.lower()
        self.result = {"filename": fname, "metadata": metadata}

        ext = f'.{fname.split('.')[-1]}'
        file_path = filename  # Assume filename is the full path

        try:
            # Audio
            if ext in self._audio_handlers:
                handler_cls = self._audio_handlers[ext]
                handler = handler_cls()
                summary = handler.handle(file_path)
                self.result["summary"] = summary
            # Text
            elif ext in self._text_handlers:
                handler_cls = self._text_handlers[ext]
                handler = handler_cls()
                text = handler.handle(file_path)
                summary = call_agent(prompt, text)
                # self.result["summary"] = self.summarize_text(text)
                self.result["summary"] = summary
            # Table
            elif ext in self._table_handlers:
                handler_cls = self._table_handlers[ext]
                handler = handler_cls()
                table_result = handler.handle(file_path)
                self.result["result_df"] = table_result

                # mapping
                mapped_df = process_df(self.result["result_df"])
                self.result["result_df"] = mapped_df
            # Unsupported => error
            else:
                self.result["error"] = "Unsupported file type"
                return self.result
        # if there was an error during handling
        except RuntimeError as re:
            self.result["error"] = str(re)
            return self.result
        
        # Apply cleaning and data quality check
        self.clean_data()
        self.data_quality_check()

        if "summary" in self.result:
            print("Saving summary to DB...")
            self.save_to_mongo(self.result)
            print("\n\n")
        elif "result_df" in self.result:
            print("Saving mapped table to DB...")
            self.save_to_mongo(self.result)
            print("\n\n")

    def clean_data(self):
        # Placeholder: implement data cleaning logic
        if self.result["filename"].endswith(tuple(self._table_handlers.keys())):
            print("Cleaning data...")

    def data_quality_check(self):
        # Placeholder: implement data quality checking logic
        if self.result["filename"].endswith(tuple(self._table_handlers.keys())):
            print("Checking data quality...")

    def save_to_mongo(self, record: dict):
        """
        record (dict):
            - metadata (dict): Metadata about the file.
            - summary (str) - optional: Summary text (for text/audio files).
            - result_df (DataFrame) - optional: Processed table data (for table files).
            - filename (str): Name of the file.
        """
        # Ensure required fields
        required_fields = ["Region", "School", "Ingestion_time", "Activity"]
        metadata = record.get("metadata", {})
        for field in required_fields:
            if field not in metadata:
                raise ValueError(f"Missing required metadata field: {field}")

        mongo_record = {
            "region": metadata["Region"],
            "school": metadata["School"],
            "ingestion_time": metadata["Ingestion_time"],
            "activity": metadata["Activity"],
            "filename": record.get("filename"),
        }
        # Add summary if present
        if "summary" in record:
            mongo_record["summary"] = record["summary"]
        # Add table data if present
        if "result_df" in record:
            df = record["result_df"]
            # Add each column as a new feature/column in mongo_record
            for col in df.columns:
                # If column name already exists, append '_table' to avoid overwrite
                key = col if col not in mongo_record else f"{col}_table"
                mongo_record[key] = df[col].tolist()
            # Optionally, also save the full table as records
            mongo_record["table_data"] = df.to_dict(orient="records")

        self.db_manager.save(mongo_record)


if __name__ == "__main__":
    processor = DataQualityProcessor()
    sample_metadata = {
        "Region": "South",
        "School": "Springfield High",
        "Activity": "Annual Report",
        "Ingestion_time": "2024-06-01T10:00:00Z"
    }
    # folder = "Data samples/"
    # files_to_upload = [
    #     folder + "PLMent_prepis.md",
    #     folder + "2024_9_FG-PL-ucastnici_TRASCRIPT.docx",
    #     folder + "Zaznam_FG_PedagogLidr_SKUPINA-B-android.mp3",
    #     folder + "ZV Otevirame dvere kolegialni podpore_běh 1_12 2023 (Odpovědi).xlsx",
    # ]
    folder = "../../data/synthetic_samples/"
    files_to_upload = [
        folder + "modified_behavior_metrics.csv",
        folder + "modified_clubs_random.json",
        folder + "modified_grades_random.json",
        folder + "modified_student_ranking.csv",
        folder + "modified_teacher_performance.csv"
    ]
    for file in files_to_upload:
        print(f"Processing file: {file}")
        result = processor.process(file, sample_metadata)
        