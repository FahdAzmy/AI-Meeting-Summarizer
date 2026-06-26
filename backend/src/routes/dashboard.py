from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.controllers.dashboard_controller import get_hr_dashboard, get_tl_dashboard
from src.helpers.db import get_db
from src.helpers.security import get_current_user
from src.models.user import User, UserRole

dashboard_router = APIRouter(tags=["dashboard"])


def _role_value(role: str | UserRole) -> str:
    return role.value if isinstance(role, UserRole) else str(role)


@dashboard_router.get("/dashboard")
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if _role_value(current_user.role) == UserRole.HR.value:
        return await get_hr_dashboard(db, current_user.company_id)
    return await get_tl_dashboard(db, current_user)
