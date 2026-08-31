from sqlalchemy import Column, Integer, String, Text, Float, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"

    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), index=True, nullable=False)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), index=True, nullable=False)
    quantity = Column(Float, nullable=False)

    # Relationships
    recipe = relationship("Recipe", back_populates="recipe_ingredients")
    ingredient = relationship("Ingredient", back_populates="recipe_ingredients")


class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    meal_type = Column(String(50), nullable=True)
    cuisine = Column(String(50), nullable=True)
    servings = Column(Integer, nullable=True)
    estimated_cost = Column(Numeric(10, 2), nullable=True)
    instructions = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    recipe_ingredients = relationship("RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan")
    meals = relationship("Meal", back_populates="recipe", cascade="all, delete-orphan")
