# Food & Recipe Database Documentation

> **Disclaimer:** Nutritional values and retail pricing benchmarks in this dataset are approximations suitable for educational engineering demonstrations. They are based on standard Indian Food Composition Tables (IFCT / ICMR) and retail market references, and do not constitute medical or clinical dietary advice.

---

## 1. Overview & Architecture

The Food & Recipe database forms the foundational catalog for the AI Meal Planner. It stores raw ingredients, composed household recipes, and the many-to-many relationship mapping how recipes are prepared from specific ingredients in exact portions.

```
+----------------+          +--------------------+          +----------------+
|     Recipe     | 1      * |  RecipeIngredient  | *      1 |   Ingredient   |
|----------------|----------|--------------------|----------|----------------|
| id             |          | id                 |          | id             |
| name           |          | recipe_id (FK)     |          | name (UNIQUE)  |
| description    |          | ingredient_id (FK) |          | category       |
| meal_type      |          | quantity           |          | unit           |
| cuisine        |          | unit               |          | price_per_unit |
| servings       |          +--------------------+          | calories       |
| prep_time      |                                          | protein        |
| cooking_time   |                                          | carbohydrates  |
| dietary_tags   |                                          | fat            |
| estimated_cost |                                          | fiber          |
| instructions   |                                          | created_at     |
| created_at     |                                          +----------------+
+----------------+
```

---

## 2. Table Specifications

### 2.1 `Ingredient` Table
Stores raw baseline food items along with normalized nutritional values and retail market pricing.

| Column | Type | Description / Standard |
| :--- | :--- | :--- |
| `id` | `INTEGER` | Primary Key, Auto-increment |
| `name` | `VARCHAR(255)` | Unique, indexed ingredient name (e.g., "White Basmati Rice", "Paneer (Cottage Cheese)") |
| `category` | `VARCHAR(100)` | Food group (Grains & Cereals, Pulses & Legumes, Vegetables, Dairy, Poultry & Meat, Seafood, Nuts & Seeds, Oils & Fats, Spices & Seasonings, Fruits) |
| `unit` | `VARCHAR(50)` | Baseline measurement unit: standardized to `'100g'` (or `'100ml'` for liquids) |
| `price_per_unit`| `NUMERIC(10, 2)`| Price in Indian Rupees (₹) per 100g / 100ml |
| `calories` | `FLOAT` | Energy in **kcal per 100g / 100ml** |
| `protein` | `FLOAT` | Protein in **grams (g) per 100g / 100ml** |
| `carbohydrates`| `FLOAT` | Carbohydrates in **grams (g) per 100g / 100ml** |
| `fat` | `FLOAT` | Total lipids/fat in **grams (g) per 100g / 100ml** |
| `fiber` | `FLOAT` | Dietary fiber in **grams (g) per 100g / 100ml** |
| `created_at` | `TIMESTAMP` | Timestamp of creation (UTC) |

### 2.2 `Recipe` Table
Stores cooked dishes, preparation metadata, portion size, and culinary instructions.

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | `INTEGER` | Primary Key, Auto-increment |
| `name` | `VARCHAR(255)` | Unique, indexed dish name (e.g., "Punjabi Rajma Masala") |
| `description` | `TEXT` | Brief overview of the meal |
| `meal_type` | `VARCHAR(50)` | Primary slot: `breakfast`, `lunch`, `dinner`, `snack` |
| `cuisine` | `VARCHAR(50)` | Regional origin: `North Indian`, `South Indian`, `Maharashtrian`, `Gujarati`, `Pan-Indian` |
| `servings` | `INTEGER` | Default serving yield (typically 2 to 3 portions) |
| `preparation_time` | `INTEGER` | Active prep time in minutes |
| `cooking_time`| `INTEGER` | Active cooking/steaming time in minutes |
| `dietary_tags` | `JSON` | List of tags: `["vegetarian", "high_protein", "lunch"]`, etc. |
| `estimated_cost` | `NUMERIC(10, 2)`| Total estimated recipe ingredient cost in ₹ |
| `instructions`| `TEXT` | Step-by-step preparation steps |
| `created_at` | `TIMESTAMP` | Timestamp of creation (UTC) |

### 2.3 `RecipeIngredient` Table (Association)
Resolves the many-to-many relationship between recipes and ingredients, storing portion sizes.

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | `INTEGER` | Primary Key, Auto-increment |
| `recipe_id` | `INTEGER` | Foreign Key referencing `recipes.id` (`ON DELETE CASCADE`) |
| `ingredient_id`| `INTEGER` | Foreign Key referencing `ingredients.id` (`ON DELETE CASCADE`) |
| `quantity` | `FLOAT` | Raw quantity used in grams (`g`) or milliliters (`ml`) |
| `unit` | `VARCHAR(50)` | Unit of measurement: `'g'` or `'ml'` |

---

## 3. Standardization & Units Convention

To prevent unit conversion errors during mathematical optimization and nutrition aggregation:

1. **All Ingredient Nutrition is Stored per 100g / 100ml**:
   - Calories $\rightarrow$ kcal / 100g
   - Protein $\rightarrow$ g / 100g
   - Carbohydrates $\rightarrow$ g / 100g
   - Fat $\rightarrow$ g / 100g
   - Fiber $\rightarrow$ g / 100g
