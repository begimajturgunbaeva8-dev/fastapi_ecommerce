from datetime import datetime
from sqlalchemy import Integer, String, ForeignKey, Boolean, DateTime
from app.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import func


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    comment: Mapped[str | None] = mapped_column(String(500), nullable=True)
    comment_date: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    grade: Mapped[int] = mapped_column(Integer, nullable=False)  # Оценка от 1 до 5
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)