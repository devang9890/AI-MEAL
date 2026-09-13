from sqlalchemy import Column, Integer, String, Float, Numeric, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    category = Column(String(100), nullable=False, default="General", index=True)
    unit = Column(String(50), nullable=False, default="100g")  # Baseline unit: 100g or 100ml
    price_per_unit = Column(Numeric(10, 2), nullable=True)  # Standardized as INR (₹) per 100g / 100ml
    calories = Column(Float, nullable=True)  # kcal per 100g
    protein = Column(Float, nullable=True)  # grams per 100g
    carbohydrates = Column(Float, nullable=True)  # grams per 100g
    fat = Column(Float, nullable=True)  # grams per 100g
    fiber = Column(Float, nullable=True, default=0.0)  # grams per 100g
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    recipe_ingredients = relationship("RecipeIngredient", back_populates="ingredient", cascade="all, delete-orphan")

    @property
    def price_per_100g(self) -> float:
        """Helper property exposing price in INR per 100g/100ml."""
        return float(self.price_per_unit) if self.price_per_unit is not None else 0.0