2. **All Ingredient Prices are Stored in INR (₹) per 100g / 100ml**:
   - Example: Whole Wheat Flour at ₹45/kg is stored as `4.50`.
   - Example: Toor Dal at ₹160/kg is stored as `16.00`.
   - Example: Toned Cow Milk at ₹65/L is stored as `6.50`.
3. **Recipe Contribution Scaling Formula**:
   Because baseline values are per 100g, the scaling factor for an ingredient portion in a recipe is simply:
   $$\text{factor} = \frac{\text{recipe\_ingredient.quantity}}{100.0}$$
   $$\text{cost\_contribution} = \text{factor} \times \text{ingredient.price\_per\_unit}$$
   $$\text{nutrient\_contribution} = \text{factor} \times \text{ingredient.nutrient\_value}$$
   $$\text{Recipe Estimated Cost} = \sum_{i=1}^{n} \left( \frac{\text{quantity}_i}{100.0} \times \text{price\_per\_unit}_i \right)$$

---

## 4. Seeding Pipeline

The seeding subsystem lives under `backend/app/seed/`:
- `ingredients.py`: Curated catalog of 83 Indian household ingredients.
- `recipes.py`: Catalog of 125 realistic household recipes across Breakfast, Lunch, Dinner, and Snacks.
- `seed_database.py`: Idempotent seeding executor.
- `validate_db.py`: Automated integrity verifier.

### 4.1 Idempotency Guarantee
- **Ingredients** are matched by unique `name`. If an ingredient exists, its nutrition and price values are updated in-place without generating duplicates.
- **Recipes** are matched by unique `name`. If a recipe exists, its attributes are updated and its associated `RecipeIngredient` links are refreshed cleanly.
- Running `python -m app.seed.seed_database` multiple times safely results in 0 duplicate entries.

---

## 5. How to Run Migrations & Seeding

From your terminal in the `backend` folder:

### 1. Apply Alembic Migrations
```powershell
.\venv\Scripts\alembic upgrade head
```

### 2. Run Database Seeding
```powershell
.\venv\Scripts\python -m app.seed.seed_database
```

### 3. Verify Database Integrity
```powershell
.\venv\Scripts\python -m app.seed.validate_db
```

---

## 6. Read-Only API Endpoints

All endpoints are mounted under `/api` in the FastAPI backend.

| Method | Endpoint | Query Parameters | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/ingredients` | `skip`, `limit`, `category`, `search` | Paginated list of ingredients with filtering |
| `GET` | `/api/ingredients/{id}` | - | Single ingredient details |
| `GET` | `/api/recipes` | `skip`, `limit`, `meal_type`, `cuisine`, `dietary_tag`, `search` | Paginated recipes with multi-criteria filters |
| `GET` | `/api/recipes/{id}` | - | Full recipe details, ingredients list, and macro totals |
| `GET` | `/api/recipes/{id}/ingredients` | - | Raw ingredient portion list for a given recipe |

---

## 7. Sample API Requests & Responses

### 7.1 Single Ingredient
**Request:**
`GET http://127.0.0.1:8000/api/ingredients/1`

**Response (200 OK):**
```json
{
  "id": 1,
  "name": "White Basmati Rice",
  "category": "Grains & Cereals",
  "unit": "100g",
  "price_per_unit": 7.0,
  "calories": 350.0,
  "protein": 7.1,
  "carbohydrates": 78.0,
  "fat": 0.6,
  "fiber": 1.3
}
```

### 7.2 Recipe Details with Calculated Nutrition
**Request:**
`GET http://127.0.0.1:8000/api/recipes/1`

**Response (200 OK):**
```json
{
  "id": 1,
  "name": "Kanda Poha",
  "description": "Traditional Maharashtrian breakfast made with flattened rice, crunchy roasted peanuts, caramelized onions, and fragrant tempered spices.",
  "meal_type": "breakfast",
  "cuisine": "Maharashtrian",
  "servings": 2,
  "preparation_time": 10,
  "cooking_time": 15,
  "dietary_tags": [
    "vegetarian",
    "vegan",
    "breakfast",
    "quick_meal"
  ],
  "estimated_cost": 18.52,
  "instructions": "Rinse poha in a colander until soft...",
  "ingredients": [
    {
      "id": 1,
      "ingredient_id": 5,
      "name": "Poha (Flattened Rice)",
      "category": "Grains & Cereals",
      "quantity": 150.0,
      "unit": "g",
      "price_contribution": 9.0,
      "calories_contribution": 529.5,
      "protein_contribution": 9.9,
      "carbs_contribution": 116.0,
      "fat_contribution": 1.5,
      "fiber_contribution": 4.2
    },
    {
      "id": 2,
      "ingredient_id": 26,
      "name": "Onion",
      "category": "Vegetables",
      "quantity": 80.0,
      "unit": "g",
      "price_contribution": 2.8,
      "calories_contribution": 32.0,
      "protein_contribution": 0.9,
      "carbs_contribution": 7.4,
      "fat_contribution": 0.1,
      "fiber_contribution": 1.4
    }
  ],
  "nutrition_total": {
    "calories": 780.2,
    "protein": 19.3,
    "carbohydrates": 133.0,
    "fat": 19.7,
    "fiber": 9.2
  },
  "nutrition_per_serving": {
    "calories": 390.1,
    "protein": 9.7,
    "carbohydrates": 66.5,
    "fat": 9.9,
    "fiber": 4.6
  }
}
```
