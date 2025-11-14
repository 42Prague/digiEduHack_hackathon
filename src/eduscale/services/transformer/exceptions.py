"""Custom exceptions for Transformer service."""


class TransformerException(Exception):
    """Base exception for Transformer service."""
    pass


class FileTooLargeError(TransformerException):
    """Exception raised when file exceeds size limit."""
    pass


class ExtractionError(TransformerException):
    """Exception raised when text extraction fails."""
    pass


class TranscriptionError(TransformerException):
    """Exception raised when audio transcription fails."""
    pass


class StorageError(TransformerException):
    """Exception raised when storage operations fail."""
    pass


class TabularError(TransformerException):
    """Exception raised when Tabular service call fails."""
    pass


class TransformationError(TransformerException):
    """Exception raised when transformation process fails."""
    pass
