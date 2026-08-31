from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Meal(Base):
    __tablename__ = "meals"

    id = Column(Integer, primary_key=True, index=True)
    meal_plan_id = Column(Integer, ForeignKey("meal_plans.id"), index=True, nullable=False)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), index=True, nullable=False)
    day = Column(String(20), nullable=False)
    meal_type = Column(String(50), nullable=False)
    servings = Column(Integer, default=1, nullable=False)
    cost = Column(Numeric(10, 2), nullable=True)

    # Relationships
    meal_plan = relationship("MealPlan", back_populates="meals")
    recipe = relationship("Recipe", back_populates="meals")
