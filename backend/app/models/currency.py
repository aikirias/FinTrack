from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class Currency(Base):
    __tablename__ = "currencies"

    code: Mapped[str] = mapped_column(String(3), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    symbol: Mapped[str | None] = mapped_column(String(8), nullable=True)
