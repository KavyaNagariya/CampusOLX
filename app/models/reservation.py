from sqlalchemy import ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.db.base import Base
from app.core.constants import ReservationStatus


class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(primary_key=True)

    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"))
    buyer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    status: Mapped[ReservationStatus] = mapped_column(
        default=ReservationStatus.REQUESTED
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    item = relationship("Item", back_populates="reservations")
