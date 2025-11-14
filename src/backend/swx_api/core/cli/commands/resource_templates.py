# swx_api/core/templates/resource_templates.py

# -------------------- Method Snippets for Extra Actions --------------------
METHOD_TEMPLATE = """
    @staticmethod
    def {method_name}(db: SessionDep, id: uuid.UUID, data: {schema_name}):
        \"\"\"Service layer: {method_name} for {name_lower} resource.\"\"\"
        return {repo_class}.{method_name}(db, id, data)
"""

CONTROLLER_METHOD_TEMPLATE = """
    @staticmethod
    def {method_name}(request: Request, id: uuid.UUID, data: {schema_name}, db: SessionDep):
        \"\"\"Controller: {method_name} for {name_lower} resource.\"\"\"
        return {service_class}.{method_name}(db, id, data)
"""

REPOSITORY_METHOD_TEMPLATE = """
    @staticmethod
    def {method_name}(db: SessionDep, id: uuid.UUID, data: {schema_name}):
        \"\"\"Repository method: {method_name} for {name_lower} resource.\"\"\"
        obj = db.get({model_class}, id)
        if not obj:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, key, value)
        db.commit()
        db.refresh(obj)
        return obj
"""

ROUTE_METHOD_TEMPLATE = """
@router.put("/{{id}}/{method_name}", response_model={model_class}Public,
            summary="{method_name} for {name_lower}",
            description="{method_doc}")
def {method_name}(request: Request, id: uuid.UUID, data: {schema_name}, db: SessionDep):
    return {controller_class}.{method_name}(request, id, data, db)
"""

# ===================== Templates =====================

