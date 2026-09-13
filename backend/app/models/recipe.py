from sqlalchemy import Column, Integer, String, Text, Float, Numeric, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"

    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id", ondelete="CASCADE"), index=True, nullable=False)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id", ondelete="CASCADE"), index=True, nullable=False)
    quantity = Column(Float, nullable=False)  # quantity in grams (g) or milliliters (ml)
    unit = Column(String(50), nullable=False, default="g")  # 'g', 'ml', 'piece', 'tsp', 'tbsp'

    # Relationships
    recipe = relationship("Recipe", back_populates="recipe_ingredients")
    ingredient = relationship("Ingredient", back_populates="recipe_ingredients")


class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    meal_type = Column(String(50), nullable=True, index=True)  # 'breakfast', 'lunch', 'dinner', 'snack'
    cuisine = Column(String(50), nullable=True, index=True)  # 'North Indian', 'South Indian', etc.
    servings = Column(Integer, nullable=False, default=2)
    preparation_time = Column(Integer, nullable=True, default=15)  # minutes
    cooking_time = Column(Integer, nullable=True, default=20)  # minutes
    dietary_tags = Column(JSON, nullable=True, default=list)  # e.g. ["vegetarian", "high_protein", "lunch"]
    estimated_cost = Column(Numeric(10, 2), nullable=True)  # in INR (₹)
    instructions = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    recipe_ingredients = relationship("RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan")
    meals = relationship("Meal", back_populates="recipe", cascade="all, delete-orphan")
