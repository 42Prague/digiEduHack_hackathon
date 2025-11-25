import importlib
import os
import subprocess
import sys
import time

import click
from click.core import Context

# Import the Base for models registration.
from swx_api.core.utils.helper import (
    resolve_base_path,
    normalize_resource_names,
    create_file, get_extra_schemas,
)
from swx_api.core.utils.model import load_all_models

from swx_api.core.cli.commands.resource_templates import (
    TEMPLATES,
    METHOD_TEMPLATE,
    CONTROLLER_METHOD_TEMPLATE,
    REPOSITORY_METHOD_TEMPLATE,
    ROUTE_METHOD_TEMPLATE,
)


# ===================== CLI Commands =====================

# -------------------- Controller Command --------------------
@click.command()
@click.argument("name")
@click.option(
    "--module", default="swx_api.app.models", help="Module where the model is defined"
)
def controller(name, module):
    """Generate a controller based on an existing model."""
    folder_path, module_path, version, res_name = resolve_base_path(name, module)
    base, controller_file, controller_class = normalize_resource_names(
        res_name, "controller"
    )
    _, service_file, service_class = normalize_resource_names(res_name, "service")
    _, model_file, model_class = normalize_resource_names(res_name, "model")

    # Get extra schemas from the module (if any) using the model's class prefix.
    mod = importlib.import_module(module)
    extra_schemas = get_extra_schemas(model_class, mod)
    extra_controller_methods = ""
    if "update_password" in extra_schemas:
        extra_controller_methods += f"""
    @staticmethod
    def update_password(request: Request, id: uuid.UUID, data: {extra_schemas["update_password"]}, db: SessionDep):
        \"\"\"Controller: update password for {base} resource.\"\"\"
        return {service_class}.update_password(db, id, data)
        """
    if "new_password" in extra_schemas:
        extra_controller_methods += f"""
    @staticmethod
    def reset_password(request: Request, id: uuid.UUID, data: {extra_schemas["new_password"]}, db: SessionDep):
        \"\"\"Controller: reset password for {base} resource.\"\"\"
        return {service_class}.reset_password(db, id, data)
        """

    columns_comment = "# Controller generated based on model fields."
    name_lower = base

    content = TEMPLATES["controller"].format(
        columns_comment=columns_comment,
        controller_class=controller_class,
        name_lower=name_lower,
        module_path=module_path,
        service_file=service_file,
        service_class=service_class,
        model_file=model_file,
        model_class=model_class,
        extra_controller_methods=extra_controller_methods,
    )
    create_file(
        os.path.join(folder_path, "controllers", f"{controller_file}.py"), content
    )


# -------------------- Route Command --------------------
@click.command()
@click.argument("name")
@click.option(
    "--module", default="swx_api.app.models", help="Module where the model is defined"
)
def route(name, module):
    """Generate an API route that delegates to the controller."""
    folder_path, module_path, version, res_name = resolve_base_path(name, module)
    base, controller_file, controller_class = normalize_resource_names(
        res_name, "controller"
    )
    _, model_file, model_class = normalize_resource_names(res_name, "model")
    extra_route_endpoints = ""  # You can add extra endpoints if needed.
    columns_comment = "# Route generated based on controller and model."
    name_lower = base

    if version:
        route_dir = os.path.join(folder_path, "routes", version)
    else:
        route_dir = os.path.join(folder_path, "routes")
    os.makedirs(route_dir, exist_ok=True)

    route_path = os.path.join(route_dir, f"{base}_route.py")
    content = TEMPLATES["route"].format(
        columns_comment=columns_comment,
        controller_file=controller_file,
        controller_class=controller_class,
        name_lower=name_lower,
        model_file=model_file,
        model_class=model_class,
        module_path=module_path,
        version=version or "",
        extra_route_endpoints=extra_route_endpoints,
    )
    create_file(route_path, content)


