from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import Report
from app.schemas.report import ReportCreate


async def create_report(
    db: AsyncSession, report_in: ReportCreate, reporter_id: int
) -> Report:
    report = Report(
        reporter_id=reporter_id,
        item_id=report_in.item_id,
        reason=report_in.reason,
        description=report_in.description,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report
