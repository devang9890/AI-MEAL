from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class NutritionTarget(Base):
    __tablename__ = "nutrition_targets"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id", ondelete="CASCADE"), index=True, nullable=False)
    daily_calories = Column(Float, nullable=False)
    daily_protein_g = Column(Float, nullable=False)
    daily_carbs_g = Column(Float, nullable=False)
    daily_fat_g = Column(Float, nullable=False)
    daily_fiber_g = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    member = relationship("Member", back_populates="nutrition_targets")

    # Compatibility properties
    @property
    def calories(self) -> float:
        return self.daily_calories

    @property
    def protein(self) -> float:
        return self.daily_protein_g

    @property
    def carbohydrates(self) -> float:
        return self.daily_carbs_g

    @property
    def fat(self) -> float:
        return self.daily_fat_g

    @property
    def fiber(self) -> float:
        return self.daily_fiber_g