# -------------------- Repository Command --------------------
@click.command()
@click.argument("name")
@click.option(
    "--module", default="swx_api.app.models", help="Module where the model is defined"
)
def repository(name, module):
    """Generate a repository based on the existing model."""
    folder_path, module_path, version, res_name = resolve_base_path(name, module)
    base, repo_file, repo_class = normalize_resource_names(res_name, "repository")
    _, model_file, model_class = normalize_resource_names(res_name, "model")
    extra_repo_methods = ""  # Extend if custom repository methods are needed.
    columns_comment = "# Repository generated based on model fields."
    name_lower = base

    content = TEMPLATES["repository"].format(
        columns_comment=columns_comment,
        module_path=module_path,
        model_file=model_file,
        model_class=model_class,
        repo_class=repo_class,
        name_lower=name_lower,
        extra_repo_methods=extra_repo_methods,
    )
    create_file(os.path.join(folder_path, "repositories", f"{repo_file}.py"), content)


# -------------------- Service Command --------------------
@click.command()
@click.argument("name")
@click.option(
    "--module", default="swx_api.app.models", help="Module where the model is defined"
)
def service(name, module):
    """Generate a service based on the existing model."""
    folder_path, module_path, version, res_name = resolve_base_path(name, module)
    base, service_file, service_class = normalize_resource_names(res_name, "service")
    _, model_file, model_class = normalize_resource_names(res_name, "model")
    _, repo_file, repo_class = normalize_resource_names(res_name, "repository")
    extra_imports = ""
    extra_methods = ""
    mod = importlib.import_module(module)
    extra_schemas = get_extra_schemas(model_class, mod)
    if "update_password" in extra_schemas:
        extra_imports += f"from {module} import {extra_schemas['update_password']}\n"
        extra_methods += f"""
    @staticmethod
    def update_password(db: SessionDep, id: uuid.UUID, data: {extra_schemas["update_password"]}):
        \"\"\"Service layer: update password for {base} resource.\"\"\"
        # Implement your password update logic here.
        return {repo_class}.update_password(db, id, data)
        """
    if "new_password" in extra_schemas:
        extra_imports += f"from {module} import {extra_schemas['new_password']}\n"
        extra_methods += f"""
    @staticmethod
    def reset_password(db: SessionDep, id: uuid.UUID, data: {extra_schemas["new_password"]}):
        \"\"\"Service layer: reset password for {base} resource.\"\"\"
        # Implement your password reset logic here.
        return {repo_class}.reset_password(db, id, data)
        """
    columns_comment = "# Service generated based on repository and model."
    name_lower = base

    content = TEMPLATES["service"].format(
        columns_comment=columns_comment,
        service_class=service_class,
        name_lower=name_lower,
        repo_file=repo_file,
        repo_class=repo_class,
        model_file=model_file,
        model_class=model_class,
        module_path=module_path,
        extra_imports=extra_imports,
        extra_methods=extra_methods,
    )
    create_file(os.path.join(folder_path, "services", f"{service_file}.py"), content)


# ===================== Model Generation Command =====================


