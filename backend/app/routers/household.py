"""Household, Member, and Nutrition Target API Routes."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.household import Household
from app.models.member import Member
from app.models.nutrition import NutritionTarget
from app.schemas.household import (
    HouseholdCreate,
    HouseholdUpdate,
    HouseholdOut,
    MemberCreate,
    MemberUpdate,
    MemberOut,
)
from app.schemas.nutrition import NutritionCalculationResult, NutritionTargetOut
from app.services.nutrition_service import (
    calculate_nutrition_for_member,
    save_or_update_nutrition_target,
)

router = APIRouter(prefix="/api", tags=["Households & Members"])


# ---------------------------------------------------------------------------
# Authorization Helpers
# ---------------------------------------------------------------------------

def _get_user_household_or_404(household_id: int, user: User, db: Session) -> Household:
    """Retrieve a household owned by current_user or raise 404."""
    household = (
        db.query(Household)
        .filter(Household.id == household_id, Household.owner_id == user.id)
        .first()
    )
    if not household:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Household with ID {household_id} not found or you do not have permission to access it.",
        )
    return household


def _get_user_member_or_404(
    household_id: int, member_id: int, user: User, db: Session
) -> Member:
    """Retrieve a member belonging to a household owned by current_user or raise 404."""
    household = _get_user_household_or_404(household_id, user, db)
    member = (
        db.query(Member)
        .filter(Member.id == member_id, Member.household_id == household.id)
        .first()
    )
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Member with ID {member_id} not found in household {household_id}.",
        )
    return member


def _get_member_by_id_for_user(member_id: int, user: User, db: Session) -> Member:
    """Retrieve member by member_id ensuring its parent household is owned by user."""
    member = (
        db.query(Member)
        .join(Household, Member.household_id == Household.id)
        .filter(Member.id == member_id, Household.owner_id == user.id)
        .first()
    )
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Member with ID {member_id} not found or you do not have permission to access it.",
        )
    return member


# ---------------------------------------------------------------------------
# Household Endpoints
# ---------------------------------------------------------------------------

@router.post("/households", response_model=HouseholdOut, status_code=status.HTTP_201_CREATED)
def create_household(
    payload: HouseholdCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new household owned by the authenticated user."""
    household = Household(
        name=payload.name.strip(),
        weekly_budget=payload.weekly_budget,
        owner_id=current_user.id,
    )
    db.add(household)
    db.commit()
    db.refresh(household)

    return HouseholdOut(
        id=household.id,
        name=household.name,
        weekly_budget=float(household.weekly_budget) if household.weekly_budget is not None else None,
        owner_id=household.owner_id,
        created_at=household.created_at,
        updated_at=household.updated_at,
        member_count=0,
    )


