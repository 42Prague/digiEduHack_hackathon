# """
# Model Loader
# ------------
# This module dynamically loads (and reloads) all SQLAlchemy models
# from both `swx_api.app.models` and `swx_api.core.models` to ensure
# they are registered with `Base.metadata`.
#
# Features:
# - Dynamically imports and reloads models.
# - Ensures that models are registered properly with SQLAlchemy.
# - Provides debug logging for model imports.
#
# Functions:
# - `load_all_models()`: Dynamically loads all models and registers them with `Base.metadata`.
# """
import sys

import click
import pkgutil
import importlib
from swx_api.core.models.base import Base  # Adjust as needed


def load_all_models() -> Base:
    """
       Dynamically loads (and reloads) all SQLAlchemy models from both `swx_api.app.models`
       and `swx_api.core.models` so that they register with `Base.metadata`.

       Behavior:
           - Scans `app.models` and `core.models` for SQLAlchemy models.
           - Reloads modules to ensure up-to-date registrations.
           - Attaches all public attributes from submodules to the parent module.

       Returns:
           Base: The SQLAlchemy Base class with registered models.

       Logs:
           - Imported parent modules.
           - Reloaded submodules.
           - Attached public attributes from submodules to parent modules.

       Example:
           ```
           from swx_api.core.database.model_loader import load_all_models
           Base = load_all_models()
           ```
       """
    importlib.invalidate_caches()
    modules_to_scan = ["swx_api.app.models", "swx_api.core.models"]

    for module_name in modules_to_scan:
        try:
            if module_name not in sys.modules:
                parent_module = importlib.import_module(module_name)
                click.echo(f"DEBUG: Imported parent module: {module_name}")
            else:
                parent_module = sys.modules[module_name]

            # If it's a package, walk through submodules
            if hasattr(parent_module, "__path__"):
                for finder, name, is_pkg in pkgutil.walk_packages(
                        parent_module.__path__, parent_module.__name__ + "."
                ):
                    if is_pkg:
                        continue

                    # Use sys.modules cache to avoid reloading
                    if name in sys.modules:
                        mod = sys.modules[name]
                    else:
                        mod = importlib.import_module(name)

                    click.echo(f"DEBUG: Loaded submodule: {name}")

                    # Attach all public attributes from submodule to parent
                    for attr in dir(mod):
                        if not attr.startswith("_"):
                            setattr(parent_module, attr, getattr(mod, attr))
                            click.echo(f"DEBUG: Attached {attr} from {name} to {module_name}")

        except ModuleNotFoundError:
            click.echo(f"Warning: Module {module_name} not found. Skipping...", err=True)

    click.echo(f"DEBUG: Loaded models in metadata: {list(Base.metadata.tables.keys())}")
    return Base
