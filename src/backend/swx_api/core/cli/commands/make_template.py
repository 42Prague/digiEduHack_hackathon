# # templates.py
#
#
# class TemplateManager:
#     TEMPLATES = None
#     DYNAMIC_TEMPLATES = None
#
#     @staticmethod
#     def get_template(template_name):
#         return TemplateManager.TEMPLATES.get(template_name, None)
#
#     @staticmethod
#     def get_dynamic_template(template_name):
#         return TemplateManager.DYNAMIC_TEMPLATES.get(template_name, None)
#
#
#     @staticmethod
#     def get_service_method_template(method_name, schema_name, name_lower, repo_class):
#         return TemplateManager.TEMPLATES["method"].format(
#             method_name=method_name, schema_name=schema_name, name_lower=name_lower, repo_class=repo_class
#         )
#
#
#     @staticmethod
#     def get_controller_method_template(method_name, schema_name, name_lower, service_class):
#         return TemplateManager.TEMPLATES["controller_method"].format(
#             method_name=method_name, schema_name=schema_name, name_lower=name_lower, service_class=service_class
#         )
#
#
#     @staticmethod
#     def get_repository_method_template(method_name, schema_name, name_lower, model_class):
#         return TemplateManager.TEMPLATES["repository_method"].format(
#             method_name=method_name, schema_name=schema_name, name_lower=name_lower, model_class=model_class
#         )
#
#
#     @staticmethod
#     def get_route_method_template(method_name, schema_name, method_doc, name_lower, model_class, controller_class):
#         return TemplateManager.TEMPLATES["route_method"].format(
#             method_name=method_name, schema_name=schema_name, method_doc=method_doc,
#             name_lower=name_lower, model_class=model_class, controller_class=controller_class
#     )
class TemplateManager:
    """
    Manages and provides templates for routes, controllers, services, and repositories.
    Ensures REST API convention for CRUD while dynamically generating additional methods.
    """

    ROUTE_TEMPLATE = """{columns_comment}

import uuid
from fastapi import APIRouter, Request, Depends, Query
from swx_api.core.database.db import SessionDep
from {module_path}.controllers.{controller_file} import {controller_class}
from {module_path}.models.{model_file} import {model_class}Create, {model_class}Update, {model_class}Public

router = APIRouter(prefix="/{name_lower}")

{crud_methods}

{extra_methods}
"""

    ROUTE_METHOD_TEMPLATE = """
@router.{http_method}("{route_path}", response_model={response_model},
            summary="{summary}",
            description="{description}")
def {method_name}(request: Request, {params}, db: SessionDep):
    return {controller_class}.{controller_method}(request, {params_call}, db)
"""

    @staticmethod
    def get_route_template(
        columns_comment,
        module_path,
        controller_file,
        controller_class,
        model_file,
        model_class,
        name_lower,
        crud_methods,
        extra_methods,
    ):
        """
        Generates the full route file template dynamically.
        """
        return TemplateManager.ROUTE_TEMPLATE.format(
            columns_comment=columns_comment,
            module_path=module_path,
            controller_file=controller_file,
            controller_class=controller_class,
            model_file=model_file,
            model_class=model_class,
            name_lower=name_lower,
            crud_methods=crud_methods,
            extra_methods=extra_methods,
        )

    @staticmethod
    def generate_route_method(
        http_method,
        route_path,
        method_name,
        params,
        response_model,
        controller_class,
        controller_method,
        description,
        summary,
    ):
        """
        Generates an individual route method dynamically.
        """
        params_call = (
            ", ".join(param.split(":")[0] for param in params.split(", "))
            if params
            else ""
        )
        return TemplateManager.ROUTE_METHOD_TEMPLATE.format(
            http_method=http_method,
            route_path=route_path,
            method_name=method_name,
            params=params,
            response_model=response_model,
            controller_class=controller_class,
            controller_method=controller_method,
            params_call=params_call,
            description=description,
            summary=summary,
        )

    @staticmethod
    def generate_crud_routes(name_lower, model_class, controller_class):
        """
        Generates standard CRUD API routes following RESTful naming conventions.
        """
        crud_methods = ""

        # List all resources (GET /)
        crud_methods += TemplateManager.generate_route_method(
            http_method="get",
            route_path="/",
            method_name=f"get_all_{name_lower}",
            params="request: Request, skip: int = Query(0), limit: int = Query(100)",
            response_model=f"list[{model_class}Public]",
            controller_class=controller_class,
            controller_method=f"retrieve_all_{name_lower}_resources",
            summary=f"Retrieve all {name_lower} resources",
            description=f"Fetch all {name_lower} resources with optional pagination",
        )

        # Get a resource by ID (GET /{id})
        crud_methods += TemplateManager.generate_route_method(
            http_method="get",
            route_path="/{id}",
            method_name=f"get_{name_lower}_by_id",
            params="request: Request, id: uuid.UUID",
            response_model=f"{model_class}Public",
            controller_class=controller_class,
            controller_method=f"retrieve_{name_lower}_by_id",
            summary=f"Retrieve {name_lower} by ID",
            description=f"Fetch a {name_lower} resource using its unique identifier",
        )

        # Create a new resource (POST /)
        crud_methods += TemplateManager.generate_route_method(
            http_method="post",
            route_path="/",
            method_name=f"create_{name_lower}",
            params="request: Request, data: {model_class}Create",
            response_model=f"{model_class}Public",
            controller_class=controller_class,
            controller_method=f"create_new_{name_lower}",
            summary=f"Create a new {name_lower}",
            description=f"Add a new {name_lower} resource to the system",
        )

        # Update an existing resource (PUT /{id})
        crud_methods += TemplateManager.generate_route_method(
            http_method="put",
            route_path="/{id}",
            method_name=f"update_{name_lower}",
            params="request: Request, id: uuid.UUID, data: {model_class}Update",
            response_model=f"{model_class}Public",
            controller_class=controller_class,
            controller_method=f"update_existing_{name_lower}",
            summary=f"Update {name_lower}",
            description=f"Modify an existing {name_lower} resource by providing updated data",
        )

        # Delete a resource (DELETE /{id})
        crud_methods += TemplateManager.generate_route_method(
            http_method="delete",
            route_path="/{id}",
            method_name=f"delete_{name_lower}",
            params="request: Request, id: uuid.UUID",
            response_model="None",
            controller_class=controller_class,
            controller_method=f"delete_existing_{name_lower}",
            summary=f"Delete {name_lower}",
            description=f"Remove a {name_lower} resource from the system using its ID",
        )

        return crud_methods

    @staticmethod
    def generate_extra_routes(
        controller_methods, name_lower, model_class, controller_class
    ):
        """
        Generates additional routes based on custom controller methods.
        """
        extra_methods = ""
        for method_name, schema_name in controller_methods.items():
            http_method = (
                "post"  # Defaulting to POST for extra methods, can be customized
            )
            route_path = f"/{method_name}"
            params = f"request: Request, data: {schema_name}"
            response_model = f"{model_class}Public"
            controller_method = method_name
            summary = f"{method_name} for {name_lower}"
            description = f"{method_name} operation for {name_lower}"

            extra_methods += TemplateManager.generate_route_method(
                http_method=http_method,
                route_path=route_path,
                method_name=method_name,
                params=params,
                response_model=response_model,
                controller_class=controller_class,
                controller_method=controller_method,
                summary=summary,
                description=description,
            )

        return extra_methods
