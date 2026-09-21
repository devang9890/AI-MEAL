# 🥗 AI Meal Planner

> **Smart, budget-friendly, and nutritionally balanced meal planning for households.**  
> Powered by mathematical linear programming (PuLP), Indian Food Composition standards (IFCT / ICMR), and conversational AI.

---

## 📸 Application Preview

| **Dashboard & Daily Overview** | **Family & Nutrition Hub** |
|:---:|:---:|
| ![Dashboard](SCREENSHOTS/DASHBOARD.png) | ![Family Hub](SCREENSHOTS/FAMILY%20HUB.png) |

| **7-Day Weekly Meal Schedule** | **Explore Indian Recipes** |
|:---:|:---:|
| ![Weekly Meal Plan](SCREENSHOTS/WEEKLY%20MEAL%20PLAN.png) | ![Explore Recipes](SCREENSHOTS/EXPLORE%20RECEPIES.png) |

| **Ingredients & Pricing Catalog** |
|:---:|
| ![Ingredients Catalog](SCREENSHOTS/INGREDIENTS%20CATALOG.png) |

---

## ✨ Key Features (In Simple Words)

### 1. 🏠 Family & Nutrition Hub
- **Individual Health Profiles**: Add family members with their age, gender, height, weight, activity level, and dietary choices (Vegetarian, Vegan, Eggitarian, Non-Vegetarian).
- **Automatic Calorie & Macro Calculation**: Automatically calculates each person's daily Basal Metabolic Rate (BMR) and Total Daily Energy Expenditure (TDEE) using the scientifically recognized **Mifflin–St Jeor** equation.
- **Combined Household Demand**: Computes the daily total target for calories, protein, carbs, healthy fats, and dietary fiber required by your entire family.

### 2. 📅 Smart 7-Day Weekly Meal Planner
- **Automated Scheduling (21 Meals)**: Generates a full week of breakfast, lunch, and dinner with a single click.
- **Cost & Budget Optimization**: Powered by **PuLP Integer Linear Programming (ILP)**, the planner picks recipes that hit your family's nutritional targets while keeping grocery costs within your weekly budget.
- **Budget Utilization Tracker**: Live progress bar showing total estimated cost vs. your weekly budget limit.
- **Easy Meal Swapping**: Don't feel like eating a recommended meal? Swap any slot with alternatives that fit the same meal slot and dietary restrictions.
- **Transparent Selection Explanations**: Understand *why* each meal was picked (e.g., high-protein, budget-friendly, or essential micronutrient balance).

### 3. 🍛 Indian Recipe Explorer (125+ Dishes)
- **Authentic Household Meals**: Includes curated North Indian, South Indian, Maharashtrian, and Gujarati dishes (from Rajma Masala and Poha to Palak Paneer and Soya Bhurji).
- **Exact Portions & Costing**: Shows prep time, cooking time, step-by-step instructions, exact ingredient weights, and real-time cost per plate.
- **Instant Filters & Search**: Search dishes by ingredient, cuisine, meal slot (Breakfast, Lunch, Dinner, Snack), or dietary preference.

### 4. 🛒 Automated Grocery Shopping List
- **One-Click Shopping List**: Compiles all ingredients needed for your entire 7-day plan, summing up total quantities (grams, kg, ml).
- **Aisle-Wise Categorization**: Organizes items into clear categories (Grains, Pulses, Dairy, Vegetables, Spices, etc.).
- **Interactive Checklist & Quick Copy**: Check off items as you shop in the market, or copy the entire list to clipboard with one click to paste into WhatsApp or notes.

### 5. 🌾 Ingredients & Nutrition Catalog (83 Items)
- **IFCT / ICMR Standardized Data**: High-quality nutritional facts normalized per 100g or 100ml.
- **Market Price Benchmarks**: Realistic benchmark prices in Indian Rupees (₹) to accurately project your grocery bill.
- **Health Badges**: Quick filters for High-Protein and High-Fiber ingredients.

### 6. 🤖 Context-Aware AI Chat Assistant
- **Personalized Assistant**: Powered by **Groq LLM**, the floating AI assistant answers questions about recipe substitutions, ingredient nutrition, budget savings, and family meal plans.
- **Context-Aware**: Understands your household's active dietary restrictions and members' nutrition goals.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 18, Vite, Tailwind CSS, Lucide Icons |
| **Authentication** | Clerk Auth (JWT verification, secure multi-tenant isolation) |
| **Backend API** | FastAPI (Python 3.10+), Pydantic v2 |
| **Database & ORM** | PostgreSQL (Neon Serverless), SQLAlchemy, Alembic Migrations |
| **Optimization Engine** | PuLP (Integer Linear Programming solver) |
| **AI Chatbot** | Groq API (`llama-3.3-70b-versatile`) |

---

## 🚀 Getting Started

### Prerequisites
- Node.js 18+ and npm
- Python 3.10+
- Neon PostgreSQL database URL
- Clerk Account (Publishable & Secret keys)

---

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv .venv
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file from template
copy .env.example .env
```

Fill in your `.env` credentials:
```env
DATABASE_URL=postgresql://user:password@host/neondb?sslmode=require
CLERK_SECRET_KEY=sk_test_...
VITE_CLERK_PUBLISHABLE_KEY=pk_test_...
GROQ_API_KEY=gsk_...
```

Run database migrations and seed food data:
```bash
# Run migrations
alembic upgrade head

# Seed 83 ingredients and 125+ recipes
python -m app.seed.seed_database

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```
Backend API will be live at `http://localhost:8000` (Docs at `http://localhost:8000/docs`).

---

### 2. Frontend Setup

```bash
# Open a new terminal and navigate to frontend directory
cd frontend

# Install packages
npm install

# Create .env.local file
# Add: VITE_CLERK_PUBLISHABLE_KEY=pk_test_...

# Start dev server
npm run dev
```
Frontend will be live at `http://localhost:5173`.

---

## 📁 Project Structure

```
ai-meal/
├── SCREENSHOTS/             # Application UI screenshots
│   ├── DASHBOARD.png
│   ├── FAMILY HUB.png
│   ├── WEEKLY MEAL PLAN.png
│   ├── EXPLORE RECEPIES.png
│   └── INGREDIENTS CATALOG.png
├── backend/
│   ├── app/
│   │   ├── core/            # Database config, Clerk auth & security
│   │   ├── models/          # SQLAlchemy schemas (User, Household, Member, Recipe, etc.)
│   │   ├── routers/         # API endpoints (Food, Household, Meal Plan, Chat)
│   │   ├── schemas/         # Pydantic validation models
│   │   ├── seed/            # Seed data for 83 ingredients & 125 recipes
│   │   └── services/        # ILP Optimizer (PuLP), Nutrition Engine, AI Chatbot (Groq)
│   ├── alembic/             # Database migration files
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/      # UI components, modals, and AI chat widget
│   │   ├── pages/           # Landing, Household, MealPlan, Recipes, Ingredients, GroceryList
│   │   └── App.jsx
│   └── package.json
└── README.md
```

---

## 🛡️ Disclaimer
*Nutritional values, meal suggestions, and cost estimates provided by this platform are algorithmic baselines intended for household planning and educational demonstration. They do not constitute formal medical or dietary advice.*
