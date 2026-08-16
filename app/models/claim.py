import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), index=True
    )
    item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("items.id", ondelete="CASCADE"), index=True
    )
    participant_name: Mapped[str] = mapped_column(String(100))
    quantity: Mapped[int] = mapped_column(Integer)

    item: Mapped["Item"] = relationship()
    session: Mapped["Session"] = relationship(back_populates="claims")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_claims_quantity_positive"),
        UniqueConstraint("session_id", "item_id", "participant_name", name="uq_claims_session_item_participant"),
    )
