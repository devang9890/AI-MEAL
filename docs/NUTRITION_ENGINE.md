# Nutrition Engine & Household Architecture Documentation

> **Educational & Algorithmic Disclaimer**  
> The nutritional calculations, equations, and macronutrient distributions implemented in this system are intended strictly for educational and algorithmic meal-planning estimation purposes within the AI Meal Planner application. They do **not** constitute medical, clinical, or formal dietary advice. Individuals with specific medical conditions, metabolic disorders, pregnant or lactating individuals, or unique dietary requirements should consult a licensed physician, registered dietitian, or qualified healthcare professional before undertaking any dietary regimen.

---

## Table of Contents
1. [What is a Household?](#1-what-is-a-household)
2. [What is a Family Member?](#2-what-is-a-family-member)
3. [How are They Connected to the Clerk User?](#3-how-are-they-connected-to-the-clerk-user)
4. [Ownership & Multi-Tenant Security Isolation](#4-ownership--multi-tenant-security-isolation)
5. [What is BMR (Basal Metabolic Rate)?](#5-what-is-bmr-basal-metabolic-rate)
6. [Why Mifflin–St Jeor Equation Was Chosen](#6-why-mifflin-st-jeor-equation-was-chosen)
7. [What is TDEE (Total Daily Energy Expenditure)?](#7-what-is-tdee-total-daily-energy-expenditure)
8. [Physical Activity Multipliers](#8-physical-activity-multipliers)
9. [How Daily Calorie Targets are Determined](#9-how-daily-calorie-targets-are-determined)
10. [How Protein is Calculated](#10-how-protein-is-calculated)
11. [How Carbohydrates are Calculated](#11-how-carbohydrates-are-calculated)
12. [How Fat is Calculated](#12-how-fat-is-calculated)
13. [How Fiber is Calculated](#13-how-fiber-is-calculated)
14. [How to Use the API: Step-by-Step Guide](#14-how-to-use-the-api-step-by-step-guide)
15. [Full End-to-End Reference Calculation: Rahul (Step-by-Step)](#15-full-end-to-end-reference-calculation-rahul-step-by-step)

---

## 1. What is a Household?
In real-world dining and grocery planning, meals are rarely bought or prepared for one solitary individual in total isolation. Families, roommates, couples, and shared living spaces purchase groceries as a unit and cook shared dishes.

A **Household** represents a shared meal-planning and budgeting entity. It encapsulates:
- A human-readable name (e.g., *"Sharma Family"*).
- An optional weekly grocery budget (e.g., `3500.00` INR).
- An owner reference tying the household to the authenticated user.
- A collection of family members who share meals in that household.

---

## 2. What is a Family Member?
A **Member** represents an individual resident of a household with specific physiological characteristics, dietary preferences, and nutritional targets.

Each member record stores:
- **`name`**: Member's name (e.g., *"Rahul"*).
- **`age`**: Age in whole years (must be $> 0$).
- **`gender`**: Biological sex (`male` or `female`), used for Mifflin–St Jeor metabolic equations.
- **`height_cm`**: Height in centimeters (must be $> 0$).
- **`weight_kg`**: Body mass in kilograms (must be $> 0$).
- **`activity_level`**: Physical activity category (`sedentary`, `light`, `moderate`, `active`, `very_active`).
- **`dietary_preference`**: Primary dietary pattern (`vegetarian`, `vegan`, `eggetarian`, `non_vegetarian`, `pescatarian`).
- **`allergies`**: Comma-delimited list or structured tags of food allergens (e.g., `["peanuts", "dairy"]`).
- **`dietary_restrictions`**: Specific guidelines (e.g., `["jain", "gluten_free", "halal"]`).

Each member can have a persisted **`NutritionTarget`** storing their calculated daily caloric, macro, and fiber goals.

---

## 3. How are They Connected to the Clerk User?
Authentication in the AI Meal Planner is managed through **Clerk**:
1. When a client authenticates with Clerk, it receives a signed JSON Web Token (JWT).
2. The frontend sends this token in the `Authorization: Bearer <token>` header to the FastAPI backend.
3. The FastAPI dependency `get_current_user` validates the JWT against Clerk's public JWKS endpoint.
4. It extracts the Clerk User ID (`sub`, e.g., `user_2b9x...`) and email address.
5. In PostgreSQL, a corresponding record in the `users` table is retrieved or automatically provisioned:
   ```sql
   SELECT * FROM users WHERE clerk_user_id = 'user_2b9x...';
   ```
6. The `Household` model has a foreign key `owner_id` pointing directly to `users.id`:
   ```sql
   households.owner_id -> users.id
   ```
7. Each `Member` is associated via foreign key `household_id`:
   ```sql
   members.household_id -> households.id
   ```

---

## 4. Ownership & Multi-Tenant Security Isolation
Multi-tenancy and data privacy are enforced at the API boundary:
- **No Cross-Tenant Leaks**: When user `A` requests `/api/households/{household_id}` or `/api/members/{member_id}`, the backend checks ownership:
  ```python
  member = (
      db.query(Member)
      .join(Household, Member.household_id == Household.id)
      .filter(Member.id == member_id, Household.owner_id == current_user.id)
      .first()
  )
  ```
- If the household or member belongs to another user (or does not exist), the endpoint immediately responds with **HTTP 404 Not Found**. It never returns a 403 or detailed existence hint, preserving complete privacy.
- When creating or modifying households and members, users can only manipulate records under their own authenticated account.

---

## 5. What is BMR (Basal Metabolic Rate)?
**Basal Metabolic Rate (BMR)** is the baseline number of calories an individual's body requires each day simply to sustain vital involuntary physiological functions while at complete rest in a temperate environment (such as respiration, circulation, cellular repair, hormone production, and neurological processing).

---

## 6. Why Mifflin–St Jeor Equation Was Chosen
Historically, several formulas have attempted to estimate BMR:
- **Harris–Benedict (1919 / 1984 Revised)**: Often overestimates energy expenditure by 5% to 15%, especially in modern populations.
- **Katch–McArdle**: Requires an accurate measurement of body fat percentage, which is rarely known or accessible to general users without specialized DEXA scans or calipers.
- **Mifflin–St Jeor (1990)**: Widely recognized by the *Academy of Nutrition and Dietetics* as the most reliable, validated, and clinically accurate equation for predicting resting energy expenditure in healthy adults based purely on weight, height, age, and sex.

### The Equations:
$$\text{Base} = (10 \times \text{weight in kg}) + (6.25 \times \text{height in cm}) - (5 \times \text{age in years})$$

- **For Males**:
  $$\text{BMR}_{\text{male}} = \text{Base} + 5$$
- **For Females**:
  $$\text{BMR}_{\text{female}} = \text{Base} - 161$$

---

## 7. What is TDEE (Total Daily Energy Expenditure)?
While BMR accounts for survival at rest, daily human life involves physical activity, work, commuting, exercise, and the thermic effect of food. 

**Total Daily Energy Expenditure (TDEE)** estimates the total number of calories a person burns in an entire 24-hour day by scaling BMR with an **Activity Multiplier**:
$$\text{TDEE} = \text{BMR} \times \text{Physical Activity Multiplier}$$

---

## 8. Physical Activity Multipliers
The AI Meal Planner incorporates standard physical activity factors:

| Activity Level | Multiplier | Description |
| :--- | :--- | :--- |
| `sedentary` | **1.200** | Little or no exercise; desk job; predominantly seated. |
| `light` | **1.375** | Light exercise / sports 1–3 days per week. |
| `moderate` | **1.550** | Moderate exercise / sports 3–5 days per week. |
| `active` | **1.725** | Hard exercise / sports 6–7 days per week. |
| `very_active` | **1.900** | Very intense daily exercise, athletic training, or demanding physical labor. |

---

## 9. How Daily Calorie Targets are Determined
In this foundational nutrition engine, the daily energy target is calibrated to **maintenance calories**, meaning:
$$\text{Daily Caloric Target} = \text{TDEE}$$
This supplies the body with sufficient energy to maintain stable mass while providing baseline parameters for meal planning.

---

## 10. How Protein is Calculated
- **Target Ratio**: **20%** of total daily calories.
- **Energy Density**: Protein provides **4 kcal per gram**.
- **Formula**:
  $$\text{Daily Protein (g)} = \frac{\text{Daily Calories} \times 0.20}{4\,\text{kcal/g}}$$

---

## 11. How Carbohydrates are Calculated
- **Target Ratio**: **50%** of total daily calories.
- **Energy Density**: Carbohydrates provide **4 kcal per gram**.
- **Formula**:
  $$\text{Daily Carbs (g)} = \frac{\text{Daily Calories} \times 0.50}{4\,\text{kcal/g}}$$

---

## 12. How Fat is Calculated
- **Target Ratio**: **30%** of total daily calories.
- **Energy Density**: Dietary fat provides **9 kcal per gram**.
- **Formula**:
  $$\text{Daily Fat (g)} = \frac{\text{Daily Calories} \times 0.30}{9\,\text{kcal/g}}$$

---

## 13. How Fiber is Calculated
- **Recommendation**: Standard public health and dietary guideline (e.g., USDA / WHO) recommending **14 grams of dietary fiber per 1,000 kilocalories**.
- **Formula**:
  $$\text{Daily Fiber (g)} = \text{Daily Calories} \times \left(\frac{14\,\text{g}}{1000\,\text{kcal}}\right) = \text{Daily Calories} \times 0.014$$

---

## 14. How to Use the API: Step-by-Step Guide

All requests require the Clerk Bearer token in the header:
```http
Authorization: Bearer <clerk_jwt_token>
```

### 1. Create a Household
`POST /api/households`
```json
{
  "name": "Sharma Residence",
  "weekly_budget": 4500.00
}
```
**Response (201 Created)**:
```json
{
  "id": 1,
  "name": "Sharma Residence",
  "weekly_budget": 4500.0,
  "owner_id": 10,
  "created_at": "2026-09-13T15:30:00Z",
  "updated_at": "2026-09-13T15:30:00Z",
  "members_count": 0
}
```

### 2. Add a Family Member
`POST /api/households/{household_id}/members`
```json
{
  "name": "Rahul",
  "age": 22,
  "gender": "male",
  "height_cm": 170.0,
  "weight_kg": 60.0,
  "activity_level": "moderate",
  "dietary_preference": "vegetarian",
  "allergies": ["peanuts"],
  "dietary_restrictions": []
}
```
**Response (201 Created)**:
```json
{
  "id": 1,
  "household_id": 1,
  "name": "Rahul",
  "age": 22,
  "gender": "male",
  "height_cm": 170.0,
  "weight_kg": 60.0,
  "activity_level": "moderate",
  "dietary_preference": "vegetarian",
  "allergies": ["peanuts"],
  "dietary_restrictions": [],
  "created_at": "2026-09-13T15:32:00Z",
  "updated_at": "2026-09-13T15:32:00Z",
  "has_nutrition_target": false
}
```

### 3. Calculate & Save Nutrition Target
`POST /api/members/{member_id}/nutrition/calculate`

No request body needed. The service queries the member's biometrics, evaluates BMR/TDEE/macros/fiber, saves or updates the `nutrition_targets` table in Neon PostgreSQL, and returns the full calculation.

**Response (200 OK)**:
```json
{
  "member_id": 1,
  "member_name": "Rahul",
  "gender": "male",
  "age": 22,
  "height_cm": 170.0,
  "weight_kg": 60.0,
  "bmr": 1557.5,
  "activity_level": "moderate",
  "activity_multiplier": 1.55,
  "tdee": 2414.1,
  "daily_calories": 2414.1,
  "daily_protein_g": 120.7,
  "daily_carbs_g": 301.8,
  "daily_fat_g": 80.5,
  "daily_fiber_g": 33.8
}
```

### 4. Fetch Stored Nutrition Target
`GET /api/members/{member_id}/nutrition`

**Response (200 OK)**:
```json
{
  "id": 1,
  "member_id": 1,
  "daily_calories": 2414.1,
  "daily_protein_g": 120.7,
  "daily_carbs_g": 301.8,
  "daily_fat_g": 80.5,
  "daily_fiber_g": 33.8,
  "created_at": "2026-09-13T15:35:00Z",
  "updated_at": "2026-09-13T15:35:00Z"
}
```

---

## 15. Full End-to-End Reference Calculation: Rahul (Step-by-Step)

### Input Profile:
- **Name**: Rahul
- **Age**: 22 years
- **Gender**: Male
- **Height**: 170 cm
- **Weight**: 60 kg
- **Activity Level**: Moderate

---

### Step 1: Compute Basal Metabolic Rate (BMR)
$$\text{BMR} = 10 \times \text{weight} + 6.25 \times \text{height} - 5 \times \text{age} + 5$$
$$\text{BMR} = (10 \times 60) + (6.25 \times 170) - (5 \times 22) + 5$$
$$\text{BMR} = 600 + 1062.5 - 110 + 5$$
$$\mathbf{\text{BMR} = 1557.5\,\text{kcal}}$$

---

### Step 2: Compute Total Daily Energy Expenditure (TDEE)
Activity level is `moderate`, so the activity factor is **1.55**:
$$\text{TDEE} = \text{BMR} \times 1.55$$
$$\text{TDEE} = 1557.5 \times 1.55 = 2414.125\,\text{kcal}$$
Rounding to one decimal place:
$$\mathbf{\text{Daily Caloric Target} = 2414.1\,\text{kcal}}$$

---

### Step 3: Compute Daily Protein Target (20%)
$$\text{Calories from Protein} = 2414.125 \times 0.20 = 482.825\,\text{kcal}$$
$$\text{Grams of Protein} = \frac{482.825}{4\,\text{kcal/g}} = 120.706\,\text{g}$$
Rounding to one decimal place:
$$\mathbf{\text{Daily Protein} = 120.7\,\text{g}}$$

---

### Step 4: Compute Daily Carbohydrate Target (50%)
$$\text{Calories from Carbs} = 2414.125 \times 0.50 = 1207.0625\,\text{kcal}$$
$$\text{Grams of Carbs} = \frac{1207.0625}{4\,\text{kcal/g}} = 301.765\,\text{g}$$
Rounding to one decimal place:
$$\mathbf{\text{Daily Carbohydrates} = 301.8\,\text{g}}$$

---

### Step 5: Compute Daily Fat Target (30%)
$$\text{Calories from Fat} = 2414.125 \times 0.30 = 724.2375\,\text{kcal}$$
$$\text{Grams of Fat} = \frac{724.2375}{9\,\text{kcal/g}} = 80.470\,\text{g}$$
Rounding to one decimal place:
$$\mathbf{\text{Daily Fat} = 80.5\,\text{g}}$$

---

### Step 6: Compute Daily Dietary Fiber Target (14g per 1,000 kcal)
$$\text{Grams of Fiber} = 2414.125 \times \frac{14}{1000} = 2414.125 \times 0.014 = 33.797\,\text{g}$$
Rounding to one decimal place:
$$\mathbf{\text{Daily Fiber} = 33.8\,\text{g}}$$

---

### Summary of Rahul's Daily Targets:
- **Calories**: **2,414.1 kcal**
- **Protein**: **120.7 g**
- **Carbohydrates**: **301.8 g**
- **Fat**: **80.5 g**
- **Fiber**: **33.8 g**
