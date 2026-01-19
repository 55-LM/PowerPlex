from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, Float, String, UniqueConstraint

class Base(DeclarativeBase):
    pass

class Frame(Base):
    __tablename__ = "frames"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    metric: Mapped[str] = mapped_column(String(64), index=True)
    value: Mapped[float] = mapped_column(Float)

    __table_args__ = (UniqueConstraint("year", "metric", name="uq_year_metric"),)

class HeatPoint(Base):
    __tablename__ = "heat_points"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    lon: Mapped[float] = mapped_column(Float)
    lat: Mapped[float] = mapped_column(Float)
    value: Mapped[float] = mapped_column(Float)