@router.get("/households", response_model=List[HouseholdOut])
def list_households(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all households owned by the authenticated user."""
    households = (
        db.query(Household)
        .filter(Household.owner_id == current_user.id)
        .order_by(Household.created_at.desc())
        .all()
    )

    return [
        HouseholdOut(
            id=h.id,
            name=h.name,
            weekly_budget=float(h.weekly_budget) if h.weekly_budget is not None else None,
            owner_id=h.owner_id,
            created_at=h.created_at,
            updated_at=h.updated_at,
            member_count=len(h.members),
        )
        for h in households
    ]


@router.get("/households/{household_id}", response_model=HouseholdOut)
def get_household(
    household_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get single household details by ID (must be owned by authenticated user)."""
    h = _get_user_household_or_404(household_id, current_user, db)
    return HouseholdOut(
        id=h.id,
        name=h.name,
        weekly_budget=float(h.weekly_budget) if h.weekly_budget is not None else None,
        owner_id=h.owner_id,
        created_at=h.created_at,
        updated_at=h.updated_at,
        member_count=len(h.members),
    )


# ---------------------------------------------------------------------------
# Member Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/households/{household_id}/members",
    response_model=MemberOut,
    status_code=status.HTTP_201_CREATED,
)
def create_member(
    household_id: int,
    payload: MemberCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a new family member to the specified household."""
    household = _get_user_household_or_404(household_id, current_user, db)

    member = Member(
        household_id=household.id,
        name=payload.name.strip(),
        age=payload.age,
        gender=payload.gender,
        height_cm=payload.height_cm,
        weight_kg=payload.weight_kg,
        activity_level=payload.activity_level,
        dietary_preference=payload.dietary_preference,
        allergies=payload.allergies,
        dietary_restrictions=payload.dietary_restrictions,
    )
    db.add(member)
    db.commit()
    db.refresh(member)

    # Automatically calculate initial baseline nutrition target
    try:
        calculated = calculate_nutrition_for_member(member)
        save_or_update_nutrition_target(db, member, calculated)
        has_target = True
    except Exception:
        has_target = False

    return MemberOut(
        id=member.id,
        household_id=member.household_id,
        name=member.name,
        age=member.age,
        gender=member.gender,
        height_cm=member.height_cm,
        weight_kg=member.weight_kg,
        activity_level=member.activity_level,
        dietary_preference=member.dietary_preference,
        allergies=member.allergies,
        dietary_restrictions=member.dietary_restrictions,
        created_at=member.created_at,
        updated_at=member.updated_at,
        has_nutrition_target=has_target,
    )


@router.get("/households/{household_id}/members", response_model=List[MemberOut])
def list_household_members(
    household_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all family members within a household."""
    household = _get_user_household_or_404(household_id, current_user, db)
    members = (
        db.query(Member)
        .filter(Member.household_id == household.id)
        .order_by(Member.created_at.asc())
        .all()
    )

    return [
        MemberOut(
            id=m.id,
            household_id=m.household_id,
            name=m.name,
            age=m.age,
            gender=m.gender,
            height_cm=m.height_cm,
            weight_kg=m.weight_kg,
            activity_level=m.activity_level,
            dietary_preference=m.dietary_preference,
            allergies=m.allergies,
            dietary_restrictions=m.dietary_restrictions,
            created_at=m.created_at,
            updated_at=m.updated_at,
            has_nutrition_target=len(m.nutrition_targets) > 0,
        )
        for m in members
    ]


@router.get(
    "/households/{household_id}/members/{member_id}", response_model=MemberOut
)
def get_member(
    household_id: int,
    member_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get single member details."""
    m = _get_user_member_or_404(household_id, member_id, current_user, db)
    return MemberOut(
        id=m.id,
        household_id=m.household_id,
        name=m.name,
        age=m.age,
        gender=m.gender,
        height_cm=m.height_cm,
        weight_kg=m.weight_kg,
        activity_level=m.activity_level,
        dietary_preference=m.dietary_preference,
        allergies=m.allergies,
        dietary_restrictions=m.dietary_restrictions,
        created_at=m.created_at,
        updated_at=m.updated_at,
        has_nutrition_target=len(m.nutrition_targets) > 0,
    )


@router.put(
    "/households/{household_id}/members/{member_id}", response_model=MemberOut
)
@router.patch(
    "/households/{household_id}/members/{member_id}", response_model=MemberOut
)
def update_member(
    household_id: int,
    member_id: int,
    payload: MemberUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update family member attributes and automatically recalculate nutrition if biometrics change."""
    member = _get_user_member_or_404(household_id, member_id, current_user, db)

    biometrics_changed = False

    if payload.name is not None:
        member.name = payload.name.strip()
    if payload.age is not None and payload.age != member.age:
        member.age = payload.age
        biometrics_changed = True
    if payload.gender is not None and payload.gender != member.gender:
        member.gender = payload.gender
        biometrics_changed = True
    if payload.height_cm is not None and payload.height_cm != member.height_cm:
        member.height_cm = payload.height_cm
        biometrics_changed = True
    if payload.weight_kg is not None and payload.weight_kg != member.weight_kg:
        member.weight_kg = payload.weight_kg
        biometrics_changed = True
    if (
        payload.activity_level is not None
        and payload.activity_level != member.activity_level
    ):
        member.activity_level = payload.activity_level
        biometrics_changed = True
    if payload.dietary_preference is not None:
        member.dietary_preference = payload.dietary_preference
    if payload.allergies is not None:
        member.allergies = payload.allergies
    if payload.dietary_restrictions is not None:
        member.dietary_restrictions = payload.dietary_restrictions

    db.commit()
    db.refresh(member)

    # Recalculate target if biometrics or activity changed and target already exists
    if biometrics_changed:
        try:
            calculated = calculate_nutrition_for_member(member)
            save_or_update_nutrition_target(db, member, calculated)
        except Exception:
            pass

    return MemberOut(
        id=member.id,
        household_id=member.household_id,
        name=member.name,
        age=member.age,
        gender=member.gender,
        height_cm=member.height_cm,
        weight_kg=member.weight_kg,
        activity_level=member.activity_level,
        dietary_preference=member.dietary_preference,
        allergies=member.allergies,
        dietary_restrictions=member.dietary_restrictions,
        created_at=member.created_at,
        updated_at=member.updated_at,
        has_nutrition_target=len(member.nutrition_targets) > 0,
    )


@router.delete(
    "/households/{household_id}/members/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_member(
    household_id: int,
    member_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a family member and cascade-delete associated nutrition targets."""
    member = _get_user_member_or_404(household_id, member_id, current_user, db)
    db.delete(member)
    db.commit()
    return None


# ---------------------------------------------------------------------------
# Nutrition Engine Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/members/{member_id}/nutrition/calculate",
    response_model=NutritionCalculationResult,
)
def calculate_and_save_member_nutrition(
    member_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Calculate BMR, TDEE, macros, and fiber for a family member, and persist the target."""
    member = _get_member_by_id_for_user(member_id, current_user, db)

    calculated = calculate_nutrition_for_member(member)
    save_or_update_nutrition_target(db, member, calculated)

    return NutritionCalculationResult(
        member_id=member.id,
        member_name=member.name,
        gender=member.gender,
        age=member.age,
        height_cm=member.height_cm,
        weight_kg=member.weight_kg,
        bmr=calculated["bmr"],
        activity_level=calculated["activity_level"],
        activity_multiplier=calculated["activity_multiplier"],
        tdee=calculated["tdee"],
        daily_calories=calculated["daily_calories"],
        daily_protein_g=calculated["daily_protein_g"],
        daily_carbs_g=calculated["daily_carbs_g"],
        daily_fat_g=calculated["daily_fat_g"],
        daily_fiber_g=calculated["daily_fiber_g"],
    )


@router.get(
    "/members/{member_id}/nutrition",
    response_model=NutritionTargetOut,
)
def get_member_nutrition_target(
    member_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve the saved daily nutrition target for a family member."""
    member = _get_member_by_id_for_user(member_id, current_user, db)

    target = (
        db.query(NutritionTarget)
        .filter(NutritionTarget.member_id == member.id)
        .order_by(NutritionTarget.updated_at.desc())
        .first()
    )
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Nutrition target has not yet been calculated for member {member_id}.",
        )

    return NutritionTargetOut(
        id=target.id,
        member_id=target.member_id,
        daily_calories=target.daily_calories,
        daily_protein_g=target.daily_protein_g,
        daily_carbs_g=target.daily_carbs_g,
        daily_fat_g=target.daily_fat_g,
        daily_fiber_g=target.daily_fiber_g,
        created_at=target.created_at,
        updated_at=target.updated_at,
    )
