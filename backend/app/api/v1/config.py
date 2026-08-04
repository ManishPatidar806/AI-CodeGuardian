from fastapi import APIRouter, HTTPException

from app.core.config_manager import GuardianConfig, config_manager

router = APIRouter(prefix="/config", tags=["Configuration"])


@router.get("", summary="Get Runtime Configuration")
def get_configuration() -> GuardianConfig:
    """Retrieve current runtime configuration settings for AI CodeGuardian."""
    try:
        return config_manager.get_config()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve configuration: {exc}",
        ) from exc


@router.put("", summary="Update Runtime Configuration")
def update_configuration(new_config: GuardianConfig) -> GuardianConfig:
    """Update runtime configuration settings for AI CodeGuardian.

    Args:
        new_config: Validated GuardianConfig update payload.

    Returns:
        Updated GuardianConfig object.
    """
    try:
        return config_manager.update_config(new_config)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to update configuration: {exc}",
        ) from exc