TEMPLATES = {
    "controller": """{columns_comment}

from swx_api.core.database.db import SessionDep
from {module_path}.services.{service_file} import {service_class}
from {module_path}.models.{model_file} import {model_class}Create, {model_class}Update, {model_class}Public
from fastapi import HTTPException, Request
from swx_api.core.middleware.logging_middleware import logger
from swx_api.core.utils.language_helper import translate
import uuid

class {controller_class}:
    @staticmethod
    def retrieve_all_{name_lower}_resources(request: Request, db: SessionDep, skip: int = 0, limit: int = 100):
        \"\"\"Retrieve all {name_lower} resources with pagination.\"\"\"
        try:
            return {service_class}.retrieve_all_{name_lower}_resources(db, skip=skip, limit=limit)
        except Exception as e:
            logger.error("Error in retrieve_all_{name_lower}_resources: %s", e)
            raise HTTPException(status_code=500, detail="Internal Server Error")

    @staticmethod
    def retrieve_{name_lower}_by_id(request: Request, id: uuid.UUID, db: SessionDep):
        \"\"\"Retrieve a single {name_lower} resource by its ID.\"\"\" 
        item = {service_class}.retrieve_{name_lower}_by_id(db, id)
        if not item:
            raise HTTPException(status_code=404, detail=translate(request, f"{model_file}.not_found"))
        return item

    @staticmethod
    def create_new_{name_lower}(request: Request, data: {model_class}Create, db: SessionDep):
        \"\"\"Create a new {name_lower} resource.\"\"\" 
        try:
            return {service_class}.create_new_{name_lower}(db, data)
        except Exception as e:
            logger.error("Error in create_new_{name_lower}: %s", e)
            raise HTTPException(status_code=500, detail="Internal Server Error")

    @staticmethod
    def update_existing_{name_lower}(request: Request, id: uuid.UUID, data: {model_class}Update, db: SessionDep):
        \"\"\"Update an existing {name_lower} resource.\"\"\" 
        item = {service_class}.update_existing_{name_lower}(db, id, data)
        if not item:
            raise HTTPException(status_code=404, detail=translate(request, f"{model_file}.not_found"))
        return item

    @staticmethod
    def delete_existing_{name_lower}(request: Request, id: uuid.UUID, db: SessionDep):
        \"\"\"Delete an existing {name_lower} resource.\"\"\" 
        success = {service_class}.delete_existing_{name_lower}(db, id)
        if not success:
            raise HTTPException(status_code=404, detail=translate(request, f"{model_file}.not_found"))
        return None
{extra_controller_methods}
""",
    "route": """{columns_comment}

import uuid
from fastapi import APIRouter, Request, Depends, Query
from swx_api.core.database.db import SessionDep
from {module_path}.controllers.{controller_file} import {controller_class}
from {module_path}.models.{model_file} import {model_class}Create, {model_class}Update, {model_class}Public

router = APIRouter(prefix="/{model_file}")

@router.get("/", response_model=list[{model_class}Public],
            summary="Get all {name_lower}",
            description="Retrieve all {name_lower} resources with optional pagination")
def get_all(request: Request, db: SessionDep,
            skip: int = Query(0, description="Number of items to skip"),
            limit: int = Query(100, description="Maximum number of items to return")):
    return {controller_class}.retrieve_all_{name_lower}_resources(request, db, skip=skip, limit=limit)

@router.get("/{{id}}", response_model={model_class}Public,
            summary="Get {name_lower} by ID",
            description="Retrieve a single {name_lower} resource by its unique identifier")
def get_by_id(request: Request, id: uuid.UUID, db: SessionDep):
    return {controller_class}.retrieve_{name_lower}_by_id(request, id, db)

@router.post("/", response_model={model_class}Public, status_code=201,
             summary="Create new {name_lower}",
             description="Create a new {name_lower} resource")
def create(request: Request, data: {model_class}Create, db: SessionDep):
    return {controller_class}.create_new_{name_lower}(request, data, db)

@router.put("/{{id}}", response_model={model_class}Public,
            summary="Update {name_lower}",
            description="Update an existing {name_lower} resource by ID")
def update(request: Request, id: uuid.UUID, data: {model_class}Update, db: SessionDep):
    return {controller_class}.update_existing_{name_lower}(request, id, data, db)

@router.delete("/{{id}}", status_code=204,
               summary="Delete {name_lower}",
               description="Delete an existing {name_lower} resource by ID")
def delete(request: Request, id: uuid.UUID, db: SessionDep):
    return {controller_class}.delete_existing_{name_lower}(request, id, db)
{extra_route_endpoints}
""",
    "repository": """{columns_comment}

import uuid
from sqlmodel import select
from swx_api.core.database.db import SessionDep
from {module_path}.models.{model_file} import {model_class}, {model_class}Create, {model_class}Update

class {repo_class}:
    @staticmethod
    def retrieve_all_{name_lower}_resources(db: SessionDep, skip: int = 0, limit: int = 100):
        \"\"\"Retrieve all {name_lower} resources with pagination.\"\"\" 
        query = select({model_class}).offset(skip).limit(limit)
        return db.exec(query).all()

    @staticmethod
    def retrieve_{name_lower}_by_id(db: SessionDep, id: uuid.UUID):
        \"\"\"Retrieve a single {name_lower} resource by ID.\"\"\" 
        return db.get({model_class}, id)

    @staticmethod
    def create_new_{name_lower}(db: SessionDep, data: {model_class}Create):
        \"\"\"Create a new {name_lower} resource in the database.\"\"\" 
        obj = {model_class}(**data.model_dump())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def update_existing_{name_lower}(db: SessionDep, id: uuid.UUID, data: {model_class}Update):
        \"\"\"Update an existing {name_lower} resource.\"\"\" 
        obj = db.get({model_class}, id)
        if not obj:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, key, value)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def delete_existing_{name_lower}(db: SessionDep, id: uuid.UUID):
        \"\"\"Delete an existing {name_lower} resource.\"\"\" 
        obj = db.get({model_class}, id)
        if not obj:
            return False
        db.delete(obj)
        db.commit()
        return True
{extra_repo_methods}
""",
    "service": """{columns_comment}

import uuid
from swx_api.core.database.db import SessionDep
from {module_path}.repositories.{repo_file} import {repo_class}
from {module_path}.models.{model_file} import {model_class}Create, {model_class}Update
{extra_imports}

class {service_class}:
    @staticmethod
    def retrieve_all_{name_lower}_resources(db: SessionDep, skip: int = 0, limit: int = 100):
        \"\"\"Service layer: retrieve all {name_lower} resources.\"\"\" 
        return {repo_class}.retrieve_all_{name_lower}_resources(db, skip=skip, limit=limit)

    @staticmethod
    def retrieve_{name_lower}_by_id(db: SessionDep, id: uuid.UUID):
        \"\"\"Service layer: retrieve a single {name_lower} resource by ID.\"\"\" 
        return {repo_class}.retrieve_{name_lower}_by_id(db, id)

    @staticmethod
    def create_new_{name_lower}(db: SessionDep, data: {model_class}Create):
        \"\"\"Service layer: create a new {name_lower} resource.\"\"\" 
        return {repo_class}.create_new_{name_lower}(db, data)

    @staticmethod
    def update_existing_{name_lower}(db: SessionDep, id: uuid.UUID, data: {model_class}Update):
        \"\"\"Service layer: update an existing {name_lower} resource.\"\"\" 
        return {repo_class}.update_existing_{name_lower}(db, id, data)

    @staticmethod
    def delete_existing_{name_lower}(db: SessionDep, id: uuid.UUID):
        \"\"\"Service layer: delete an existing {name_lower} resource.\"\"\" 
        return {repo_class}.delete_existing_{name_lower}(db, id)

{extra_methods}
""",
    "model": """\
# This model was generated using swx CLI.

from typing import Optional
from sqlmodel import SQLModel, Field
from swx_api.core.models.base import Base

class {class_name}Base(Base):
{columns_base_placeholder}

class {class_name}({class_name}Base, table=True):
    __tablename__ = "{table_name}"
    __table_args__ = {{"extend_existing": True}}

    id: Optional[int] = Field(default=None, primary_key=True)
{columns_placeholder}

class {class_name}Create(SQLModel):
{columns_create_placeholder}

class {class_name}Update(SQLModel):
{columns_update_placeholder}

class {class_name}Public({class_name}):
    pass
""",
}