@click.command()
@click.argument("name")
@click.option(
    "--columns",
    default="",
    help="Comma-separated list of columns (e.g. 'name:str, price:float, description:str')",
)
@click.option(
    "--module",
    default="swx_api.app.models",
    help="Module path for the model (affects file location)",
)
def model(name, columns, module):
    """
    Generate a new model file with optional columns following a CRUD pattern.
    The generated file will include:
      - A shared base class ({class_name}Base) for common fields.
      - A table class ({class_name}) that inherits from the base and adds a primary key.
      - Separate CRUD schemas for creation, update, and public output.

    The first column provided is treated as table‑specific (e.g. an identifying field),
    while any remaining columns are added to the Base.
    """
    # Resolve paths and normalized names.
    folder_path, module_path, version, resource_name = resolve_base_path(name, module)
    base, file_name, class_name = normalize_resource_names(resource_name, "model")

    # Parse columns into a list of tuples: (field_name, field_type)
    columns_list = []
    if columns:
        for col in columns.split(","):
            col = col.strip()
            if col:
                parts = col.split(":")
                if len(parts) == 2:
                    field_name = parts[0].strip()
                    field_type = parts[1].strip()
                else:
                    field_name = parts[0].strip()
                    field_type = "str"
                columns_list.append((field_name, field_type))

    # Split columns: first field goes into the table class; the rest go to the Base.
    if columns_list:
        table_fields = [columns_list[0]]
        base_fields = columns_list[1:]
    else:
        table_fields = []
        base_fields = []

    # Helper to generate lines with proper indentation.
    def generate_lines(fields, template):
        lines = ""
        for field_name, field_type in fields:
            lines += template.format(field_name=field_name, field_type=field_type)
        return lines

    # Lines for the Base class (shared fields)
    columns_base_placeholder = (
        generate_lines(base_fields, "    {field_name}: {field_type} = Field(...)\n")
        if base_fields
        else "    # Define base fields here\n"
    )
    # Lines for the table class (table-specific fields)
    columns_placeholder = (
        generate_lines(table_fields, "    {field_name}: {field_type} = Field(...)\n")
        if table_fields
        else "    # Define table-specific fields here\n"
    )
    # For the Create schema: include all fields as required.
    columns_create_placeholder = (
        generate_lines(columns_list, "    {field_name}: {field_type}\n")
        if columns_list
        else "    # Define required fields for creation\n"
    )
    # For the Update schema: include all fields as optional.
    columns_update_placeholder = (
        generate_lines(
            columns_list, "    {field_name}: Optional[{field_type}] = None\n"
        )
        if columns_list
        else "    # Define fields that can be updated\n"
    )

    content = TEMPLATES["model"].format(
        class_name=class_name,
        table_name=base,
        columns_base_placeholder=columns_base_placeholder,
        columns_placeholder=columns_placeholder,
        columns_create_placeholder=columns_create_placeholder,
        columns_update_placeholder=columns_update_placeholder,
    )
    target_path = os.path.join(folder_path, "models", f"{file_name}.py")
    create_file(target_path, content)
    click.secho(f"✅ Model file created at {target_path}", fg="blue")


