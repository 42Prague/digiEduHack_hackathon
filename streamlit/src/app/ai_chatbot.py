"""
AI Chatbot module for natural language to SQL translation (Education Data)
Enhanced with privacy guardrails and schema awareness.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import re
import os
import logging
import requests
from typing import Optional, Tuple, List, Dict, Any
from database import get_schema_info, get_database_values
from privacy import is_safe_sql, run_safe_query, ALLOWED_TABLES, SENSITIVE_COLUMNS
from components.sql_viewer import sql_viewer

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Core Functions ---
def get_ollama_config() -> Tuple[str, str]:
    """Get Ollama server URL and model from environment variables."""
    # Get from environment, fallback to defaults
    base_url = os.getenv("OLLAMA_URL", "http://host.docker.internal:8085/ollama")
    if not base_url.startswith(("http://", "https://")):
        base_url = f"http://{base_url}"
    model = os.getenv("OLLAMA_MODEL", "gpt-oss:20b")
    
    logger.info(f"Ollama config from env: OLLAMA_URL={os.getenv('OLLAMA_URL', 'NOT SET')}, OLLAMA_MODEL={os.getenv('OLLAMA_MODEL', 'NOT SET')}")
    logger.info(f"Using: base_url={base_url}, model={model}")
    
    return base_url, model

def get_translation_endpoint() -> str:
    """Get translation endpoint URL from environment variables."""
    # Get from environment, fallback to default
    translation_url = os.getenv("TRANSLATION_URL", "http://localhost:8085/translation/translate")
    
    # Ensure it starts with http:// or https://
    if not translation_url.startswith(("http://", "https://")):
        translation_url = f"http://{translation_url}"
    
    logger.info(f"Translation endpoint: {translation_url}")
    return translation_url

def translate_czech_to_english(text: str) -> Optional[str]:
    """Translate Czech text to English using the translation endpoint."""
    try:
        translation_url = get_translation_endpoint()
        
        payload = {
            "text": text,
            "source_lang": "cs",
            "target_lang": "en"
        }
        
        logger.info(f"Translating Czech text to English: {text[:100]}...")
        response = requests.post(translation_url, json=payload, timeout=30)
        response.raise_for_status()
        
        response_data = response.json()
        translated_text = response_data.get("text", "").strip()
        
        if translated_text:
            logger.info(f"Translation successful: {translated_text[:100]}...")
            return translated_text
        else:
            logger.warning("Translation endpoint returned empty text")
            return None
            
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        return None

def fetch_schema(conn) -> Tuple[Dict[str, List[str]], List[str]]:
    """Fetch schema info from FastAPI or fallback to database."""
    tables_summary = {}
    schema_descriptions = []

    try:
        # Try FASTAPI_URL_EXTERNAL first, then FASTAPI_URL
        fastapi_url = os.getenv("FASTAPI_URL_EXTERNAL") or os.getenv("FASTAPI_URL")
        
        # If no URL is set, default to Docker service name (for container-to-container communication)
        # Docker Compose allows containers to communicate using service names
        if not fastapi_url:
            # Default to Docker service name - this works in Docker Compose networks
            # If running locally (not in Docker), user should set FASTAPI_URL env var
            fastapi_url = "http://fastapi-bi-backend:8000"
            logger.info("No FastAPI URL set in env, defaulting to Docker service name: fastapi-bi-backend:8000")
        
        schemas_url = f"{fastapi_url}/schemas"
        logger.info(f"FastAPI URL from env: FASTAPI_URL_EXTERNAL={os.getenv('FASTAPI_URL_EXTERNAL', 'NOT SET')}, FASTAPI_URL={os.getenv('FASTAPI_URL', 'NOT SET')}")
        logger.info(f"Using FastAPI URL: {fastapi_url}")
        response = requests.get(schemas_url, timeout=10)
        if response.status_code == 200:
            schemas = response.json().get("schemas", [])
            for schema in schemas:
                schema_name = schema.get("schema_name", "unknown")
                columns = schema.get("columns", {})
                col_list = [f"{col_name} ({col_type})" for col_name, col_type in columns.items()]
                tables_summary[schema_name] = col_list
                if schema.get("description"):
                    schema_descriptions.append(f"{schema_name}: {schema['description']}")
    except Exception as e:
        logger.error(f"FastAPI schema fetch failed: {e}. Falling back to database.")
        try:
            schema_info = get_schema_info(conn)
            for col_info in schema_info:
                table = col_info.get("table_name", "unknown")
                if table not in tables_summary:
                    tables_summary[table] = []
                tables_summary[table].append(f"{col_info['column_name']} ({col_info['column_type']})")
        except Exception as db_error:
            logger.error(f"Database schema fetch failed: {db_error}")

    return tables_summary, schema_descriptions

def build_schema_description(tables_summary: Dict[str, List[str]], schema_descriptions: List[str]) -> str:
    """Build a human-readable schema description for the LLM."""
    schema_parts = []
    for table, cols in tables_summary.items():
        table_desc = f"\n{table}:"
        for desc in schema_descriptions:
            if desc.startswith(f"{table}:"):
                table_desc += f" ({desc.split(':', 1)[1].strip()})"
        table_desc += "\n  - " + "\n  - ".join(cols)
        schema_parts.append(table_desc)
    return "\n".join(schema_parts) if schema_parts else "⚠️ No schemas found."

def build_system_prompt(schema_description: str, regions: List[str], interventions: List[str]) -> str:
    regions_info = f"\nAvailable regions: {', '.join(regions)}" if regions else ""
    interventions_info = f"\nAvailable intervention types: {', '.join(interventions)}" if interventions else ""

    return f"""
