"""
Resource Utilities
------------------
This module provides helper functions for naming conversions and file path resolution.

Features:
- Converts names between `PascalCase`, `snake_case`, and URL paths.
- Generates file paths for creating resources.
- Detects core developers based on environment variables.

Functions:
- `format_name()`: Converts names to `PascalCase` (Class Names) and `snake_case` (File/Table Names).
- `create_file()`: Creates a file if it does not already exist.
- `extract_version()`: Extracts API version from a resource path.
- `is_core_developer()`: Checks if the user is a core developer.
- `resolve_base_path()`: Determines base folder path for a resource.
- `to_snake_case()`: Converts `CamelCase` to `snake_case`.
- `to_pascal_case()`: Converts `snake_case` to `PascalCase`.
- `normalize_resource_names()`: Generates base name, file name, and class name for resources.
"""

import re
import os
import click
from fastapi import Request, HTTPException


def format_name(name: str) -> tuple[str, str]:
    """
    Converts the given name into standard naming conventions:
    - Class Name: PascalCase
    - Table/File Name: snake_case

    Args:
        name (str): The input name (e.g., "user_profile", "UserProfile").

    Returns:
        tuple[str, str]: (PascalCase name, snake_case name)
    """
    name = name.strip().replace("-", "_").replace(" ", "_")

    # Convert to PascalCase (Class Names)
    class_name = "".join(word.capitalize() for word in name.split("_"))

    # Convert to snake_case (File/Table Names)
    table_name = re.sub(r"(?<!^)(?=[A-Z])", "_", class_name).lower()

    return class_name, table_name


def create_file(path: str, content: str) -> None:
    """
    Creates a file if it does not already exist.

    Args:
        path (str): File path to create.
        content (str): File content to write.

    Notes:
        - Ensures the parent directories exist.
        - Uses UTF-8 encoding when writing files.
        - Skips creation if the file already exists.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)

    if os.path.exists(path):
        click.secho(f"Skipped (already exists): {path}", fg="yellow")
        return

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def extract_version(name: str) -> tuple[str | None, str]:
    """
    Extracts API version from a resource path.

    Args:
        name (str): The resource path (e.g., "v1/product").

    Returns:
        tuple[str | None, str]: (version or None, resource name)

    Examples:
        - "v1/product" -> ("v1", "product")
        - "product" -> (None, "product")
    """
    parts = name.split("/")
    if len(parts) == 2 and parts[0].startswith("v") and parts[0][1:].isdigit():
        return parts[0], parts[1]
    return None, name


def is_core_developer() -> bool:
    """
    Checks if the user is a core developer based on an environment variable.

    Returns:
        bool: True if CORE_DEV_MODE is set to "1".
    """
    return os.getenv("CORE_DEV_MODE", "0") == "1"


def resolve_base_path(name: str, module: str | None = None) -> tuple[str, str, str | None, str]:
    """
    Determines the correct base folder path and extracts version if provided.

    Args:
        name (str): The resource name (e.g., "v1/product", "core/user").
        module (Optional[str]): The module path (optional).

    Returns:
        tuple[str, str, str | None, str]: (folder path, module path, version, resource name)

    Examples:
        - "v1/product"  -> ("swx_api/app", "swx_api.app", "v1", "product")
        - "product"     -> ("swx_api/app", "swx_api.app", None, "product")
        - "core/user"   -> ("swx_api/core", "swx_api.core", None, "user")
    """
    version = None

    if "/" in name and name.split("/", 1)[0].startswith("v") and name.split("/", 1)[0][1:].isdigit():
        version, resource_name = name.split("/", 1)
    elif name.startswith("core/"):
        _, resource_name = name.split("/", 1)
    else:
        resource_name = name

    if name.startswith("core/") or (module and "swx_api.core" in module):
        return "swx_api/core", "swx_api.core", version, resource_name
    return "swx_api/app", "swx_api.app", version, resource_name


def to_snake_case(name: str) -> str:
    """
    Converts a CamelCase or mixed string to snake_case.

    Args:
        name (str): Input string in CamelCase.

    Returns:
        str: The converted string in snake_case.

    Example:
        "UserProfile" -> "user_profile"
    """
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def to_pascal_case(name: str) -> str:
    """
    Converts a snake_case string to PascalCase.

    Args:
        name (str): Input string in snake_case.

    Returns:
        str: The converted string in PascalCase.

    Example:
        "user_profile" -> "UserProfile"
    """
    return "".join(word.capitalize() for word in name.split("_"))


def normalize_resource_names(raw_name: str, component_suffix: str) -> tuple[str, str, str]:
    """
    Generates standardized names for resources.

    Args:
        raw_name (str): The raw resource name (e.g., "user_profile").
        component_suffix (str): The component type (e.g., "repository", "service").

    Returns:
        tuple[str, str, str]: (base_name, file_name, class_name)

    Examples:
        - ("languageTranslation", "repository") -> ("language_translation", "language_translation_repository", "LanguageTranslationRepository")
        - ("user", "model") -> ("user", "user", "User")
    """
    base = to_snake_case(raw_name.split("/")[-1].strip())
    if component_suffix.lower() == "model":
        file_name = base  # Drop the "model" suffix for the file name
        class_name = to_pascal_case(base)
    else:
        file_name = f"{base}_{component_suffix}"
        class_name = f"{to_pascal_case(base)}{to_pascal_case(component_suffix)}"
    return base, file_name, class_name


def get_model_columns(model_cls):
    """
    Introspect a SQLModel (or SQLAlchemy) model to retrieve its columns.
    Returns a list of tuples: (column_name, column_type)
    """
    columns = []
    if hasattr(model_cls, "__table__"):
        for col in model_cls.__table__.columns:
            columns.append((col.key, str(col.type)))
    return columns


def format_columns_comment(columns):
    """
    Create a formatted comment string with model column information.
    """
    if not columns:
        return "# No columns detected."
    lines = ["# Detected columns:"]
    for name, col_type in columns:
        lines.append(f"#   - {name}: {col_type}")
    return "\n".join(lines)


def get_extra_schemas(prefix, module):
    """
    Scans the module for schema classes that start with the given prefix.
    Returns a dict of detected schema classes mapped to action names.
    """
    extra = {}
    for attr_name in dir(module):
        if attr_name.startswith(prefix) and attr_name != prefix:
            schema_action = attr_name[len(prefix):].lower()  # Extract method name
            extra[schema_action] = attr_name
    return extra


def extract_api_key(request: Request) -> str:
    auth = request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = auth.split(" ", 1)[1].strip()
    return token
