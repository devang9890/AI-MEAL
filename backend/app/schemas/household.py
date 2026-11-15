"""Pydantic schemas for Households and Members."""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator


# Enums / controlled value types
GenderType = Literal["male", "female"]
ActivityLevelType = Literal["sedentary", "light", "moderate", "active", "very_active"]
DietaryPreferenceType = Literal["vegetarian", "non_vegetarian", "vegan", "eggitarian"]


class HouseholdBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Name of the household (e.g. 'Sharma Family')")
    weekly_budget: Optional[float] = Field(None, ge=0, description="Weekly grocery budget in ₹")


class HouseholdCreate(HouseholdBase):
    pass


class HouseholdUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    weekly_budget: Optional[float] = Field(None, ge=0)


class HouseholdOut(HouseholdBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime
    member_count: Optional[int] = 0


# ---------------------------------------------------------------------------
# Member Schemas
# ---------------------------------------------------------------------------

class MemberBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Member's full name")
    age: int = Field(..., gt=0, le=125, description="Age in years (must be > 0)")
    gender: GenderType = Field(..., description="Biological sex ('male' or 'female')")
    height_cm: float = Field(..., gt=30, le=260, description="Height in centimeters (must be > 0)")
    weight_kg: float = Field(..., gt=2, le=350, description="Weight in kilograms (must be > 0)")
    activity_level: ActivityLevelType = Field(
        ..., description="'sedentary', 'light', 'moderate', 'active', or 'very_active'"
    )
    dietary_preference: DietaryPreferenceType = Field(
        default="vegetarian",
        description="'vegetarian', 'non_vegetarian', 'vegan', or 'eggitarian'",
    )
    allergies: Optional[str] = Field(None, description="Known allergies (e.g. 'peanuts, lactose')")
    diseases: Optional[str] = Field(None, description="Selected health conditions, stored as comma-separated labels")
    dietary_restrictions: Optional[str] = Field(None, description="Specific restrictions (e.g. 'no onion, no garlic')")

    @field_validator("gender", mode="before")
    @classmethod
    def normalize_gender(cls, v):
        if isinstance(v, str):
            v_clean = v.strip().lower()
            if v_clean in ("male", "female"):
                return v_clean
        raise ValueError("gender must be either 'male' or 'female'")

    @field_validator("activity_level", mode="before")
    @classmethod
    def normalize_activity_level(cls, v):
        if isinstance(v, str):
            v_clean = v.strip().lower()
            if v_clean in ("sedentary", "light", "moderate", "active", "very_active"):
                return v_clean
        raise ValueError("activity_level must be 'sedentary', 'light', 'moderate', 'active', or 'very_active'")

    @field_validator("dietary_preference", mode="before")
    @classmethod
    def normalize_dietary_preference(cls, v):
        if isinstance(v, str):
            v_clean = v.strip().lower()
            if v_clean in ("vegetarian", "non_vegetarian", "vegan", "eggitarian"):
                return v_clean
        raise ValueError("dietary_preference must be 'vegetarian', 'non_vegetarian', 'vegan', or 'eggitarian'")


class MemberCreate(MemberBase):
    pass


class MemberUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    age: Optional[int] = Field(None, gt=0, le=125)
    gender: Optional[GenderType] = None
    height_cm: Optional[float] = Field(None, gt=30, le=260)
    weight_kg: Optional[float] = Field(None, gt=2, le=350)
    activity_level: Optional[ActivityLevelType] = None
    dietary_preference: Optional[DietaryPreferenceType] = None
    allergies: Optional[str] = None
    diseases: Optional[str] = None
    dietary_restrictions: Optional[str] = None

    @field_validator("gender", mode="before")
    @classmethod
    def normalize_gender(cls, v):
        if v is not None and isinstance(v, str):
            v_clean = v.strip().lower()
            if v_clean in ("male", "female"):
                return v_clean
            raise ValueError("gender must be either 'male' or 'female'")
        return v

    @field_validator("activity_level", mode="before")
    @classmethod
    def normalize_activity_level(cls, v):
        if v is not None and isinstance(v, str):
            v_clean = v.strip().lower()
            if v_clean in ("sedentary", "light", "moderate", "active", "very_active"):
                return v_clean
            raise ValueError("activity_level must be 'sedentary', 'light', 'moderate', 'active', or 'very_active'")
        return v

    @field_validator("dietary_preference", mode="before")
    @classmethod
    def normalize_dietary_preference(cls, v):
        if v is not None and isinstance(v, str):
            v_clean = v.strip().lower()
            if v_clean in ("vegetarian", "non_vegetarian", "vegan", "eggitarian"):
                return v_clean
            raise ValueError("dietary_preference must be 'vegetarian', 'non_vegetarian', 'vegan', or 'eggitarian'")
        return v


class MemberOut(MemberBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    household_id: int
    created_at: datetime
    updated_at: datetime
    has_nutrition_target: Optional[bool] = False
