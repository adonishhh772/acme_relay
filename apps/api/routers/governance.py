from typing import Annotated, Any

from fastapi import APIRouter, Depends

from auth.dependencies import CurrentUser, require_permission
from services.prompt_service import prompt_service

router = APIRouter(prefix="/api/governance", tags=["governance"])


@router.get("/prompts")
async def prompt_versions(
    user: Annotated[CurrentUser, Depends(require_permission("approve_next_action"))],
) -> dict[str, Any]:
    _ = user
    raw = prompt_service.load_raw()
    return {
        "active": {
            "name": raw["name"],
            "version": raw["version"],
            "labels": raw.get("labels") or [],
            "description": raw.get("description"),
        }
    }
