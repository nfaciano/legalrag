from fastapi import APIRouter, HTTPException, Depends
import logging

from app.models import UserSettings, UserSettingsResponse
from app.auth import get_current_user
from app.user_settings_db import get_user_settings, save_user_settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/user-settings", response_model=UserSettingsResponse)
async def get_user_settings_endpoint(
    user_id: str = Depends(get_current_user)
):
    """Get user settings (return address, signature, etc.)."""
    logger.info(f"Getting settings for user {user_id}")

    try:
        settings = get_user_settings(user_id)

        if not settings:
            settings = {
                "return_address_name": "",
                "return_address_line1": "",
                "return_address_line2": "",
                "return_address_city_state_zip": "",
                "signature_name": "",
                "initials": "",
                "closing": "Very truly yours,"
            }

        return UserSettingsResponse(settings=UserSettings(**settings))

    except Exception as e:
        logger.error(f"Error getting user settings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting settings: {str(e)}")


@router.put("/user-settings", response_model=UserSettingsResponse)
async def update_user_settings_endpoint(
    settings: UserSettings,
    user_id: str = Depends(get_current_user)
):
    """Update user settings."""
    logger.info(f"Updating settings for user {user_id}")

    try:
        settings_dict = settings.model_dump()
        saved_settings = save_user_settings(user_id, settings_dict)

        return UserSettingsResponse(settings=UserSettings(**saved_settings))

    except Exception as e:
        logger.error(f"Error updating user settings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error updating settings: {str(e)}")
