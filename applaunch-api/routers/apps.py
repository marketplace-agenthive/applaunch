# applaunch-api/routers/apps.py
"""CRUD endpoints for app profiles."""

from fastapi import APIRouter, Depends, HTTPException, status
from models.app import AppCreate, AppUpdate, AppResponse
from routers.auth import AuthenticatedUser, get_current_user
from db.supabase_client import get_supabase
from typing import List

router = APIRouter(prefix="/apps", tags=["apps"])


@router.post("", response_model=AppResponse, status_code=status.HTTP_201_CREATED)
async def create_app(
    body: AppCreate,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Create a new app profile for the authenticated user."""
    supabase = get_supabase()
    try:
        result = supabase.table("apps").insert({
            "user_id": user.id,
            "app_name": body.app_name,
            "package_name": body.package_name,
            "framework": body.framework.value,
            "description": body.description,
            "icon_url": body.icon_url,
        }).execute()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": str(exc), "code": "APP_CREATE_FAILED"},
        )
    return result.data[0]


@router.get("", response_model=List[AppResponse])
async def list_apps(user: AuthenticatedUser = Depends(get_current_user)):
    """List all app profiles belonging to the authenticated user."""
    supabase = get_supabase()
    result = supabase.table("apps").select("*").eq("user_id", user.id).execute()
    return result.data


@router.get("/{app_id}", response_model=AppResponse)
async def get_app(
    app_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Fetch a single app profile by ID (must belong to user)."""
    supabase = get_supabase()
    result = (
        supabase.table("apps")
        .select("*")
        .eq("id", app_id)
        .eq("user_id", user.id)
        .maybe_single()
        .execute()
    )
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "App not found", "code": "APP_NOT_FOUND"},
        )
    return result.data


@router.patch("/{app_id}", response_model=AppResponse)
async def update_app(
    app_id: str,
    body: AppUpdate,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Update mutable fields on an app profile."""
    supabase = get_supabase()
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "No fields to update", "code": "EMPTY_UPDATE"},
        )
    result = (
        supabase.table("apps")
        .update(updates)
        .eq("id", app_id)
        .eq("user_id", user.id)
        .execute()
    )
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "App not found", "code": "APP_NOT_FOUND"},
        )
    return result.data[0]


@router.delete("/{app_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_app(
    app_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Delete an app profile and all associated records."""
    supabase = get_supabase()
    supabase.table("apps").delete().eq("id", app_id).eq("user_id", user.id).execute()
