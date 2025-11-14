"""
AI Dashboard module for generating insights using LangChain + Ollama + Qwen VL 4B
Generates dashboard insights from Parquet table schemas and basic statistics
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
import pandas as pd

logger = logging.getLogger(__name__)


def get_ollama_llm():
    """
    Get ChatOllama LLM instance configured for dashboard insights
    Reuses the same LangChain/Ollama setup as the chat feature
    
    Returns:
        ChatOllama instance or None if initialization fails
    """
    try:
        from langchain_ollama import ChatOllama
        from langchain_core.messages import SystemMessage, HumanMessage
        
        # Handle OLLAMA_URL - fix localhost to host.docker.internal when running in Docker
        base_url = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")
        
        # Ensure URL has a scheme
        if not base_url.startswith(("http://", "https://")):
            base_url = f"http://{base_url}"
        
        # If URL uses localhost or 127.0.0.1, check if we're in Docker and switch to host.docker.internal
        if ("localhost" in base_url or "127.0.0.1" in base_url) and "host.docker.internal" not in base_url:
            if os.path.exists("/.dockerenv") or os.getenv("CONTAINER_NAME"):
                base_url = base_url.replace("localhost", "host.docker.internal")
                base_url = base_url.replace("127.0.0.1", "host.docker.internal")
        
        # If OLLAMA_USE_HOST_GATEWAY is set, replace any host IP with host.docker.internal
        if os.getenv("OLLAMA_USE_HOST_GATEWAY", "").lower() in ("true", "1", "yes") and "host.docker.internal" not in base_url:
            import re
            host_match = re.search(r'://([^:/]+)', base_url)
            if host_match:
                original_host = host_match.group(1)
                base_url = base_url.replace(original_host, "host.docker.internal")
        
        # Remove trailing slash if present
        base_url = base_url.rstrip("/")
        
        # Use Qwen VL 4B for dashboard insights by default
        # Default model names to try: qwen2.5-vl:4b, qwen2-vl-7b, qwen-vl-4b
        # Check DASHBOARD_MODEL first (specific to dashboard), then OLLAMA_MODEL (shared), then default to Qwen VL 4B
        dashboard_model = os.getenv("DASHBOARD_MODEL") or os.getenv("OLLAMA_MODEL") or "qwen2.5-vl:4b"
        
        llm = ChatOllama(
            model=dashboard_model,
            base_url=base_url,
            temperature=0.2,  # Lower temperature for more consistent JSON output
            num_predict=3000,  # More tokens for detailed insights
            timeout=60.0  # Longer timeout for complex reasoning
        )
        
        return llm
    except ImportError as e:
        logger.error(f"LangChain Ollama not available: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error initializing Ollama LLM: {str(e)}")
        return None


def generate_schema_summary(df: pd.DataFrame, sample_rows: int = 20) -> Dict[str, Any]:
    """
    Generate a concise schema summary for a DataFrame
    
    Args:
        df: pandas DataFrame
        sample_rows: Number of sample rows to include (default: 20)
        
    Returns:
        Dictionary with schema information
    """
    try:
        # Basic column info
        columns_info = []
        for col in df.columns:
            dtype = str(df[col].dtype)
            col_info = {
                "name": col,
                "dtype": dtype,
                "type_category": _categorize_dtype(dtype, df[col])
            }
            
            # Add basic stats based on type
            if pd.api.types.is_numeric_dtype(df[col]):
                col_info["stats"] = {
                    "count": int(df[col].notna().sum()),
                    "null_count": int(df[col].isna().sum()),
                    "unique": int(df[col].nunique()),
                    "min": float(df[col].min()) if not df[col].isna().all() else None,
                    "max": float(df[col].max()) if not df[col].isna().all() else None,
                    "mean": float(df[col].mean()) if not df[col].isna().all() else None,
                    "std": float(df[col].std()) if not df[col].isna().all() else None
                }
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                col_info["stats"] = {
                    "count": int(df[col].notna().sum()),
                    "null_count": int(df[col].isna().sum()),
                    "unique": int(df[col].nunique()),
                    "min": str(df[col].min()) if not df[col].isna().all() else None,
                    "max": str(df[col].max()) if not df[col].isna().all() else None
                }
            else:
                # Categorical/text
                col_info["stats"] = {
                    "count": int(df[col].notna().sum()),
                    "null_count": int(df[col].isna().sum()),
                    "unique": int(df[col].nunique()),
                    "top_values": df[col].value_counts().head(5).to_dict() if df[col].nunique() > 0 else {}
                }
            
            columns_info.append(col_info)
        
        # Sample rows (convert to dict for JSON serialization)
        sample_df = df.head(sample_rows)
        sample_data = []
        for _, row in sample_df.iterrows():
            row_dict = {}
            for col in df.columns:
                val = row[col]
                # Convert non-serializable types
                if pd.isna(val):
                    row_dict[col] = None
                elif isinstance(val, (pd.Timestamp, pd.DatetimeTZDtype)):
                    row_dict[col] = str(val)
                else:
                    row_dict[col] = val
            sample_data.append(row_dict)
        
        return {
            "num_rows": len(df),
            "num_columns": len(df.columns),
            "columns": columns_info,
            "sample_rows": sample_data[:min(sample_rows, len(sample_data))]  # Limit sample size
        }
    except Exception as e:
        logger.error(f"Error generating schema summary: {str(e)}")
        return {
            "num_rows": len(df),
            "num_columns": len(df.columns),
            "columns": [{"name": col, "dtype": str(df[col].dtype)} for col in df.columns],
            "sample_rows": []
        }


def _categorize_dtype(dtype_str: str, series: pd.Series) -> str:
    """Categorize a dtype into: numeric, categorical, datetime, text"""
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
    elif pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    elif pd.api.types.is_categorical_dtype(series) or series.dtype == 'category':
        return "categorical"
    elif series.nunique() / len(series) < 0.5 and series.nunique() < 50:
        # Low cardinality - treat as categorical
        return "categorical"
    else:
        return "text"


def generate_dashboard_insights(
    table_name: str,
    schema_summary: Dict[str, Any],
    max_insights: int = 10
) -> List[Dict[str, Any]]:
    """
    Generate dashboard insights using LangChain + Ollama + Qwen VL 4B
    
    Args:
        table_name: Name of the table
        schema_summary: Schema summary dictionary from generate_schema_summary()
        max_insights: Maximum number of insights to generate (default: 10)
        
    Returns:
        List of insight dictionaries, or empty list if generation fails
    """
    try:
        llm = get_ollama_llm()
        if llm is None:
            logger.error("Failed to initialize LLM")
            return _get_fallback_insights(table_name, schema_summary)
        
        from langchain_core.messages import SystemMessage, HumanMessage
        
        # Build schema description text
        schema_text = f"Table: {table_name}\n"
        schema_text += f"Rows: {schema_summary['num_rows']:,}\n"
        schema_text += f"Columns: {schema_summary['num_columns']}\n\n"
        
        schema_text += "Columns:\n"
        for col_info in schema_summary['columns']:
            schema_text += f"  - {col_info['name']} ({col_info['type_category']}): {col_info['dtype']}\n"
            if 'stats' in col_info:
                stats = col_info['stats']
                schema_text += f"    Stats: "
                stat_parts = []
                if 'count' in stats:
                    stat_parts.append(f"count={stats['count']}")
                if 'unique' in stats:
                    stat_parts.append(f"unique={stats['unique']}")
                if 'mean' in stats and stats['mean'] is not None:
                    stat_parts.append(f"mean={stats['mean']:.2f}")
                if 'min' in stats and stats['min'] is not None:
                    stat_parts.append(f"min={stats['min']}")
                if 'max' in stats and stats['max'] is not None:
                    stat_parts.append(f"max={stats['max']}")
                if 'top_values' in stats:
                    top_vals = list(stats['top_values'].keys())[:3]
                    stat_parts.append(f"top={top_vals}")
                schema_text += ", ".join(stat_parts) + "\n"
        
        # Add sample data if available (truncated)
        if schema_summary.get('sample_rows'):
            schema_text += "\nSample data (first 5 rows):\n"
            for i, row in enumerate(schema_summary['sample_rows'][:5]):
                schema_text += f"  Row {i+1}: {json.dumps(row, default=str)}\n"
        
        # System prompt for insight generation
        system_prompt = """You are an expert data analyst specializing in generating dashboard insights from data schemas.