You are a SQL expert specializing in DuckDB for education analytics.
Your job: Convert any natural-language question into a **valid, privacy-safe DuckDB SQL query**.

DATABASE SCHEMA:
{schema_description}
{regions_info}
{interventions_info}

PRIVACY RULES (MANDATORY):
1. Always aggregate (COUNT, AVG, SUM, etc.) — never return individual rows.
2. Include GROUP BY only when breaking down results by categories (e.g., by region, by type). Simple counts or totals don't need GROUP BY.
3. Never select sensitive columns: {', '.join(sorted(SENSITIVE_COLUMNS))}.
4. Never expose exact dates — use date bands or year/month instead.
5. Do not output names of individual students or participants.

QUERY RULES:
1. Return ONLY the SQL query (no explanation, no markdown).
2. Use valid DuckDB syntax.
3. Use exact region & intervention names from the available lists.
4. Always aggregate results — never return raw records.
5. Use explicit table names, no SELECT *.
6. For simple counts or totals, don't add GROUP BY unless the user asks for a breakdown.

EXAMPLES:

-- Simple total count (no GROUP BY needed)
SELECT COUNT(*) AS total_feedback
FROM Feedback;

-- Count by region (GROUP BY needed for breakdown)
SELECT Region, COUNT(*) AS feedback_count
FROM Feedback
GROUP BY Region
ORDER BY feedback_count DESC;

-- Average math scores by region
SELECT s.region, AVG(a.math_score) AS avg_score
FROM assessments a
JOIN schools s ON a.school_id = s.school_id
GROUP BY s.region
ORDER BY avg_score DESC;

-- Top 5 schools by total score
SELECT s.school_name,
       AVG(a.math_score + a.reading_score + a.science_score) AS avg_total_score
FROM schools s
JOIN assessments a ON a.school_id = s.school_id
GROUP BY s.school_name
ORDER BY avg_total_score DESC
LIMIT 5;