@click.command(name="make-from-model")
@click.argument("model_name")
@click.option(
    "--module", default="swx_api.app.models", help="Module where the model is defined"
)
@click.pass_context
def make_from_model(ctx: Context, model_name, module):
    """
    Generate controllers, repositories, services, and routes based on an existing model.
    """
    click.echo("DEBUG: Calling load_all_models()")
    load_all_models()

    try:
        mod = importlib.import_module(module)
        click.echo(f"DEBUG: Successfully imported module: {module}")
    except ModuleNotFoundError:
        click.secho(f"Module {module} not found.", fg="red")
        return

    click.echo(f"DEBUG: Attributes in {module} before reloading: {dir(mod)}")
    # Force a reload of the parent module to catch new changes:
    mod = importlib.reload(mod)
    click.echo(f"DEBUG: Attributes in {module} after reload: {dir(mod)}")

    # --- Force reload the specific submodule dynamically based on model_name ---
    _, file_name, _ = normalize_resource_names(model_name, "model")
    submodule_name = module + "." + file_name
    click.echo(f"DEBUG: Derived submodule name: {submodule_name}")
    try:
        sub_mod = importlib.import_module(submodule_name)
        sub_mod = importlib.reload(sub_mod)
        click.echo(f"DEBUG: Successfully reloaded submodule: {submodule_name}")
    except ModuleNotFoundError as e:
        click.echo(f"DEBUG: Could not reload submodule {submodule_name}: {e}")
        from importlib.util import spec_from_file_location, module_from_spec

        folder_path, _, _, _ = resolve_base_path(model_name, module)
        target_model_file = os.path.join(folder_path, "models", f"{file_name}.py")
        click.echo(f"DEBUG: Attempting manual load from file: {target_model_file}")
        try:
            spec = spec_from_file_location(submodule_name, target_model_file)
            if spec is None:
                raise ImportError(
                    f"Cannot create spec for {submodule_name} at {target_model_file}"
                )
            sub_mod = module_from_spec(spec)
            spec.loader.exec_module(sub_mod)
            sys.modules[submodule_name] = sub_mod
            click.echo(
                f"DEBUG: Successfully manually loaded submodule: {submodule_name}"
            )
        except Exception as e2:
            click.echo(f"DEBUG: Manual load failed for {submodule_name}: {e2}")

    # Explicitly attach the model to the parent module if it exists in the submodule.
    if hasattr(sub_mod, model_name):
        setattr(mod, model_name, getattr(sub_mod, model_name))
        click.echo(
            f"DEBUG: Manually attached {model_name} from {submodule_name} to {module}"
        )
    else:
        click.echo(f"DEBUG: {model_name} not found in submodule {submodule_name}")

    # Now try to retrieve the model class from the parent module.
    try:
        model_cls = getattr(mod, model_name)
        click.echo(f"DEBUG: Found model '{model_name}' in {module}.")
    except AttributeError:
        click.secho(f"Model {model_name} not found in module {module}.", fg="red")
        return

    # ... continue with the rest of your command

    extra_schemas = get_extra_schemas(model_name, mod)
    click.echo(f"DEBUG: Extra schemas retrieved: {extra_schemas}")

    # Unpack values from resolve_base_path.
    folder_path, module_path, version, resource_name = resolve_base_path(
        model_name, module
    )
    click.echo(
        f"DEBUG: resolve_base_path returned folder_path: {folder_path}, module_path: {module_path}, version: {version}, resource_name: {resource_name}"
    )

    # Remove trailing "base" from resource_name (case-insensitive)
    if resource_name.lower().endswith("base"):
        resource_name = resource_name[:-4].rstrip("_")
        click.echo(f"DEBUG: Adjusted resource_name to: {resource_name}")

    # Normalize names for each component using our helper.
    base, controller_file, controller_class = normalize_resource_names(
        resource_name, "controller"
    )
    _, model_file, model_class = normalize_resource_names(resource_name, "model")
    base, repository_file, repo_class = normalize_resource_names(
        resource_name, "repository"
    )
    base, service_file, service_class = normalize_resource_names(
        resource_name, "service"
    )

    # ... (rest of your command follows)

    click.echo(
        f"DEBUG: Normalized names:\n  Controller: {controller_file} ({controller_class})\n  Model: {model_file} ({model_class})\n  Repository: {repository_file} ({repo_class})\n  Service: {service_file} ({service_class})"
    )

    extra_controller_methods = ""
    extra_service_methods = ""
    extra_repo_methods = ""
    extra_route_methods = ""
    extra_imports = ""

    for method_name, schema_name in extra_schemas.items():
        method_doc = f"{method_name} for {base} resource."
        extra_imports += f"from {module} import {schema_name}\n"
        click.echo(f"DEBUG: Processing extra schema: {method_name} -> {schema_name}")

        extra_controller_methods += CONTROLLER_METHOD_TEMPLATE.format(
            method_name=method_name,
            schema_name=schema_name,
            name_lower=base,
            service_class=service_class,
        )

        extra_service_methods += METHOD_TEMPLATE.format(
            method_name=method_name,
            schema_name=schema_name,
            name_lower=base,
            repo_class=repo_class,
        )

        extra_repo_methods += REPOSITORY_METHOD_TEMPLATE.format(
            method_name=method_name,
            schema_name=schema_name,
            name_lower=base,
            model_class=model_class,
        )

        extra_route_methods += ROUTE_METHOD_TEMPLATE.format(
            method_name=method_name,
            schema_name=schema_name,
            method_doc=method_doc,
            name_lower=base,
            model_class=model_class,
            controller_class=controller_class,
        )

    # Generate full file contents using the provided templates.
    controller_content = TEMPLATES["controller"].format(
        columns_comment="# Controller generated based on model fields.",
        controller_class=controller_class,
        name_lower=base,
        module_path=module_path,
        service_file=service_file,
        service_class=service_class,
        model_file=model_file,
        model_class=model_class,
        extra_controller_methods=extra_controller_methods,
    )

    service_content = TEMPLATES["service"].format(
        columns_comment="# Service generated based on repository and model.",
        service_class=service_class,
        name_lower=base,
        repo_file=repository_file,
        repo_class=repo_class,
        model_file=model_file,
        model_class=model_class,
        module_path=module_path,
        extra_imports=extra_imports,
        extra_methods=extra_service_methods,
    )

    repository_content = TEMPLATES["repository"].format(
        columns_comment="# Repository generated based on model fields.",
        module_path=module_path,
        model_file=model_file,
        model_class=model_class,
        repo_class=repo_class,
        name_lower=base,
        extra_repo_methods=extra_repo_methods,
    )

    route_content = TEMPLATES["route"].format(
        columns_comment="# Route generated based on controller and model.",
        controller_file=controller_file,
        controller_class=controller_class,
        name_lower=base,
        model_file=model_file,
        model_class=model_class,
        module_path=module_path,
        version=version or "",
        extra_route_endpoints=extra_route_methods,
    )

    # Determine the correct routes directory (include version if provided)
    if version:
        route_dir = os.path.join(folder_path, "routes", version)
    else:
        route_dir = os.path.join(folder_path, "routes")
    os.makedirs(route_dir, exist_ok=True)
    click.echo(f"DEBUG: Routes directory set to: {route_dir}")

    # Build full file paths.
    controller_path = os.path.join(folder_path, "controllers", f"{controller_file}.py")
    service_path = os.path.join(folder_path, "services", f"{service_file}.py")
    repository_path = os.path.join(folder_path, "repositories", f"{repository_file}.py")
    route_path = os.path.join(route_dir, f"{base}_route.py")

    click.echo(
        f"DEBUG: File paths determined:\n  Controller: {controller_path}\n  Service: {service_path}\n  Repository: {repository_path}\n  Route: {route_path}"
    )

    # Use the helper create_file to write contents only if file does not already exist.
    create_file(controller_path, controller_content)
    create_file(service_path, service_content)
    create_file(repository_path, repository_content)
    create_file(route_path, route_content)

    click.secho(f"✅ Created: {controller_path}", fg="green")
    click.secho(f"✅ Created: {service_path}", fg="green")
    click.secho(f"✅ Created: {repository_path}", fg="green")
    click.secho(f"✅ Created: {route_path}", fg="green")
    click.secho("🚀 Generated resources from model successfully!", fg="green")