Your task is to analyze a table schema and statistics, then propose up to {max_insights} meaningful dashboard insights.

For each insight, provide:
1. **title**: A short, descriptive title (e.g., "Distribution by Category")
2. **description**: 1-2 sentences explaining what the insight shows
3. **chart_type**: One of: "table", "bar", "line", "area", "pie", "scatter", "histogram"
4. **x**: Column name for x-axis (if applicable, null otherwise)
5. **y**: Column name or expression for y-axis/metric (if applicable, null otherwise)
6. **group_by**: Optional column name for grouping/series (null if not applicable)
7. **aggregation**: Optional aggregation type: "count", "sum", "mean", "min", "max" (null if not applicable)
8. **filters**: Optional natural language description of filters to apply (null if not applicable)

IMPORTANT RULES:
- Focus on insights that reveal patterns, distributions, comparisons, or trends
- Prefer aggregations over raw data
- Use appropriate chart types: pie for small categorical distributions, bar for comparisons, line for trends, histogram for distributions
- Ensure all column names exist in the schema
- Return ONLY valid JSON, no markdown formatting or explanations

Return a JSON object with this structure:
{{
  "insights": [
    {{
      "title": "...",
      "description": "...",
      "chart_type": "...",
      "x": "column_name or null",
      "y": "column_name or null",
      "group_by": "column_name or null",
      "aggregation": "count|sum|mean|min|max or null",
      "filters": "optional filter description or null"
    }}
  ]
}}