-- Average total scores by intervention type
SELECT i.type, AVG(a.math_score + a.reading_score + a.science_score) AS avg_total_score
FROM assessments a
JOIN schools s ON a.school_id = s.school_id
JOIN interventions i ON s.school_id = i.school_id
GROUP BY i.type;
"""


def call_ollama_api(base_url: str, model: str, messages: List[Dict[str, str]]) -> str:
    """Call Ollama API and extract SQL from the response."""
    chat_url = f"{base_url}/api/chat"
    payload = {
        "model": model,
        "messages": messages,
        "options": {"temperature": 0.1, "num_predict": 2000},
        "stream": False
    }

    try:
        logger.info(f"Calling Ollama API: POST {chat_url}")
        logger.info(f"Payload: model={payload['model']}, temperature={payload['options']['temperature']}, num_predict={payload['options']['num_predict']}")
        
        response = requests.post(chat_url, json=payload, timeout=120)
        response.raise_for_status()
        response_data = response.json()
        sql_query = response_data.get("message", {}).get("content", "").strip()
        
        logger.info(f"Ollama response received (first 500 chars): {sql_query[:500] if sql_query else 'EMPTY'}")
        logger.info(f"Ollama response length: {len(sql_query)} chars")

        # Extract SQL from markdown or raw text
        sql_match = re.search(r'(SELECT.*?;)', sql_query, re.IGNORECASE | re.DOTALL)
        if sql_match:
            sql_query = sql_match.group(1)
        else:
            sql_match = re.search(r'(SELECT.*?)(?:\n\n|$)', sql_query, re.IGNORECASE | re.DOTALL)
            if sql_match:
                sql_query = sql_match.group(1).strip()
                if not sql_query.endswith(';'):
                    sql_query += ';'

        # Clean up markdown artifacts
        sql_query = re.sub(r'^```\w*\n?', '', sql_query)
        sql_query = re.sub(r'\n?```.*$', '', sql_query, flags=re.DOTALL)
        final_sql = sql_query.strip()
        
        logger.info(f"\n--- EXTRACTED SQL QUERY ---")
        logger.info(final_sql)
        logger.info("=" * 80)
        
        return final_sql

    except Exception as e:
        logger.error(f"Ollama API error: {e}")
        raise Exception(f"Ollama API failed: {str(e)}")

def translate_to_sql_ollama(user_query: str, conn) -> Tuple[Optional[str], Optional[str]]:
    """Translate natural language to SQL using Ollama."""
    try:
        # Translate Czech input to English if needed
        original_query = user_query
        translated_query = translate_czech_to_english(user_query)
        
        # Use translated query if available, otherwise use original
        if translated_query:
            user_query = translated_query
            logger.info(f"Using translated query (Czech -> English): {original_query[:50]}... -> {translated_query[:50]}...")
        else:
            logger.info("No translation applied, using original query")
        
        base_url, model = get_ollama_config()
        tables_summary, schema_descriptions = fetch_schema(conn)
        regions, interventions = get_database_values(conn)

        schema_description = build_schema_description(tables_summary, schema_descriptions)
        system_prompt = build_system_prompt(schema_description, regions, interventions)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]

        # Log what we're sending to the model
        logger.info("=" * 80)
        logger.info("SENDING QUERY TO OLLAMA MODEL")
        logger.info("=" * 80)
        logger.info(f"Ollama URL: {base_url}")
        logger.info(f"Model: {model}")
        logger.info(f"\n--- USER QUERY ---")
        logger.info(user_query)
        logger.info(f"\n--- SYSTEM PROMPT (first 500 chars) ---")
        logger.info(system_prompt[:500] + "..." if len(system_prompt) > 500 else system_prompt)
        logger.info(f"\n--- FULL SYSTEM PROMPT LENGTH: {len(system_prompt)} chars ---")
        logger.info(f"\n--- FULL SYSTEM PROMPT ---")
        logger.info(system_prompt)
        logger.info(f"\n--- MESSAGES STRUCTURE ---")
        logger.info(f"Number of messages: {len(messages)}")
        logger.info(f"System message length: {len(messages[0]['content'])} chars")
        logger.info(f"User message: {messages[1]['content']}")
        logger.info("=" * 80)

        sql_query = call_ollama_api(base_url, model, messages)

        # Validate SQL starts with SELECT and is an aggregation
        if not sql_query.upper().startswith("SELECT"):
            return None, "Invalid SQL: Must start with SELECT."

        if "GROUP BY" not in sql_query.upper() and not any(agg in sql_query.upper() for agg in ["AVG(", "COUNT(", "SUM("]):
            return None, "Privacy violation: Aggregation (GROUP BY) required for sensitive data."

        return sql_query, None

    except Exception as e:
        logger.error(f"SQL translation failed: {e}")
        return None, f"Error: {str(e)}"

def generate_visualization(df: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """Generate the best visualization for education data."""
    if df.empty:
        return None

    numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    if len(numeric_cols) == 1 and len(categorical_cols) == 1:
        # Bar chart for categorical vs. numeric (e.g., region vs. avg_score)
        fig = px.bar(
            df,
            x=categorical_cols[0],
            y=numeric_cols[0],
            title=f"{numeric_cols[0].replace('_', ' ').title()} x {categorical_cols[0].replace('_', ' ').title()}"
        )
        return {"type": "bar", "chart": fig}

    elif len(numeric_cols) >= 2:
        # Scatter plot for numeric vs. numeric (e.g., math_score vs. reading_score)
        fig = px.scatter(
            df,
            x=numeric_cols[0],
            y=numeric_cols[1],
            title=f"{numeric_cols[1].replace('_', ' ').title()} vs {numeric_cols[0].replace('_', ' ').title()}"
        )
        return {"type": "scatter", "chart": fig}

    return None

# --- Streamlit UI ---
def get_available_tables_info(conn):
    """Get information about available tables for display"""
    try:
        tables = conn.execute("SHOW TABLES").fetchdf()
        if tables.empty:
            return []
        
        table_info = []
        for table_name in tables['name'].tolist():
            try:
                # Get row count
                count_result = conn.execute(f"SELECT COUNT(*) as count FROM {table_name}").fetchone()
                row_count = count_result[0] if count_result else 0
                
                # Get column info
                schema = conn.execute(f"DESCRIBE {table_name}").fetchdf()
                columns = schema['column_name'].tolist() if not schema.empty else []
                
                table_info.append({
                    'name': table_name,
                    'row_count': row_count,
                    'column_count': len(columns),
                    'columns': columns[:10]  # Show first 10 columns
                })
            except Exception as e:
                logger.warning(f"Error getting info for table {table_name}: {e}")
                table_info.append({
                    'name': table_name,
                    'row_count': 0,
                    'column_count': 0,
                    'columns': []
                })
        
        return table_info
    except Exception as e:
        logger.error(f"Error getting available tables: {e}")
        return []


def render_chat_interface(conn):
    """Render the Streamlit chat interface."""
    if not conn:
        st.error("❌ Database connection failed.")
        return

    # Initialize messages
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Show available tables in an expander
    table_info = get_available_tables_info(conn)
    if table_info:
        table_names = [t['name'] for t in table_info]
        st.info(f"📊 **AI can query {len(table_names)} table(s):** {', '.join(table_names)}")
        
        with st.expander("📋 View Table Details", expanded=False):
            st.markdown("**The AI chatbot can query these tables:**")
            for table in table_info:
                with st.expander(f"📋 {table['name']} ({table['row_count']:,} rows, {table['column_count']} columns)"):
                    if table['columns']:
                        st.markdown("**Columns:**")
                        # Display columns in a more readable format
                        cols_display = ", ".join(table['columns'])
                        if len(table['columns']) > 10:
                            cols_display += f" ... (+{len(table['columns']) - 10} more)"
                        st.code(cols_display, language=None)
                    else:
                        st.info("No column information available")
    else:
        st.warning("⚠️ No tables found in the database. The AI won't be able to answer questions until data is loaded.")
    
    # Clear chat button
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "sql" in message:
                sql_viewer(message["sql"], show_by_default=False)
            if "result" in message:
                st.dataframe(message["result"])
                if "chart" in message and message["chart"] is not None:
                    try:
                        # Check if it's a valid Plotly figure
                        from plotly.graph_objs import Figure
                        if isinstance(message["chart"], Figure):
                            st.plotly_chart(message["chart"], use_container_width=True)
                        else:
                            logger.warning(f"Invalid chart type in message: {type(message['chart'])}")
                    except Exception as e:
                        logger.error(f"Error displaying chart: {e}")

    if user_input := st.chat_input("Ask about education data..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Generating SQL..."):
                sql_query, error = translate_to_sql_ollama(user_input, conn)

            if error:
                st.error(error)
                st.session_state.messages.append({"role": "assistant", "content": f"Error: {error}"})
            elif sql_query:
                sql_viewer(sql_query, show_by_default=True)
                with st.spinner("Executing query..."):
                    result_df, privacy_error = run_safe_query(conn, sql_query)

                if privacy_error:
                    st.error(f"❌ Query error: {privacy_error}")
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"Query failed: {privacy_error}",
                        "sql": sql_query
                    })
                elif result_df is not None:
                    # Check if dataframe is empty
                    if result_df.empty:
                        st.warning("⚠️ Query executed successfully but returned 0 rows.")
                        st.info("💡 Try adjusting your query filters or check if the data exists in the table.")
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": "Query executed but returned no results.",
                            "sql": sql_query,
                            "result": result_df
                        })
                    else:
                        # Show result count
                        st.success(f"✅ Query returned {len(result_df)} row(s)")
                        
                        # Display dataframe
                        st.dataframe(result_df, use_container_width=True)
                        
                        # Generate and show chart if applicable
                        chart = generate_visualization(result_df)
                        if chart:
                            st.plotly_chart(chart["chart"], use_container_width=True)

                        # Store in session state
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": f"✅ Found {len(result_df)} row(s).",
                            "sql": sql_query,
                            "result": result_df,
                            "chart": chart["chart"] if chart else None
                        })
                else:
                    st.error("❌ Query execution failed. No results returned.")
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": "Query execution failed.",
                        "sql": sql_query
                    })

# --- Main ---
if __name__ == "__main__":
    st.title("🎓 Education Data AI Chatbot")
    render_chat_interface(st.connection("duckdb"))

