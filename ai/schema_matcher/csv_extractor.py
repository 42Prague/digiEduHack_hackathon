"""Simple CSV data extractor using LangChain and Ollama."""

import os
import keyword
import json
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, create_model, field_validator, ValidationError
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# Type mapping for schema
TYPE_MAP = {
    "string": (str, None),
    "number": (float, None),
    "integer": (int, None),
    "float": (float, None),
    "boolean": (bool, None),
    "date": (str, None),
    "datetime": (str, None),
}

# Supported type names
SUPPORTED_TYPES = set(TYPE_MAP.keys())


def validate_column_name(name: str) -> None:
    """
    Validate that a column name is a valid Python identifier.

    Args:
        name: Column name to validate

    Raises:
        ValueError: If name is invalid
    """
    if not name:
        raise ValueError("Column name cannot be empty")

    if not name.isidentifier():
        raise ValueError(f"Column name '{name}' is not a valid Python identifier")

    if keyword.iskeyword(name):
        raise ValueError(f"Column name '{name}' is a Python keyword and cannot be used")


def validate_schema(schema: List[Dict[str, str]]) -> None:
    """
    Validate the schema before processing.

    Args:
        schema: List of column definitions

    Raises:
        ValueError: If schema is invalid
    """
    if not schema:
        raise ValueError("Schema cannot be empty")

    seen_names = set()
    for col in schema:
        # Check required fields
        if "name" not in col:
            raise ValueError("Each column must have a 'name' field")

        col_name = col["name"]
        col_type = col.get("type", "string").lower()

        # Validate column name
        validate_column_name(col_name)

        # Check for duplicates
        if col_name in seen_names:
            raise ValueError(f"Duplicate column name: '{col_name}'")
        seen_names.add(col_name)

        # Validate type
        if col_type not in SUPPORTED_TYPES:
            raise ValueError(
                f"Unsupported type '{col_type}' for column '{col_name}'. "
                f"Supported types: {', '.join(sorted(SUPPORTED_TYPES))}"
            )


def create_row_model(schema: List[Dict[str, str]]) -> type[BaseModel]:
    """
    Dynamically create a Pydantic model from schema.

    Args:
        schema: List of {name, type, description}

    Returns:
        Pydantic model class
    """
    fields = {}
    for col in schema:
        col_name = col["name"]
        col_type = col.get("type", "string").lower()
        col_desc = col.get("description", "")

        # Get Python type and default value
        py_type, default_val = TYPE_MAP.get(col_type, (str, None))

        # Make field optional (allow missing data)
        fields[col_name] = (Optional[py_type], Field(default=default_val, description=col_desc))

    return create_model("ExtractedRow", **fields)


def coerce_integer_field(value: Any, col_type: str) -> Any:
    """
    Coerce float values to int when the schema expects integer.

    Args:
        value: Value to coerce
        col_type: Expected column type

    Returns:
        Coerced value
    """
    if col_type == "integer" and value is not None:
        if isinstance(value, float):
            # Convert float to int if it's a whole number
            if value.is_integer():
                return int(value)
        elif isinstance(value, str):
            try:
                # Try parsing as float first, then convert to int
                float_val = float(value)
                if float_val.is_integer():
                    return int(float_val)
            except (ValueError, TypeError):
                pass
    return value


class ExtractionResult(BaseModel):
    """Result of extraction with validation."""
    relevance_score: float = Field(description="Relevance of text to schema (0-1)")
    rows: List[Dict[str, Any]] = Field(description="Extracted data rows")
    explanation: str = Field(description="Explanation of extraction and relevance")

    @field_validator('relevance_score')
    @classmethod
    def validate_relevance_score(cls, v: float) -> float:
        """Ensure relevance_score is between 0.0 and 1.0."""
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"relevance_score must be between 0.0 and 1.0, got {v}")
        return v


