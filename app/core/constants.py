from enum import Enum


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


class ItemStatus(str, Enum):
    AVAILABLE = "available"
    PENDING = "pending"
    RESERVED = "reserved"
    SOLD = "sold"


class ReservationStatus(str, Enum):
    REQUESTED = "requested"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class ReportReason(str, Enum):
    FRAUD = "fraud"
    ILLEGAL_ITEM = "illegal_item"
    MISLEADING_INFO = "misleading_info"
    SPAM = "spam"


# Categories you listed
DEFAULT_CATEGORIES = [
    "Books & Notes",
    "Electronics",
    "Cycles & Transport",
    "Lab Equipment",
    "Clothes & Accessories",
    "Furniture",
    "Miscellaneous",
]
