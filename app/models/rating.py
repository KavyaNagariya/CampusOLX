from sqlalchemy import ForeignKey, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from app.db.base import Base


class Rating(Base):
    __tablename__ = "ratings"

    id: Mapped[int] = mapped_column(primary_key=True)

    rater_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    rated_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    score: Mapped[int] = mapped_column(Integer)  # 1 to 5
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

