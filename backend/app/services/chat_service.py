"""Chat Service for AI Meal Planner using Groq SDK.

Provides context-grounded nutrition assistance based on the user's actual
household biometrics, calculated Mifflin–St Jeor targets, recipes, and ingredients.
"""
import os
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.household import Household
from app.models.member import Member
from app.models.nutrition import NutritionTarget
from app.models.recipe import Recipe
from app.models.ingredient import Ingredient
from app.schemas.chat import ChatMessageItem

logger = logging.getLogger(__name__)

DEFAULT_GROQ_MODEL = "openai/gpt-oss-120b"


def get_household_context(
    db: Session,
    current_user: Optional[User],
    household_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Extracts the authenticated user's household, member biometrics, and
    calculated daily nutrition targets. Ensures strict data isolation:
    users can only query households they own.
    """
    if not current_user:
        return {
            "has_household": False,
            "reason": "User is not authenticated."
        }

    # Query household owned by current_user
    query = db.query(Household).filter(Household.owner_id == current_user.id)
    if household_id:
        household = query.filter(Household.id == household_id).first()
    else:
        household = query.first()

    if not household:
        return {
            "has_household": False,
            "user_name": current_user.name or "User",
            "reason": "No household profiles found for this account yet."
        }

    members = db.query(Member).filter(Member.household_id == household.id).all()

    members_data = []
    total_calories = 0.0
    total_protein_g = 0.0
    total_carbs_g = 0.0
    total_fat_g = 0.0
    total_fiber_g = 0.0
    members_with_targets = 0

    for m in members:
        target = db.query(NutritionTarget).filter(NutritionTarget.member_id == m.id).first()
        target_info = None
        if target:
            members_with_targets += 1
            total_calories += target.daily_calories or 0.0
            total_protein_g += target.daily_protein_g or 0.0
            total_carbs_g += target.daily_carbs_g or 0.0
            total_fat_g += target.daily_fat_g or 0.0
            total_fiber_g += target.daily_fiber_g or 0.0
            target_info = {
                "daily_calories": round(target.daily_calories, 1),
                "daily_protein_g": round(target.daily_protein_g, 1),
                "daily_carbs_g": round(target.daily_carbs_g, 1),
                "daily_fat_g": round(target.daily_fat_g, 1),
                "daily_fiber_g": round(target.daily_fiber_g, 1),
            }

        members_data.append({
            "name": m.name,
            "age": m.age,
            "gender": m.gender,
            "height_cm": m.height_cm,
            "weight_kg": m.weight_kg,
            "activity_level": m.activity_level,
            "dietary_preference": m.dietary_preference,
            "allergies": m.allergies or "None",
            "dietary_restrictions": m.dietary_restrictions or "None",
            "nutrition_target": target_info
        })

    return {
        "has_household": True,
        "household_id": household.id,
        "household_name": household.name,
        "weekly_budget": float(household.weekly_budget) if household.weekly_budget is not None else None,
        "member_count": len(members),
        "members": members_data,
        "has_targets": members_with_targets > 0,
        "aggregate_targets": {
            "daily_calories": round(total_calories, 1),
            "daily_protein_g": round(total_protein_g, 1),
            "daily_carbs_g": round(total_carbs_g, 1),
            "daily_fat_g": round(total_fat_g, 1),
            "daily_fiber_g": round(total_fiber_g, 1),
        } if members_with_targets > 0 else None
    }


def get_food_knowledge_context(db: Session) -> Dict[str, Any]:
    """
    Pulls sample high-protein and staple recipes, plus affordable ingredients
    from the database to allow grounded answers without hallucinating foods.
    """
    try:
        # Sample recipes
        recipes = db.query(Recipe).limit(8).all()
        recipe_summaries = []
        for r in recipes:
            recipe_summaries.append({
                "name": r.name,
                "meal_type": r.meal_type,
                "cuisine": r.cuisine,
                "tags": r.dietary_tags or [],
                "cost_inr": float(r.estimated_cost) if r.estimated_cost is not None else None,
            })

        # Affordable / staple ingredients
        ingredients = (
            db.query(Ingredient)
            .filter(Ingredient.price_per_unit.isnot(None))
            .order_by(Ingredient.price_per_unit.asc())
            .limit(10)
            .all()
        )
        ingredient_summaries = []
        for ing in ingredients:
            ingredient_summaries.append({
                "name": ing.name,
                "category": ing.category,
                "price_per_unit": float(ing.price_per_unit) if ing.price_per_unit is not None else None,
                "unit": ing.unit,
                "protein_g": ing.protein,
                "calories": ing.calories
            })

        return {
            "sample_recipes": recipe_summaries,
            "affordable_ingredients": ingredient_summaries
        }
    except Exception as exc:
        logger.warning(f"Could not load food knowledge context: {exc}")
        return {"sample_recipes": [], "affordable_ingredients": []}


def build_system_prompt(household_ctx: Dict[str, Any], food_ctx: Dict[str, Any]) -> str:
    """
    Builds the system prompt with assistant identity, safety instructions,
    and verified database context.
    """
    prompt_lines = [
        "You are the 'AI Meal Planner Assistant', an intelligent, empathetic, and knowledgeable nutrition and meal planning assistant built into the AI Meal Planner web application.",
        "",
        "### YOUR GOALS & SCOPE:",
        "- Help users understand their household nutrition targets (calories, protein, carbohydrates, fats, fiber).",
        "- Explain metabolic concepts like Basal Metabolic Rate (BMR) and Total Daily Energy Expenditure (TDEE) in clear, accessible, everyday English.",
        "- Guide users on affordable, balanced meal planning, Indian meals, grocery budgeting, and wholesome ingredients.",
        "- Explain recipe options, dietary preferences (vegetarian, vegan, non-vegetarian, eggitarian), and high-protein foods.",
        "",
        "### IMPORTANT SAFETY & MEDICAL DISCLAIMER RULE:",
        "- You are an AI assistant, NOT a doctor, registered dietitian, or medical professional.",
        "- Always provide general nutritional and educational information.",
        "- Do NOT diagnose, treat, or offer clinical medical advice.",
        "- If the user asks about serious medical conditions, extreme diets, or clinical illnesses, kindly remind them to consult a qualified physician or certified dietitian.",
        "",
        "### TONE & COMMUNICATION STYLE:",
        "- Use warm, concise, and easy-to-understand English. Avoid unnecessary medical or mathematical jargon.",
        "- Use bullet points or short paragraphs where appropriate for readability.",
        "- Keep responses direct and relevant to the user's question.",
        "",
        "### HOUSEHOLD & NUTRITION DATA (DATABASE GROUND TRUTH):"
    ]

    if household_ctx.get("has_household"):
        prompt_lines.append(f"- Household Name: {household_ctx.get('household_name')}")
        if household_ctx.get("weekly_budget"):
            prompt_lines.append(f"- Weekly Budget: ₹{household_ctx.get('weekly_budget'):.2f}")
        prompt_lines.append(f"- Total Family Members: {household_ctx.get('member_count')}")

        members = household_ctx.get("members", [])
        if members:
            prompt_lines.append("- Members:")
            for m in members:
                line = (
                    f"  * {m['name']}: {m['age']} yrs old, {m['gender']}, {m['height_cm']}cm, "
                    f"{m['weight_kg']}kg, Activity: {m['activity_level']}, Diet: {m['dietary_preference']}"
                )
                if m.get("allergies") and m["allergies"] != "None":
                    line += f", Allergies: {m['allergies']}"
                if m.get("nutrition_target"):
                    t = m["nutrition_target"]
                    line += (
                        f" -> Target: {t['daily_calories']} kcal/day "
                        f"({t['daily_protein_g']}g protein, {t['daily_carbs_g']}g carbs, "
                        f"{t['daily_fat_g']}g fat, {t['daily_fiber_g']}g fiber)"
                    )
                else:
                    line += " -> (Nutrition target not computed yet)"
                prompt_lines.append(line)

        agg = household_ctx.get("aggregate_targets")
        if agg:
            prompt_lines.append("- TOTAL HOUSEHOLD DAILY NUTRITION TARGET:")
            prompt_lines.append(f"  * Calories: {agg['daily_calories']} kcal/day")
            prompt_lines.append(f"  * Protein: {agg['daily_protein_g']} g/day")
            prompt_lines.append(f"  * Carbohydrates: {agg['daily_carbs_g']} g/day")
            prompt_lines.append(f"  * Fat: {agg['daily_fat_g']} g/day")
            prompt_lines.append(f"  * Fiber: {agg['daily_fiber_g']} g/day")
            prompt_lines.append(
                "CRITICAL INSTRUCTION: When the user asks about their household calories, protein, or targets, "
                "YOU MUST USE THESE EXACT VALUES rather than inventing arbitrary numbers! Explain how they were calculated "
                "from individual member BMR (Mifflin–St Jeor equation) and activity levels."
            )
        else:
            prompt_lines.append(
                "- Nutrition targets have not been calculated yet for these members. "
                "If the user asks for their calorie or protein target, politely let them know they can click the "
                "'⚡ Calculate Nutrition Target' button for their members on this page to compute them."
            )
    else:
        prompt_lines.append(
            "- No household is currently loaded for this user session. "
            "If asked about 'my household' or 'my calories', explain that no household profile is active right now, "
            "and explain general nutrition guidelines or invite them to set up a household profile."
        )

    # Food context
    sample_recipes = food_ctx.get("sample_recipes", [])
    if sample_recipes:
        prompt_lines.append("")
        prompt_lines.append("### AVAILABLE RECIPES IN DATABASE (Reference these when suggesting meals):")
        for r in sample_recipes[:6]:
            tags_str = ", ".join(r.get("tags", []))
            cost_str = f", ₹{r['cost_inr']}" if r.get("cost_inr") else ""
            prompt_lines.append(f"- {r['name']} ({r.get('meal_type', 'Meal')}, {r.get('cuisine', '')}{cost_str}, Tags: {tags_str})")

    affordable_ings = food_ctx.get("affordable_ingredients", [])
    if affordable_ings:
        prompt_lines.append("")
        prompt_lines.append("### AFFORDABLE & NUTRITIOUS STAPLE INGREDIENTS IN DATABASE:")
        for ing in affordable_ings[:8]:
            p_str = f"₹{ing['price_per_unit']}/{ing['unit']}" if ing.get("price_per_unit") is not None else "Budget-friendly"
            prompt_lines.append(f"- {ing['name']} ({ing['category']}): ~{p_str}, ~{ing.get('protein_g', 0)}g protein/100g")

    return "\n".join(prompt_lines)


def generate_chat_reply(
    message: str,
    conversation: List[ChatMessageItem],
    db: Session,
    current_user: Optional[User] = None,
    household_id: Optional[int] = None,
    groq_client: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Main entry point for generating chat replies using Groq LLM.
    """
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    model = os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL).strip() or DEFAULT_GROQ_MODEL

    # Check API key
    if not api_key and groq_client is None:
        logger.warning("GROQ_API_KEY is not configured in environment.")
        return {
            "reply": (
                "The AI assistant service is running, but the backend requires a configured `GROQ_API_KEY` "
                "in `backend/.env` to process live conversations. Please set `GROQ_API_KEY` to enable full responses."
            ),
            "success": False,
            "error": "GROQ_API_KEY_NOT_CONFIGURED"
        }

    # Fetch context
    household_ctx = get_household_context(db, current_user, household_id)
    food_ctx = get_food_knowledge_context(db)
    system_prompt = build_system_prompt(household_ctx, food_ctx)

    # Prepare messages array for Groq
    groq_messages = [
        {"role": "system", "content": system_prompt}
    ]

    # Append up to last 10 turns of conversation history
    for item in conversation[-10:]:
        if item.role in ("user", "assistant"):
            groq_messages.append({
                "role": item.role,
                "content": item.content
            })

    # Append the latest user query
    groq_messages.append({
        "role": "user",
        "content": message
    })

    try:
        # Initialize Groq client if not injected (for testing injection)
        if groq_client is None:
            from groq import Groq
            groq_client = Groq(api_key=api_key)

        chat_completion = groq_client.chat.completions.create(
            messages=groq_messages,
            model=model,
            temperature=0.6,
            max_tokens=1024,
        )

        reply_text = chat_completion.choices[0].message.content
        return {
            "reply": reply_text.strip(),
            "success": True,
            "error": None
        }

    except Exception as exc:
        logger.error(f"Groq API call error: {exc}", exc_info=True)
        return {
            "reply": "Sorry, I couldn't process that right now. Please try again in a moment.",
            "success": False,
            "error": "GROQ_PROCESSING_ERROR"
        }