# ===================== CLI Group =====================


# -------------------- Optional: Make-Model-From-Existing Command --------------------
@click.command(name="make-model-from-existing")
@click.argument("model_name")
@click.option(
    "--module", default="swx_api.app.models", help="Module where the model is defined"
)
def make_model_from_existing(model_name, module):
    """
    Generate a model file from an existing model definition.
    This is optional if the model already exists.
    """
    folder_path, module_path, version, _ = resolve_base_path(model_name, module)
    _, file_name, class_name = normalize_resource_names(model_name, "model")

    content = (
        f"# This file was generated from the existing model {model_name}\n\n"
        f"from swx_api.core.models.base import Base\n\n"
        f"class {class_name}(Base):\n    pass\n"
    )
    target_path = os.path.join(folder_path, "models", f"{file_name}.py")
    create_file(target_path, content)
    click.secho(f"Model file created at {target_path}", fg="blue")


@click.command(name="migration")
@click.argument("model_name")
@click.option(
    "--existing",
    is_flag=True,
    help="Generate migration for an existing model (using autogenerate).",
)
@click.option(
    "--new", is_flag=True, help="Generate migration for a new model (blank revision)."
)
def migration(model_name, existing, new):
    """
    Generate a migration file for a model using Alembic.

    --existing : Run 'alembic revision --autogenerate' to capture schema changes.
    --new      : Run 'alembic revision' to create a blank migration revision.
    """
    # If neither flag is provided, default to a new (blank) migration.
    if not existing and not new:
        new = True

    # Construct the migration message.
    message = f"Migration for model {model_name}"

    if existing:
        command = ["alembic", "revision", "--autogenerate", "-m", message]
    elif new:
        command = ["alembic", "revision", "-m", message]

    click.echo(f"Running command: {' '.join(command)}")
    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        click.secho(f"❌ Alembic command failed: {result.stderr}", fg="red")
    else:
        click.secho(f"✅ Migration file created:\n{result.stdout}", fg="blue")


