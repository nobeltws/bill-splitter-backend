import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Session(Base):
    __tablename__ = "sessions"
    __table_args__ = (
        CheckConstraint("participant_count > 0", name="ck_sessions_participant_count_positive"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    host_paynow_id: Mapped[str] = mapped_column(String(50))
    tax: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    service_charge: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    discount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    participant_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    items: Mapped[list["Item"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    claims: Mapped[list["Claim"]] = relationship(back_populates="session", cascade="all, delete-orphan")