Return ONLY the JSON object, nothing else.""".format(max_insights=max_insights)
        
        # Human message with schema
        human_prompt = f"""Analyze this table schema and generate dashboard insights:

{schema_text}

Generate up to {max_insights} meaningful insights. Focus on the most interesting patterns and relationships."""
        
        # Call LLM
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
        
        response = llm.invoke(messages)
        response_text = response.content.strip()
        
        # Extract JSON from response
        # Remove markdown code blocks if present
        response_text = response_text.replace("```json", "").replace("```", "").strip()
        
        # Try to parse JSON
        try:
            # Find JSON object in response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                result = json.loads(json_str)
                
                if "insights" in result and isinstance(result["insights"], list):
                    # Validate and clean insights
                    valid_insights = []
                    for insight in result["insights"][:max_insights]:
                        if _validate_insight(insight, schema_summary):
                            valid_insights.append(insight)
                    
                    if valid_insights:
                        return valid_insights
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {str(e)}")
            logger.debug(f"Response text: {response_text[:500]}")
        
        # Fallback if parsing fails
        logger.warning("Failed to parse LLM response, using fallback insights")
        return _get_fallback_insights(table_name, schema_summary)
        
    except Exception as e:
        logger.error(f"Error generating insights: {str(e)}", exc_info=True)
        return _get_fallback_insights(table_name, schema_summary)


def _validate_insight(insight: Dict[str, Any], schema_summary: Dict[str, Any]) -> bool:
    """Validate that an insight has required fields and valid column references"""
    required_fields = ["title", "description", "chart_type"]
    if not all(field in insight for field in required_fields):
        return False
    
    # Validate chart type
    valid_chart_types = ["table", "bar", "line", "area", "pie", "scatter", "histogram"]
    if insight.get("chart_type") not in valid_chart_types:
        return False
    
    # Validate column references
    column_names = {col["name"] for col in schema_summary["columns"]}
    
    for col_field in ["x", "y", "group_by"]:
        if insight.get(col_field) and insight[col_field] != "null":
            col_name = insight[col_field]
            if col_name not in column_names:
                logger.warning(f"Invalid column reference: {col_name}")
                return False
    
    return True


def _get_fallback_insights(table_name: str, schema_summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate basic fallback insights if LLM fails"""
    insights = []
    
    # Find numeric and categorical columns
    numeric_cols = [
        col["name"] for col in schema_summary["columns"]
        if col["type_category"] == "numeric"
    ]
    categorical_cols = [
        col["name"] for col in schema_summary["columns"]
        if col["type_category"] == "categorical"
    ]
    
    # Insight 1: Basic table view
    insights.append({
        "title": f"Data Overview: {table_name}",
        "description": f"First 100 rows of the {table_name} table",
        "chart_type": "table",
        "x": None,
        "y": None,
        "group_by": None,
        "aggregation": None,
        "filters": None
    })
    
    # Insight 2: Distribution of first categorical column
    if categorical_cols:
        cat_col = categorical_cols[0]
        insights.append({
            "title": f"Distribution by {cat_col}",
            "description": f"Count of records grouped by {cat_col}",
            "chart_type": "bar",
            "x": cat_col,
            "y": None,
            "group_by": None,
            "aggregation": "count",
            "filters": None
        })
    
    # Insight 3: Summary statistics of first numeric column
    if numeric_cols:
        num_col = numeric_cols[0]
        insights.append({
            "title": f"Summary Statistics: {num_col}",
            "description": f"Basic statistics for {num_col}",
            "chart_type": "histogram",
            "x": num_col,
            "y": None,
            "group_by": None,
            "aggregation": None,
            "filters": None
        })
    
    # Insight 4: Relationship between categorical and numeric
    if categorical_cols and numeric_cols:
        insights.append({
            "title": f"{numeric_cols[0]} by {categorical_cols[0]}",
            "description": f"Average {numeric_cols[0]} grouped by {categorical_cols[0]}",
            "chart_type": "bar",
            "x": categorical_cols[0],
            "y": numeric_cols[0],
            "group_by": None,
            "aggregation": "mean",
            "filters": None
        })
    
    return insights[:10]  # Limit to 10

