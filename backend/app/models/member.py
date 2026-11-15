from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    household_id = Column(Integer, ForeignKey("households.id", ondelete="CASCADE"), index=True, nullable=False)
    name = Column(String(255), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(50), nullable=False)  # 'male', 'female'
    height_cm = Column(Float, nullable=False)
    weight_kg = Column(Float, nullable=False)
    activity_level = Column(String(50), nullable=False)  # 'sedentary', 'light', 'moderate', 'active', 'very_active'
    dietary_preference = Column(String(50), nullable=False, default="vegetarian")  # 'vegetarian', 'non_vegetarian', 'vegan', 'eggitarian'
    allergies = Column(Text, nullable=True)
    # Comma-separated selected conditions from the curated health catalog.
    diseases = Column(Text, nullable=True)
    dietary_restrictions = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    household = relationship("Household", back_populates="members")
    nutrition_targets = relationship("NutritionTarget", back_populates="member", cascade="all, delete-orphan")

    # Compatibility properties
    @property
    def height(self) -> float:
        return self.height_cm

    @property
    def weight(self) -> float:
        return self.weight_kg

    @property
    def diet_type(self) -> str:
        return self.dietary_preference

