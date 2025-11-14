"""Natural Language Query (NLQ) API routes.

This module provides REST API endpoints for natural language to SQL translation
and execution against BigQuery analytics data.
"""

import logging
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from eduscale.core.config import settings
from eduscale.nlq.bq_query_engine import QueryExecutionError, run_analytics_query
from eduscale.nlq.llm_sql import SqlGenerationError, SqlSafetyError, generate_sql_from_nl

logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(prefix="/api/v1/nlq")

# Create UI router (for HTML templates)
ui_router = APIRouter()

# Setup Jinja2 templates
templates = Jinja2Templates(directory="src/eduscale/ui/templates")


# Pydantic models for request/response
class ChatMessage(BaseModel):
    """Single chat message."""

    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Request body for chat endpoint."""

    messages: list[ChatMessage] = Field(
        ..., description="Conversation messages (at least one user message required)"
    )


class ChatResponse(BaseModel):
    """Response body for chat endpoint."""

    messages: list[ChatMessage] = Field(..., description="Updated conversation messages")
    sql: str | None = Field(None, description="Generated SQL query (if successful)")
    explanation: str | None = Field(None, description="Explanation of the query")
    rows: list[dict[str, Any]] | None = Field(
        None, description="Query result rows (limited to first 20 for display)"
    )
    total_rows: int | None = Field(None, description="Total number of rows returned")
    error: str | None = Field(None, description="Error message if query failed")


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Natural language query chat endpoint.
    
    Accepts conversation messages, generates SQL from latest user message,
    executes query, and returns results formatted as assistant message.
    
    Args:
        request: ChatRequest with conversation messages
        
    Returns:
        ChatResponse with updated messages, SQL, and results
        
    Raises:
        HTTPException: 400 for invalid requests, 503 if feature disabled, 500 for server errors
    """
    # Generate correlation ID for tracing
    correlation_id = str(uuid4())
    
    logger.info(
        "Chat request received",
        extra={
            "correlation_id": correlation_id,
            "message_count": len(request.messages),
        },
    )
    
    # Check feature toggle
    if not settings.LLM_ENABLED:
        logger.warning(
            "NLQ feature disabled",
            extra={"correlation_id": correlation_id},
        )
        raise HTTPException(
            status_code=503,
            detail="Natural language query feature is currently disabled",
        )
    
    # Validate request
    if not request.messages:
        raise HTTPException(status_code=400, detail="No messages provided")
    
    # Extract latest user message
    user_messages = [msg for msg in request.messages if msg.role == "user"]
    if not user_messages:
        raise HTTPException(status_code=400, detail="No user message found")
    
    latest_user_message = user_messages[-1]
    user_query = latest_user_message.content
    
    logger.info(
        "Processing user query",
        extra={
            "correlation_id": correlation_id,
            "user_query": user_query,
        },
    )
    
    # Build conversation history (all messages except latest user message)
    # This is optional for MVP but supports future multi-turn conversations
    history = [
        {"role": msg.role, "content": msg.content}
        for msg in request.messages[:-1]
    ]
    
    # Initialize response
    sql = None
    explanation = None
    rows = None
    total_rows = None
    error = None
    assistant_message = None
    
    try:
        # Step 1: Generate SQL from user query
        logger.debug(
            "Generating SQL from natural language",
            extra={"correlation_id": correlation_id},
        )
        
        sql_result = generate_sql_from_nl(
            user_query=user_query,
            history=history,
            correlation_id=correlation_id,
        )
        
        sql = sql_result["sql"]
        explanation = sql_result["explanation"]
        
        logger.info(
            "SQL generated successfully",
            extra={
                "correlation_id": correlation_id,
                "sql": sql,
            },
        )
        
        # Step 2: Execute SQL query against BigQuery
        logger.debug(
            "Executing query against BigQuery",
            extra={"correlation_id": correlation_id},
        )
        
        rows = run_analytics_query(sql=sql, correlation_id=correlation_id)
        total_rows = len(rows)
        
        logger.info(
            "Query executed successfully",
            extra={
                "correlation_id": correlation_id,
                "total_rows": total_rows,
            },
        )
        
        # Step 3: Build assistant response message
        if total_rows == 0:
            assistant_message = f"{explanation}\n\nNo results found."
        else:
            assistant_message = f"{explanation}\n\nFound {total_rows} result(s)."
    
    except SqlSafetyError as e:
        # SQL safety validation failed
        logger.error(
            "SQL safety validation failed",
            extra={
                "correlation_id": correlation_id,
                "error": str(e),
                "sql": sql,
            },
        )
        error = f"Safety check failed: {e}"
        assistant_message = f"I couldn't process your query safely. {error}"
    
    except SqlGenerationError as e:
        # LLM failed to generate valid SQL
        logger.error(
            "SQL generation failed",
            extra={
                "correlation_id": correlation_id,
                "error": str(e),
            },
        )
        error = f"Failed to generate SQL: {e}"
        assistant_message = f"I couldn't understand your question. {error}"
    
    except QueryExecutionError as e:
        # BigQuery query execution failed
        logger.error(
            "BigQuery query execution failed",
            extra={
                "correlation_id": correlation_id,
                "error": str(e),
                "sql": sql,
            },
        )
        error = f"Query execution failed: {e}"
        assistant_message = f"I generated a query but it failed to execute. {error}"
    
    except Exception as e:
        # Unexpected error
        logger.error(
            "Unexpected error in chat endpoint",
            extra={
                "correlation_id": correlation_id,
                "error": str(e),
            },
            exc_info=True,
        )
        error = "An unexpected error occurred"
        assistant_message = f"Sorry, something went wrong. Please try again."
        
        # Return 500 for unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {e}",
        )
    
    # Build response
    updated_messages = request.messages.copy()
    updated_messages.append(
        ChatMessage(role="assistant", content=assistant_message)
    )
    
    # Limit rows for display (full results available via sql field)
    display_rows = rows[:20] if rows else None
    
    return ChatResponse(
        messages=updated_messages,
        sql=sql,
        explanation=explanation,
        rows=display_rows,
        total_rows=total_rows,
        error=error,
    )


@ui_router.get("/nlq/chat", response_class=HTMLResponse)
async def chat_ui(request: Request):
    """Render chat UI page.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        HTMLResponse with rendered chat template
    """
    return templates.TemplateResponse(
        "chat.html",
        {"request": request, "title": "EduScale Analytics Chat"},
    )

