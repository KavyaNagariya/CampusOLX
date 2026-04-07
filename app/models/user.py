

from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.db.base import Base
from app.core.constants import UserRole


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))

    role: Mapped[UserRole] = mapped_column(default=UserRole.USER)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    items_for_sale = relationship(
        "Item", 
        foreign_keys="[Item.seller_id]", 
        back_populates="seller"
    )

    reserved_items = relationship(
        "Item", 
        foreign_keys="[Item.reserved_by_id]", 
        back_populates="reserved_by"
    )

    ratings_received = relationship(
        "Rating",
        foreign_keys="[Rating.rated_user_id]",
        backref="rated_user",
        passive_deletes=True
    )

    @property
    def average_rating(self) -> float:
        if not self.ratings_received:
            return 0.0
        return sum(r.score for r in self.ratings_received) / len(self.ratings_received)

    @property
    def rating_count(self) -> int:
        return len(self.ratings_received) if self.ratings_received else 0