@click.command(name="resource")
@click.argument("resource_name")
@click.option(
    "--module", default="swx_api.app.models", help="Module where the model is defined"
)
@click.option(
    "--columns",
    default="",
    help="Comma-separated list of columns for the model (e.g. 'name:str, price:float, description:str')",
)
@click.option(
    "--migration",
    is_flag=True,
    help="Also generate an Alembic migration file for this resource",
)
@click.option(
    "--existing",
    is_flag=True,
    help="Generate migration for an existing model (autogenerate changes).",
)
def resource(resource_name, module, columns, migration, existing):
    """
    Generate a full resource scaffold including:
      - Model file (CRUD style)
      - Controller
      - Service
      - Repository
      - Route
      - (Optionally) Alembic migration file

    Example:
      swx make resource Product --columns "name:str, price:float, description:str" --migration --existing
    """
    ctx = click.get_current_context()
    click.echo("DEBUG: Invoking model command...")
    # ✅ Generate the model file
    ctx.invoke(model, name=resource_name, columns=columns, module=module)

    # === DEBUG: Wait until the model file is detected ===
    folder_path, module_path, version, _ = resolve_base_path(resource_name, module)
    _, file_name, _ = normalize_resource_names(resource_name, "model")
    target_model_file = os.path.join(folder_path, "models", f"{file_name}.py")
    click.echo(f"DEBUG: Expected model file path: {target_model_file}")

    max_wait = 10  # maximum wait time in seconds
    elapsed = 0
    poll_interval = 1  # check every 1 second
    while not os.path.exists(target_model_file) and elapsed < max_wait:
        click.echo(f"DEBUG: Waiting... {elapsed} seconds elapsed.")
        time.sleep(poll_interval)
        elapsed += poll_interval

    if not os.path.exists(target_model_file):
        click.secho(
            f"❌ Model file {target_model_file} was not detected after {max_wait} seconds.",
            fg="red",
        )
        return
    else:
        click.secho(
            f"✅ Model file {target_model_file} detected after {elapsed} seconds.",
            fg="blue",
        )

    # ✅ Increase wait time a bit more to ensure the file system and caches are updated.
    click.echo(
        "DEBUG: Waiting an additional 2 seconds for file system and cache update."
    )
    time.sleep(2)

    # ✅ Invalidate Python's import caches
    click.echo("DEBUG: Invalidating Python import caches.")
    importlib.invalidate_caches()

    # ✅ Ensure the current working directory is in sys.path
    cwd = os.getcwd()
    if cwd not in sys.path:
        click.echo(f"DEBUG: Adding current working directory to sys.path: {cwd}")
        sys.path.insert(0, cwd)

    # ✅ Dynamically load all models so the new model is registered.
    click.echo("DEBUG: Dynamically loading all models...")
    load_all_models()
    from swx_api.core.models.base import Base  # adjust based on your project structure

    click.secho(
        f"DEBUG: Loaded models in metadata: {list(Base.metadata.tables.keys())}",
        fg="green",
    )

    # ✅ Debug: List attributes in the parent module before invoking make_from_model.
    try:
        parent_mod = importlib.import_module(module)
        click.echo(f"DEBUG: Attributes in {module}: {dir(parent_mod)}")
    except Exception as e:
        click.echo(f"DEBUG: Error importing module {module}: {e}")

    # ✅ Generate controllers, services, repositories, and routes from the model.
    click.echo("DEBUG: Invoking make_from_model command...")
    ctx.invoke(make_from_model, model_name=resource_name, module=module)

    if migration:
        click.echo(
            "DEBUG: Migration flag is set. Waiting 2 seconds before generating migration."
        )
        time.sleep(2)  # Ensure DB models are detected before migration
        migration_message = f"Generated CRUD for {resource_name}"
        command = (
            f'alembic revision --autogenerate -m "{migration_message}"'
            if os.name == "nt"
            else f"alembic revision --autogenerate -m '{migration_message}'"
        )
        click.echo(f"DEBUG: Running migration command: {command}")
        os.system(command)
        click.secho(
            "🚀 Migration file created! Run `alembic upgrade head` to apply it.",
            fg="yellow",
        )

    click.secho("🚀 Full resource generated successfully!", fg="green")


# ===================== CLI Group =====================
@click.group()
def make_group():
    """Commands for generating supporting layers based on a model."""
    pass


make_group.add_command(controller)
make_group.add_command(migration)
make_group.add_command(model)
make_group.add_command(make_from_model)
make_group.add_command(make_model_from_existing)
make_group.add_command(resource)
make_group.add_command(repository)
make_group.add_command(route)
make_group.add_command(service)

if __name__ == "__main__":
    make_group()
