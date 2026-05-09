# applaunch-api/models/app.py
"""Pydantic schemas for App profiles."""

from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime
from enum import Enum


class Framework(str, Enum):
    react_native = "react_native"
    expo = "expo"
    flutter = "flutter"


class AppCreate(BaseModel):
    app_name: str
    package_name: str
    framework: Framework
    description: Optional[str] = None
    icon_url: Optional[str] = None

    @field_validator("package_name")
    @classmethod
    def validate_package_name(cls, v: str) -> str:
        parts = v.split(".")
        if len(parts) < 2:
            raise ValueError("package_name must be in reverse-domain format (e.g. com.example.app)")
        return v.lower()


class AppUpdate(BaseModel):
    app_name: Optional[str] = None
    description: Optional[str] = None
    icon_url: Optional[str] = None


class AppResponse(BaseModel):
    id: str
    user_id: str
    app_name: str
    package_name: str
    framework: Framework
    description: Optional[str]
    icon_url: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
