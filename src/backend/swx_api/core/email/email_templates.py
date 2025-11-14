"""
Email Template Renderer
------------------------
This module provides a function to render email templates using Jinja2.

Features:
- `render_email_template()`: Loads an email template and populates it with dynamic data.
"""

from pathlib import Path
from typing import Any

from jinja2 import Template


def render_email_template(*, template_name: str, context: dict[str, Any]) -> str:
    """
    Renders an email template using Jinja2.

    Args:
        template_name (str): The name of the template file.
        context (dict[str, Any]): The dynamic data to populate in the template.

    Returns:
        str: The rendered email template as an HTML string.

    Raises:
        FileNotFoundError: If the template file does not exist.
        Exception: If template rendering fails.
    """
    try:
        template_path = Path(__file__).parent / "templates" / "build" / template_name
        template_str = template_path.read_text()
        return Template(template_str).render(context)
    except FileNotFoundError:
        raise FileNotFoundError(f"Template file '{template_name}' not found.")
    except Exception as e:
        raise Exception(f"Error rendering email template: {e}")
