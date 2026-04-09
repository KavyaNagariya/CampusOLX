from sqlalchemy import String, Text, ForeignKey, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
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
    category = relationship("Category", back_populates="items")
    reservations = relationship("Reservation", back_populates="item", cascade="all, delete-orphan", passive_deletes=True)

    seller = relationship(
        "User", 
        foreign_keys=[seller_id], # Explicitly point to seller_id
        back_populates="items_for_sale"
    )
    #Optional
    reserved_by = relationship(
        "User", 
        foreign_keys=[reserved_by_id], 
        back_populates="reserved_items"
    )

    @property
    def is_actually_available(self) -> bool:
        return self.status == ItemStatus.AVAILABLE

    @property
    def seller_name(self) -> str | None:
        return self.seller.name if hasattr(self, 'seller') and self.seller else None

    @property
    def seller_rating(self) -> float | None:
        return self.seller.average_rating if hasattr(self, 'seller') and self.seller else 0.0

    @property
    def seller_rating_count(self) -> int | None:
        return self.seller.rating_count if hasattr(self, 'seller') and self.seller else 0
