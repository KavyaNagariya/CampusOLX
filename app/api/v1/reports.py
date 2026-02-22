from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.report import ReportCreate, ReportResponse
from app.services.report_service import create_report

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("/", response_model=ReportResponse)
async def report_item(
    report_in: ReportCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await create_report(
        db, report_in, current_user.id
    )

