#!/usr/bin/env python3
"""Quick test of CSV extractor with sample data."""

from csv_extractor import CSVExtractor
import json

# Initialize extractor (uses env vars)
print("Initializing extractor...")
extractor = CSVExtractor()
print(f"Using model: {extractor.model} at {extractor.ollama_url}")

# Test data
test_text = """
John Doe is 35 years old and works as a Software Engineer.
His email is john.doe@example.com.
Jane Smith, age 28, is a Data Scientist at TechCorp.
Her contact is jane.smith@techcorp.com.
"""

test_schema = [
    {"name": "name", "type": "string", "description": "Full name of the person"},
    {"name": "age", "type": "integer", "description": "Age in years"},
    {"name": "role", "type": "string", "description": "Job title or profession"},
    {"name": "email", "type": "string", "description": "Email address"}
]

print("\n" + "="*60)
print("TEST INPUT")
print("="*60)
print(f"Text: {test_text.strip()}")
print(f"\nSchema: {json.dumps(test_schema, indent=2)}")

print("\n" + "="*60)
print("RUNNING EXTRACTION...")
print("="*60)

try:
    result = extractor.extract(text=test_text, schema=test_schema)

    print(f"\n✓ Extraction successful!")
    print(f"\nRelevance Score: {result.relevance_score}")
    print(f"Rows Extracted: {len(result.rows)}")
    print(f"\nExtracted Data:")
    print(json.dumps(result.rows, indent=2))
    print(f"\nExplanation: {result.explanation}")

except Exception as e:
    print(f"\n✗ Extraction failed: {e}")
    import traceback
    traceback.print_exc()
