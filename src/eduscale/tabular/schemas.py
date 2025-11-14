"""Pandera validation schemas for data quality.

This module defines validation schemas for each table type to ensure
data quality before loading to BigQuery.
"""

import logging
from typing import Literal

import pandas as pd
import pandera as pa
from pandera import Column, DataFrameSchema, Check

logger = logging.getLogger(__name__)

# ATTENDANCE Schema
ATTENDANCE_SCHEMA = DataFrameSchema(
    {
        "student_id": Column(str, required=True, nullable=False),
        "date": Column(pd.DatetimeTZDtype(tz="UTC"), required=True, nullable=False),
        "region_id": Column(str, required=True),
        "file_id": Column(str, required=True),
    },
    strict=False,  # Allow additional columns
    coerce=True,
)

# ASSESSMENT Schema
ASSESSMENT_SCHEMA = DataFrameSchema(
    {
        "student_id": Column(str, required=True, nullable=False),
        "test_score": Column(float, required=True, nullable=False, checks=[
            Check.greater_than_or_equal_to(0),
            Check.less_than_or_equal_to(100),
        ]),
        "date": Column(pd.DatetimeTZDtype(tz="UTC"), required=False),
        "region_id": Column(str, required=True),
        "file_id": Column(str, required=True),
    },
    strict=False,
    coerce=True,
)

# FEEDBACK Schema
FEEDBACK_SCHEMA = DataFrameSchema(
    {
        "feedback_id": Column(str, required=False),
        "feedback_text": Column(str, required=True, nullable=False),
        "author_id": Column(str, required=False),
        "author_type": Column(str, required=False),
        "sentiment_score": Column(float, required=False, checks=[
            Check.greater_than_or_equal_to(-1.0),
            Check.less_than_or_equal_to(1.0),
        ]),
        "region_id": Column(str, required=True),
        "file_id": Column(str, required=True),
    },
    strict=False,
    coerce=True,
)

# INTERVENTION Schema
INTERVENTION_SCHEMA = DataFrameSchema(
    {
        "intervention_id": Column(str, required=False),
        "intervention_type": Column(str, required=True, nullable=False),
        "student_id": Column(str, required=False),
        "date": Column(pd.DatetimeTZDtype(tz="UTC"), required=False),
        "participants_count": Column(float, required=False, checks=[
            Check.greater_than_or_equal_to(0),
        ]),
        "region_id": Column(str, required=True),
        "file_id": Column(str, required=True),
    },
    strict=False,
    coerce=True,
)

# RELATIONSHIP Schema (for junction tables)
RELATIONSHIP_SCHEMA = DataFrameSchema(
    {
        "region_id": Column(str, required=True),
        "file_id": Column(str, required=True),
        # Junction tables have variable columns, so minimal validation
    },
    strict=False,
    coerce=True,
)


def validate_normalized_df(
    df: pd.DataFrame, table_type: str
) -> tuple[pd.DataFrame, list[str]]:
    """Validate DataFrame against schema for table type.

    Args:
        df: Normalized DataFrame
        table_type: Table type (ATTENDANCE, ASSESSMENT, etc.)

    Returns:
        Tuple of (validated_df, warnings)
        - validated_df: DataFrame with valid rows
        - warnings: List of validation warning messages

    Raises:
        pa.errors.SchemaError: If validation fails on required columns (hard failure)
    """
    if df.empty:
        logger.warning("Empty DataFrame, skipping validation")
        return df, []

    # Select schema based on table type
    schema = _get_schema_for_table_type(table_type)

    if schema is None:
        logger.warning(f"No schema defined for table_type={table_type}, skipping validation")
        return df, []

    warnings = []

    try:
        # Validate DataFrame
        validated_df = schema.validate(df, lazy=True)
        logger.info(f"Validation passed for table_type={table_type}")
        return validated_df, warnings

    except pa.errors.SchemaErrors as e:
        # Collect validation errors
        error_df = e.failure_cases

        # Separate hard failures (missing required columns) from soft failures (invalid values)
        hard_failures = error_df[error_df["check"].str.contains("column_in_dataframe|not_nullable")]
        soft_failures = error_df[~error_df["check"].str.contains("column_in_dataframe|not_nullable")]

        if not hard_failures.empty:
            # Hard failure - raise exception
            logger.error(f"Hard validation failures: {hard_failures}")
            raise

        # Soft failures - log warnings and optionally remove invalid rows
        if not soft_failures.empty:
            logger.warning(f"Soft validation failures: {len(soft_failures)} issues found")

            for _, failure in soft_failures.iterrows():
                warning_msg = (
                    f"Validation warning in column '{failure['column']}': "
                    f"{failure['check']} failed for {failure['failure_case']}"
                )
                warnings.append(warning_msg)
                logger.warning(warning_msg)

            # For now, return DataFrame as-is with warnings
            # In production, could filter out invalid rows
            return df, warnings

    except Exception as e:
        logger.error(f"Unexpected validation error: {e}")
        raise


def _get_schema_for_table_type(table_type: str) -> DataFrameSchema | None:
    """Get Pandera schema for table type.

    Args:
        table_type: Table type

    Returns:
        DataFrameSchema or None if no schema defined
    """
    schemas = {
        "ATTENDANCE": ATTENDANCE_SCHEMA,
        "ASSESSMENT": ASSESSMENT_SCHEMA,
        "FEEDBACK": FEEDBACK_SCHEMA,
        "INTERVENTION": INTERVENTION_SCHEMA,
        "RELATIONSHIP": RELATIONSHIP_SCHEMA,
    }

    return schemas.get(table_type)
