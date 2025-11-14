"""Smoke tests for Transformer exceptions."""

import pytest
from eduscale.services.transformer.exceptions import (
    TransformerException,
    FileTooLargeError,
    ExtractionError,
    TranscriptionError,
    StorageError,
    TabularError,
    TransformationError,
)


def test_transformer_exception_hierarchy():
    """Test that all exceptions inherit from TransformerException."""
    assert issubclass(FileTooLargeError, TransformerException)
    assert issubclass(ExtractionError, TransformerException)
    assert issubclass(TranscriptionError, TransformerException)
    assert issubclass(StorageError, TransformerException)
    assert issubclass(TabularError, TransformerException)
    assert issubclass(TransformationError, TransformerException)


def test_exceptions_can_be_raised():
    """Test that exceptions can be raised and caught."""
    with pytest.raises(FileTooLargeError):
        raise FileTooLargeError("Test error")

    with pytest.raises(ExtractionError):
        raise ExtractionError("Test error")

    with pytest.raises(StorageError):
        raise StorageError("Test error")


def test_exceptions_can_be_caught_as_base():
    """Test that specific exceptions can be caught as TransformerException."""
    with pytest.raises(TransformerException):
        raise FileTooLargeError("Test error")

    with pytest.raises(TransformerException):
        raise ExtractionError("Test error")
