from pathlib import Path

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker


# ============================================================
#                 USER CONFIG (EDIT THESE)
# ============================================================

# The paths you want to ingest — files or folders
INPUT_PATHS = [
    r"C:\Users\ahmad\OneDrive\Desktop\Hackathon_project\digiEduHack_hackathon\srcs\bara"

    # Add more paths here
    # r"file1.md",
    # r"folder_path",
]

# Language tag to assign to transcripts
LANGUAGE = "cs"

# Link transcripts to a specific recording? Use integer or None
RECORDING_ID = None

# ============================================================
#                 INTERNAL CONFIG
# ============================================================

DB_URL = "sqlite:///hackathon.db"
SUPPORTED_SUFFIXES = {".txt", ".md", ".docx", ".pdf"}

engine = create_engine(DB_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

Base = declarative_base()


# ============================================================
#                 ORM MODELS
# ============================================================

class Recording(Base):
    __tablename__ = "Recording"

    recording_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String)
    date_recorded = Column(String)
    program_name = Column(String)
    group_label = Column(String)
    audio_file_path = Column(String)
    notes = Column(Text)

    transcripts = relationship("TranscriptFile", back_populates="recording")


class TranscriptFile(Base):
    __tablename__ = "TranscriptFile"

    transcript_id = Column(Integer, primary_key=True, autoincrement=True)
    recording_id = Column(Integer, ForeignKey("Recording.recording_id"), nullable=True)
    file_path = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    language = Column(String)
    full_text = Column(Text)

    recording = relationship("Recording", back_populates="transcripts")


# ============================================================
#                 DB INITIALIZATION
# ============================================================

def init_db():
    print("[*] Creating database and tables if not present...")
    Base.metadata.create_all(engine)
    print("[*] Database ready.")


# ============================================================
#                 TEXT EXTRACTION
# ============================================================

def extract_text_from_file(path: Path) -> str:
    suffix = path.suffix.lower()

    if suffix in {".txt", ".md"}:
        return path.read_text(encoding="utf-8", errors="ignore")

    elif suffix == ".docx":
        from docx import Document
        doc = Document(str(path))
        return "\n".join(p.text for p in doc.paragraphs)

    elif suffix == ".pdf":
        from PyPDF2 import PdfReader
        reader = PdfReader(str(path))
        texts = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                texts.append(t)
        return "\n\n".join(texts)

    else:
        raise ValueError(f"Unsupported file type: {suffix}")


# ============================================================
#                 FILE ITERATION
# ============================================================

def iter_supported_files(root: Path):
    if root.is_file():
        if root.suffix.lower() in SUPPORTED_SUFFIXES:
            yield root
        return

    for f in root.rglob("*"):
        if f.is_file() and f.suffix.lower() in SUPPORTED_SUFFIXES:
            yield f


# ============================================================
#                 INGESTION LOGIC
# ============================================================

def ingest_single_path(session, path: Path, language: str, recording_id: int | None):
    print(f"[*] Ingesting: {path}")

    text = extract_text_from_file(path)

    tf = TranscriptFile(
        recording_id=recording_id,
        file_path=str(path.resolve()),
        file_name=path.name,
        file_type=path.suffix.lower(),
        language=language,
        full_text=text,
    )

    session.add(tf)
    session.flush()

    print(f"      -> Saved as TranscriptFile ID {tf.transcript_id}")


def ingest_paths(paths, language: str, recording_id: int | None):
    with SessionLocal() as session:
        for raw in paths:
            root = Path(raw)
            if not root.exists():
                print(f"[!] Path does not exist: {root}")
                continue

            for f in iter_supported_files(root):
                try:
                    ingest_single_path(session, f, language, recording_id)
                except Exception as e:
                    print(f"[!] Failed to ingest {f}: {e}")

        session.commit()
        print("[*] All changes committed.")


# ============================================================
#                 MAIN EXECUTION
# ============================================================

def main():
    init_db()
    ingest_paths(INPUT_PATHS, LANGUAGE, RECORDING_ID)
    print("[*] Finished ingestion.")


if __name__ == "__main__":
    main()
