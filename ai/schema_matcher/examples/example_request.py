"""Example usage of the CSV Data Extractor API."""

import requests
import json

API_URL = "http://localhost:8005"


def example_1_basic_extraction():
    """Example 1: Basic person data extraction."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Person Data Extraction")
    print("="*60)

    request_data = {
        "text": "John Doe is 35 years old and works as a Software Engineer. His email is john.doe@example.com.",
        "schema": [
            {"name": "name", "type": "string", "description": "Full name of the person"},
            {"name": "age", "type": "number", "description": "Age in years"},
            {"name": "role", "type": "string", "description": "Job title or position"},
            {"name": "email", "type": "string", "description": "Email address"}
        ]
    }

    response = requests.post(f"{API_URL}/extract", json=request_data)
    result = response.json()

    print(f"\nRelevance Score: {result['relevance_score']}")
    print(f"Extracted Rows: {json.dumps(result['rows'], indent=2)}")
    print(f"Explanation: {result['explanation']}")


def example_2_multiple_entities():
    """Example 2: Multiple people in one text."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Multiple Entities")
    print("="*60)

    request_data = {
        "text": "The team includes Jane Smith (28, Designer) and Bob Johnson (42, Manager). Jane's email is jane@company.com.",
        "schema": [
            {"name": "name", "type": "string", "description": "Full name"},
            {"name": "age", "type": "number", "description": "Age"},
            {"name": "role", "type": "string", "description": "Job title"},
            {"name": "email", "type": "string", "description": "Email"}
        ]
    }

    response = requests.post(f"{API_URL}/extract", json=request_data)
    result = response.json()

    print(f"\nRelevance Score: {result['relevance_score']}")
    print(f"Extracted Rows ({len(result['rows'])} people):")
    for i, row in enumerate(result['rows'], 1):
        print(f"  Person {i}: {json.dumps(row, indent=4)}")
    print(f"Explanation: {result['explanation']}")


def example_3_irrelevant_text():
    """Example 3: Text unrelated to schema (low relevance)."""
    print("\n" + "="*60)
    print("EXAMPLE 3: Irrelevant Text (Low Relevance)")
    print("="*60)

    request_data = {
        "text": "The weather today is sunny with a temperature of 25 degrees Celsius. Perfect for a picnic!",
        "schema": [
            {"name": "name", "type": "string", "description": "Person's name"},
            {"name": "age", "type": "number", "description": "Age in years"},
            {"name": "email", "type": "string", "description": "Email address"}
        ]
    }

    response = requests.post(f"{API_URL}/extract", json=request_data)
    result = response.json()

    print(f"\nRelevance Score: {result['relevance_score']} (should be low)")
    print(f"Extracted Rows: {json.dumps(result['rows'], indent=2)}")
    print(f"Explanation: {result['explanation']}")


def example_4_partial_data():
    """Example 4: Text with partial information (missing fields)."""
    print("\n" + "="*60)
    print("EXAMPLE 4: Partial Data (Missing Fields)")
    print("="*60)

    request_data = {
        "text": "Alice works as a Data Scientist. She can be reached at alice@data.com.",
        "schema": [
            {"name": "name", "type": "string", "description": "Full name"},
            {"name": "age", "type": "number", "description": "Age in years"},
            {"name": "role", "type": "string", "description": "Job title"},
            {"name": "email", "type": "string", "description": "Email address"}
        ]
    }

    response = requests.post(f"{API_URL}/extract", json=request_data)
    result = response.json()

    print(f"\nRelevance Score: {result['relevance_score']}")
    print(f"Extracted Rows: {json.dumps(result['rows'], indent=2)}")
    print(f"Note: Age field should be empty/null (not mentioned in text)")
    print(f"Explanation: {result['explanation']}")


def example_5_event_data():
    """Example 5: Event data extraction."""
    print("\n" + "="*60)
    print("EXAMPLE 5: Event Data Extraction")
    print("="*60)

    request_data = {
        "text": "The annual conference will be held on March 15, 2024 in Prague. We expect 150 attendees.",
        "schema": [
            {"name": "event_name", "type": "string", "description": "Name of the event"},
            {"name": "date", "type": "date", "description": "Event date"},
            {"name": "location", "type": "string", "description": "Event location/city"},
            {"name": "attendees", "type": "number", "description": "Expected number of attendees"}
        ]
    }

    response = requests.post(f"{API_URL}/extract", json=request_data)
    result = response.json()

    print(f"\nRelevance Score: {result['relevance_score']}")
    print(f"Extracted Rows: {json.dumps(result['rows'], indent=2)}")
    print(f"Explanation: {result['explanation']}")


def check_health():
    """Check API health."""
    print("\n" + "="*60)
    print("API HEALTH CHECK")
    print("="*60)

    response = requests.get(f"{API_URL}/health")
    health = response.json()

    print(f"Status: {health['status']}")
    print(f"Service: {health['service']}")
    print(f"Model: {health['model']}")
    print(f"Ollama URL: {health['ollama_url']}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("CSV DATA EXTRACTOR - EXAMPLE USAGE")
    print("="*60)

    # Check if API is running
    try:
        check_health()
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to API at http://localhost:8005")
        print("Please start the API first:")
        print("  docker run -p 8005:8005 csv-extractor")
        print("  OR")
        print("  python app.py")
        exit(1)

    # Run examples
    try:
        example_1_basic_extraction()
        example_2_multiple_entities()
        example_3_irrelevant_text()
        example_4_partial_data()
        example_5_event_data()

        print("\n" + "="*60)
        print("ALL EXAMPLES COMPLETE")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
