"""FastAPI application for CSV data extraction."""

import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any
import logging
from dotenv import load_dotenv

from csv_extractor import CSVExtractor, SUPPORTED_TYPES

# Load environment variables
load_dotenv()

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, log_level))
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="CSV Data Extractor API",
    description="Extract structured CSV data from text using LLM",
    version="1.0.0"
)

# Initialize extractor (will use environment variables)
extractor = CSVExtractor()


class ColumnSchema(BaseModel):
    """Schema for a single CSV column."""
    name: str = Field(description="Column name", min_length=1)
    type: str = Field(description="Data type: string, number, integer, float, boolean, date, datetime", default="string")
    description: str = Field(description="What this column represents", default="")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate column name is not empty."""
        if not v or not v.strip():
            raise ValueError("Column name cannot be empty")
        return v.strip()

    @field_validator('type')
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Validate type is supported."""
        v_lower = v.lower()
        if v_lower not in SUPPORTED_TYPES:
            raise ValueError(
                f"Unsupported type '{v}'. Supported types: {', '.join(sorted(SUPPORTED_TYPES))}"
            )
        return v_lower


class ExtractionRequest(BaseModel):
    """Request model for extraction."""
    text: str = Field(description="Text to extract data from", min_length=1)
    schema: List[ColumnSchema] = Field(description="CSV column definitions", min_length=1)

    @field_validator('text')
    @classmethod
    def validate_text(cls, v: str) -> str:
        """Validate text is not empty."""
        if not v or not v.strip():
            raise ValueError("Text cannot be empty or whitespace only")
        return v

    @field_validator('schema')
    @classmethod
    def validate_schema(cls, v: List[ColumnSchema]) -> List[ColumnSchema]:
        """Validate schema has no duplicate column names."""
        if not v:
            raise ValueError("Schema cannot be empty")

        # Check for duplicate names
        names = [col.name for col in v]
        seen = set()
        duplicates = []
        for name in names:
            if name in seen:
                duplicates.append(name)
            seen.add(name)

        if duplicates:
            raise ValueError(f"Duplicate column names found: {', '.join(duplicates)}")

        return v


class ExtractionResponse(BaseModel):
    """Response model for extraction."""
    relevance_score: float = Field(description="How relevant the text is to the schema (0-1)")
    rows: List[Dict[str, Any]] = Field(description="Extracted data rows")
    explanation: str = Field(description="Explanation of the extraction")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "CSV Data Extractor API",
        "endpoints": {
            "/extract": "POST - Extract structured data from text",
            "/health": "GET - Health check"
        },
        "supported_types": [
            "string", "number", "integer", "float",
            "boolean", "date", "datetime"
        ],
        "model": extractor.model
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "CSV Data Extractor",
        "model": extractor.model,
        "ollama_url": extractor.ollama_url,
        "temperature": extractor.temperature
    }


@app.post("/extract", response_model=ExtractionResponse)
async def extract_data(request: ExtractionRequest):
    """
    Extract structured CSV data from text.

    Args:
        request: ExtractionRequest with text and schema

    Returns:
        ExtractionResponse with relevance_score, rows, and explanation

    Raises:
        HTTPException: 400 for invalid input, 500 for server errors
    """
    try:
        logger.info(f"Extracting data with schema: {[col.name for col in request.schema]}")

        # Convert Pydantic models to dicts
        schema_dicts = [col.model_dump() for col in request.schema]

        # Perform extraction
        result = extractor.extract(
            text=request.text,
            schema=schema_dicts
        )

        logger.info(f"Extraction complete. Relevance: {result.relevance_score}, Rows: {len(result.rows)}")

        return ExtractionResponse(
            relevance_score=result.relevance_score,
            rows=result.rows,
            explanation=result.explanation
        )

    except ValueError as e:
        # Input validation errors
        logger.warning(f"Invalid input: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")

    except Exception as e:
        # Unexpected server errors
        logger.error(f"Extraction error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during extraction: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8005"))
    uvicorn.run(app, host=host, port=port)
