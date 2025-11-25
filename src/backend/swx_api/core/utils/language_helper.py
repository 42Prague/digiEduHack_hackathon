"""
Translation Utilities
---------------------
This module provides utility functions for managing application translations.

Features:
- Loads and saves translations from a JSON cache file.
- Provides a translation lookup function with fallback to English.
- Ensures translations are formatted with dynamic placeholders.

Functions:
- `save_translations_to_cache()`: Saves translations to a JSON cache file.
- `load_translations_from_cache()`: Loads translations from a JSON cache file.
- `translate()`: Retrieves the translated text for a given key.
"""

import json
import os
import uuid

from fastapi import Request

from swx_api.core.middleware.logging_middleware import logger

# Path to the translation cache file
CACHE_FILE = "translation_cache.json"


def default_serializer(obj) -> str:
    """
    Custom serializer for handling non-serializable objects like UUIDs.

    Args:
        obj (Any): Object to be serialized.

    Returns:
        str: Serialized string representation.

    Raises:
        TypeError: If the object type is not serializable.
    """
    if isinstance(obj, uuid.UUID):
        return str(obj)
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")


def save_translations_to_cache(translations: dict) -> None:
    """
    Saves translations to a JSON cache file.

    Args:
        translations (dict): Dictionary of translations.

    Logs:
        - Success message when translations are saved.
        - Error message if saving fails.
    """
    try:
        with open(CACHE_FILE, "w") as file:
            json.dump(translations, file, indent=4, default=default_serializer)
        logger.info("Successfully saved translations to cache file '%s'.", CACHE_FILE)
    except Exception as e:
        logger.error("Failed to save translations to cache: %s", e)


def load_translations_from_cache() -> dict:
    """
    Loads translations from a JSON cache file.

    Returns:
        dict: Dictionary containing translations.

    Logs:
        - Success message if the cache file is loaded.
        - Error message if loading fails.
        - Message indicating cache file does not exist.
    """
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE) as file:
                translations = json.load(file)
            logger.info("Successfully loaded translations from cache file '%s'.", CACHE_FILE)
            return translations
        except Exception as e:
            logger.error("Failed to load translations from cache: %s", e)
            return {}

    logger.info("Cache file '%s' does not exist; returning empty translations.", CACHE_FILE)
    return {}


def translate(request: Request, key: str, **kwargs) -> str:
    """
    Retrieves the translated text for a given key.

    Args:
        request (Request): FastAPI request object (used to get state translations).
        key (str): The translation key.
        **kwargs: Additional placeholders for formatting the translation.

    Returns:
        str: The translated text, formatted with placeholders if provided.

    Behavior:
        - Looks up the translation in `request.state.translations`.
        - Falls back to the default language ('en') if no translation is found.
        - If still missing, returns the key itself as a fallback.

    Example:
        ```python
        translated_text = translate(request, "welcome_message", username="John")
        ```
    """

    translations = getattr(request.state, "translations", {})
    text = translations.get(key)

    if text is None:
        all_translations = load_translations_from_cache()
        default_translations = all_translations.get("en", {})
        text = default_translations.get(key, key)

    return text.format(**kwargs) if kwargs else text
