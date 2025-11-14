"""
MIME type classifier for file categorization.

Classifies files into categories based on their MIME type:
- text: Plain text, markdown, HTML, JSON, CSV, TSV, RTF
- pdf: PDF documents
- docx: Word documents (.doc, .docx)
- odf: OpenDocument formats (.odt, .odp, .ods)
- excel: Binary spreadsheet formats (Excel .xls/.xlsx)
- audio: Audio files and voice recordings
- archive: ZIP, TAR, GZIP archives
- other: Unknown or unsupported file types (including images, PowerPoint)
"""

from enum import Enum
from typing import Dict, List


class FileCategory(str, Enum):
    """File categories for processing routing."""

    TEXT = "text"
    PDF = "pdf"
    DOCX = "docx"
    ODF = "odf"
    EXCEL = "excel"
    AUDIO = "audio"
    ARCHIVE = "archive"
    OTHER = "other"


# MIME type mappings to file categories
MIME_CATEGORY_MAP: Dict[str, FileCategory] = {
    # Text formats
    "text/plain": FileCategory.TEXT,
    "text/markdown": FileCategory.TEXT,
    "text/html": FileCategory.TEXT,
    "application/json": FileCategory.TEXT,  # .json
    "application/rtf": FileCategory.TEXT,
    "application/octet-stream": FileCategory.TEXT,  # Generic binary (often used for .md files)
    # PDF formats (separate category)
    "application/pdf": FileCategory.PDF,
    # Microsoft Office Word formats (separate category)
    "application/msword": FileCategory.DOCX,  # .doc
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": FileCategory.DOCX,  # .docx
    # OpenDocument formats (separate category)
    "application/vnd.oasis.opendocument.text": FileCategory.ODF,  # .odt
    "application/vnd.oasis.opendocument.presentation": FileCategory.ODF,  # .odp
    "application/vnd.oasis.opendocument.spreadsheet": FileCategory.ODF,  # .ods
    # CSV/TSV formats (plain text tabular data)
    "text/csv": FileCategory.TEXT,  # .csv
    "text/tab-separated-values": FileCategory.TEXT,  # .tsv
    # Excel/Spreadsheet formats (binary/complex formats)
    "application/vnd.ms-excel": FileCategory.EXCEL,  # .xls
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": FileCategory.EXCEL,  # .xlsx

    # Audio formats
    "audio/mpeg": FileCategory.AUDIO,  # .mp3
    "audio/wav": FileCategory.AUDIO,
    "audio/ogg": FileCategory.AUDIO,
    "audio/webm": FileCategory.AUDIO,
    "audio/flac": FileCategory.AUDIO,
    "audio/aac": FileCategory.AUDIO,
    "audio/x-m4a": FileCategory.AUDIO,  # .m4a
    "audio/mp4": FileCategory.AUDIO,  # .m4a alternative
    "audio/m4a": FileCategory.AUDIO,  # .m4a alternative
    # Archive formats
    "application/zip": FileCategory.ARCHIVE,
    "application/x-zip-compressed": FileCategory.ARCHIVE,
    "application/x-tar": FileCategory.ARCHIVE,
    "application/gzip": FileCategory.ARCHIVE,
    "application/x-gzip": FileCategory.ARCHIVE,
    "application/x-bzip2": FileCategory.ARCHIVE,
    "application/x-7z-compressed": FileCategory.ARCHIVE,
    "application/x-rar-compressed": FileCategory.ARCHIVE,
}

# Prefix-based classification for partial matches
MIME_PREFIX_MAP: Dict[str, FileCategory] = {
    "text/": FileCategory.TEXT,
    "audio/": FileCategory.AUDIO,
}


def classify_mime_type(mime_type: str) -> FileCategory:
    """
    Classify a MIME type into a file category.

    Args:
        mime_type: The MIME type string (e.g., "application/pdf")

    Returns:
        FileCategory enum value (TEXT, IMAGE, AUDIO, ARCHIVE, or OTHER)

    Examples:
        >>> classify_mime_type("application/pdf")
        FileCategory.PDF
        >>> classify_mime_type("image/png")
        FileCategory.OTHER
        >>> classify_mime_type("audio/mp3")
        FileCategory.AUDIO
        >>> classify_mime_type("application/zip")
        FileCategory.ARCHIVE
        >>> classify_mime_type("application/octet-stream")
        FileCategory.TEXT
    """
    # Normalize MIME type (lowercase, remove parameters)
    normalized_mime = mime_type.lower().split(";")[0].strip()

    # Exact match
    if normalized_mime in MIME_CATEGORY_MAP:
        return MIME_CATEGORY_MAP[normalized_mime]

    # Prefix match
    for prefix, category in MIME_PREFIX_MAP.items():
        if normalized_mime.startswith(prefix):
            return category

    # Default to OTHER for unknown types
    return FileCategory.OTHER


def get_supported_mime_types() -> List[str]:
    """
    Get a list of all explicitly supported MIME types.

    Returns:
        List of MIME type strings that have explicit mappings
    """
    return list(MIME_CATEGORY_MAP.keys())


def get_category_mime_types(category: FileCategory) -> List[str]:
    """
    Get all MIME types for a specific category.

    Args:
        category: The file category to query

    Returns:
        List of MIME types in that category
    """
    return [mime for mime, cat in MIME_CATEGORY_MAP.items() if cat == category]