class CSVExtractor:
    """Extract structured CSV data from text using LLM."""

    def __init__(
        self,
        ollama_url: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None
    ):
        """
        Initialize the extractor.

        Args:
            ollama_url: URL of Ollama server (defaults to OLLAMA_URL env var)
            model: Model name (defaults to OLLAMA_MODEL env var)
            temperature: Temperature for generation (defaults to OLLAMA_TEMPERATURE env var)
        """
        self.ollama_url = ollama_url or os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.model = model or os.getenv("OLLAMA_MODEL", "gpt-oss:20b")
        self.temperature = temperature if temperature is not None else float(os.getenv("OLLAMA_TEMPERATURE", "0.1"))

        self.llm = Ollama(
            base_url=self.ollama_url,
            model=self.model,
            temperature=self.temperature
        )

    def extract(self, text: str, schema: List[Dict[str, str]]) -> ExtractionResult:
        """
        Extract data from text according to schema.

        Args:
            text: Input text to extract from
            schema: List of column definitions [{name, type, description}]

        Returns:
            ExtractionResult with relevance_score, rows, and explanation

        Raises:
            ValueError: If text or schema is invalid
        """
        # Validate inputs
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        validate_schema(schema)

        # Create dynamic Pydantic model for rows
        RowModel = create_row_model(schema)

        # Build schema description for prompt with better formatting
        schema_desc = "\n".join([
            f"- {col['name']} ({col.get('type', 'string')}): {col.get('description', 'No description')}"
            for col in schema
        ])

        # Build example row with actual field names
        example_fields = {col['name']: self._get_example_value(col.get('type', 'string'))
                          for col in schema}
        example_row_json = json.dumps(example_fields)

        # Create prompt with few-shot examples
        prompt_template = """You are a data extraction expert. Extract structured data from the text according to the schema.

SCHEMA (CSV columns to extract):
{schema_description}

TEXT TO ANALYZE:
{text}

INSTRUCTIONS:
1. Analyze if the text contains information relevant to the schema.
2. Calculate a relevance_score (float between 0.0 and 1.0):
   - 0.0-0.2 = Text completely unrelated to schema
   - 0.3-0.5 = Text has minimal relevant information
   - 0.6-0.8 = Text has substantial relevant information but some fields missing
   - 0.9-1.0 = Text contains complete information for all or most fields
3. Extract data matching the schema. Create ONE ROW per distinct entity (person, event, product, etc.).
4. For missing fields, use null (not empty strings or placeholders).
5. Respect the data types specified in the schema.
6. Provide a brief explanation of your extraction and relevance score.

OUTPUT FORMAT - Return ONLY valid JSON, no markdown formatting, no code blocks, no extra text:
{{
  "relevance_score": 0.85,
  "rows": [
    {example_row}
  ],
  "explanation": "Found 1 entity with 3 out of 4 fields present. Relevance is 0.85 because..."
}}

EXAMPLES:

Example 1 - High relevance:
Text: "John Doe, 30 years old, Software Engineer"
Schema: name (string), age (integer), role (string)
Output:
{{"relevance_score": 1.0, "rows": [{{"name": "John Doe", "age": 30, "role": "Software Engineer"}}], "explanation": "Complete information for all fields"}}

Example 2 - Low relevance:
Text: "The weather is sunny today"
Schema: name (string), age (integer), role (string)
Output:
{{"relevance_score": 0.0, "rows": [], "explanation": "Text discusses weather, completely unrelated to person schema"}}

Example 3 - Partial relevance:
Text: "Alice works as a Designer"
Schema: name (string), age (integer), role (string)
Output:
{{"relevance_score": 0.7, "rows": [{{"name": "Alice", "age": null, "role": "Designer"}}], "explanation": "Found name and role, but age is missing (2 out of 3 fields)"}}

Your response (ONLY valid JSON):"""

        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["schema_description", "text", "example_row"]
        )

        # Generate extraction
        chain = prompt | self.llm

        try:
            response = chain.invoke({
                "schema_description": schema_desc,
                "text": text,
                "example_row": example_row_json
            })

            # Clean response (remove markdown code blocks if present)
            response_clean = response.strip()
            if response_clean.startswith("```"):
                # Remove markdown code blocks
                lines = response_clean.split('\n')
                response_clean = '\n'.join(lines[1:-1] if lines[-1].strip() == '```' else lines[1:])
                response_clean = response_clean.strip()

            # Parse JSON response
            result_data = json.loads(response_clean)

            # Validate and coerce row data
            validated_rows = []
            for row in result_data.get("rows", []):
                # Coerce integer fields if needed
                coerced_row = {}
                for col in schema:
                    col_name = col["name"]
                    col_type = col.get("type", "string").lower()
                    value = row.get(col_name)
                    coerced_row[col_name] = coerce_integer_field(value, col_type)

                # Validate row with Pydantic model
                try:
                    validated_model = RowModel(**coerced_row)
                    validated_rows.append(validated_model.model_dump())
                except ValidationError as ve:
                    # Log validation error but continue with other rows
                    print(f"Warning: Row validation failed: {ve}")
                    continue

            # Create result with validated rows
            result = ExtractionResult(
                relevance_score=result_data.get("relevance_score", 0.0),
                rows=validated_rows,
                explanation=result_data.get("explanation", "No explanation provided")
            )

            return result

        except json.JSONDecodeError as e:
            # JSON parsing error
            return ExtractionResult(
                relevance_score=0.0,
                rows=[],
                explanation=f"Failed to parse LLM response as JSON: {str(e)}. Response was: {response[:200]}"
            )

        except ValidationError as e:
            # Pydantic validation error
            return ExtractionResult(
                relevance_score=0.0,
                rows=[],
                explanation=f"Data validation failed: {str(e)}"
            )

        except Exception as e:
            # Other errors (connection, etc.)
            return ExtractionResult(
                relevance_score=0.0,
                rows=[],
                explanation=f"Unexpected error during extraction: {type(e).__name__}: {str(e)}"
            )

    def _get_example_value(self, col_type: str) -> Any:
        """Get an example value for a given column type."""
        examples = {
            "string": "example text",
            "number": 42.5,
            "integer": 42,
            "float": 42.5,
            "boolean": True,
            "date": "2024-01-15",
            "datetime": "2024-01-15T10:30:00"
        }
        return examples.get(col_type.lower(), "example")
