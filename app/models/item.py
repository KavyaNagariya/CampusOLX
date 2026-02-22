from sqlalchemy import String, Text, ForeignKey, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timedelta
from typing import Optional

from app.db.base import Base
from app.core.constants import ItemStatus


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(150))
    description: Mapped[str] = mapped_column(Text)
    price: Mapped[int] = mapped_column(Integer)

    status: Mapped[ItemStatus] = mapped_column(
        default=ItemStatus.AVAILABLE
    )
    # ... inside class Item(Base): ...
    
    # Optional[] because a student might want to sell something without a photo
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))

    pickup_location: Mapped[str] = mapped_column(String(255))
    available_till: Mapped[datetime] = mapped_column(DateTime)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    # --- NEW CONCURRENCY & TIMEOUT FIELDS ---
    # Using Optional[] tells SQLAlchemy 2.0 these can be NULL
    reserved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    reserved_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)

    # Relationships
    seller = relationship("User", back_populates="items", foreign_keys=[seller_id])
    category = relationship("Category", back_populates="items")
    reservations = relationship("Reservation", back_populates="item")
    
    # Optional but recommended: A direct relationship to the user who reserved it
    reserved_by = relationship("User", foreign_keys=[reserved_by_id])

    @property
    def is_actually_available(self) -> bool:
        """
        Kill Switch / Lazy Expiry Logic:
        If an item is marked 'RESERVED' but 5 minutes have passed,
        the system treats it as 'AVAILABLE' to prevent marketplace stagnation.
        """
        if self.status == ItemStatus.AVAILABLE:
            return True
        if self.status == ItemStatus.RESERVED and self.reserved_at:
            five_mins_ago = datetime.utcnow() - timedelta(minutes=5)
            # If the reservation time is older than 5 minutes ago, it's available again
            return self.reserved_at < five_mins_ago
        return False
