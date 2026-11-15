"""Curated food-allergy/intolerance and diet-relevant condition catalog.

This catalog is intentionally educational.  It provides selection labels and a
small set of conservative, transparent planner safeguards; it is not a
diagnostic tool or a replacement for individual dietetic advice.
"""
from __future__ import annotations

from typing import Dict, List


def _entries(category: str, kind: str, names: List[str]) -> List[Dict[str, str]]:
    return [{"id": name.lower().replace(" ", "-").replace("/", "-"), "name": name,
             "category": category, "kind": kind} for name in names]


ALLERGY_CATALOG: List[Dict[str, str]] = []
ALLERGY_CATALOG += _entries("Dairy and milk", "allergy", [
    "Cow's milk allergy", "Casein allergy", "Whey allergy", "Goat's milk allergy", "Sheep's milk allergy",
    "Butter allergy", "Cheese allergy", "Yogurt allergy", "Ghee allergy", "Milk protein allergy",
])
ALLERGY_CATALOG += _entries("Nuts and tree nuts", "allergy", [
    "Peanut allergy", "Almond allergy", "Cashew allergy", "Walnut allergy", "Pistachio allergy", "Pecan allergy",
    "Hazelnut allergy", "Brazil nut allergy", "Macadamia allergy", "Pine nut allergy", "Chestnut allergy",
])
ALLERGY_CATALOG += _entries("Seeds and legumes", "allergy", [
    "Sesame allergy", "Mustard allergy", "Sunflower seed allergy", "Poppy seed allergy", "Chia seed allergy",
    "Flaxseed allergy", "Pumpkin seed allergy", "Soy allergy", "Chickpea allergy", "Lentil allergy",
    "Pea allergy", "Fenugreek allergy",
])
ALLERGY_CATALOG += _entries("Seafood and shellfish", "allergy", [
    "Fish allergy", "Shellfish allergy", "Shrimp allergy", "Prawn allergy", "Crab allergy", "Lobster allergy",
    "Mollusc allergy", "Oyster allergy", "Mussel allergy", "Squid allergy", "Anchovy allergy", "Tuna allergy",
])
ALLERGY_CATALOG += _entries("Grain and gluten related", "allergy", [
    "Wheat allergy", "Barley allergy", "Rye allergy", "Oat allergy", "Rice allergy", "Corn allergy",
    "Buckwheat allergy", "Millet allergy", "Quinoa allergy", "Gluten sensitivity", "Non-celiac gluten sensitivity",
    "Celiac disease",
])
ALLERGY_CATALOG += _entries("Fruit and vegetable", "allergy", [
    "Banana allergy", "Kiwi allergy", "Mango allergy", "Citrus allergy", "Apple allergy", "Peach allergy",
    "Pineapple allergy", "Avocado allergy", "Tomato allergy", "Potato allergy", "Eggplant allergy", "Mushroom allergy",
    "Garlic allergy", "Onion allergy", "Celery allergy", "Carrot allergy", "Spinach allergy", "Coconut allergy",
])
ALLERGY_CATALOG += _entries("Meat, poultry and egg", "allergy", [
    "Egg allergy", "Chicken allergy", "Turkey allergy", "Duck allergy", "Beef allergy", "Pork allergy",
    "Lamb allergy", "Gelatin allergy", "Alpha-gal syndrome", "Red meat allergy",
])
ALLERGY_CATALOG += _entries("Additives and preservatives", "sensitivity", [
    "Sulfite sensitivity", "MSG sensitivity", "Tartrazine sensitivity", "Benzoate sensitivity", "Nitrate sensitivity",
    "Nitrite sensitivity", "Aspartame sensitivity", "Artificial colour sensitivity", "Artificial flavour sensitivity",
    "Food dye sensitivity", "Salicylate sensitivity", "Histamine intolerance",
])
ALLERGY_CATALOG += _entries("Food intolerances", "intolerance", [
    "Lactose intolerance", "Fructose intolerance", "Sucrose intolerance", "Sorbitol intolerance", "FODMAP sensitivity",
    "Gluten intolerance", "Caffeine intolerance", "Alcohol intolerance", "Oral allergy syndrome", "Food protein intolerance",
    "Tyramine sensitivity", "Nickel food sensitivity",
])


DISEASE_CATALOG: List[Dict[str, str]] = []
DISEASE_CATALOG += _entries("Endocrine and metabolic", "condition", [
    "Type 1 diabetes", "Type 2 diabetes", "Prediabetes", "Gestational diabetes", "Insulin resistance",
    "Metabolic syndrome", "Obesity", "Underweight", "Hypothyroidism", "Hyperthyroidism", "Polycystic ovary syndrome",
    "Gout", "Hyperuricemia", "Phenylketonuria", "Galactosemia",
])
DISEASE_CATALOG += _entries("Cardiovascular", "condition", [
    "Hypertension", "Hypotension", "Coronary artery disease", "Heart failure", "High cholesterol", "High triglycerides",
    "Atherosclerosis", "Peripheral artery disease", "Atrial fibrillation", "Cardiomyopathy", "Stroke history",
    "Transient ischemic attack", "Pulmonary hypertension",
])
DISEASE_CATALOG += _entries("Gastrointestinal and digestive", "condition", [
    "Celiac disease", "Irritable bowel syndrome", "Inflammatory bowel disease", "Crohn's disease", "Ulcerative colitis",
    "Gastroesophageal reflux disease", "Peptic ulcer disease", "Gastritis", "Chronic constipation", "Chronic diarrhea",
    "Diverticular disease", "Pancreatitis", "Gastroparesis", "Eosinophilic esophagitis", "Short bowel syndrome",
])
DISEASE_CATALOG += _entries("Kidney and urinary", "condition", [
    "Chronic kidney disease", "Kidney failure", "Kidney stones", "Nephrotic syndrome", "Polycystic kidney disease",
    "Urinary tract infection", "Dialysis", "Acute kidney injury", "Proteinuria", "Hyperkalemia",
])
DISEASE_CATALOG += _entries("Liver and gallbladder", "condition", [
    "Non-alcoholic fatty liver disease", "Fatty liver disease", "Cirrhosis", "Hepatitis B", "Hepatitis C", "Gallstones",
    "Cholecystitis", "Pancreatic insufficiency", "Wilson disease", "Hemochromatosis",
])
DISEASE_CATALOG += _entries("Autoimmune and inflammatory", "condition", [
    "Rheumatoid arthritis", "Systemic lupus erythematosus", "Multiple sclerosis", "Psoriasis", "Psoriatic arthritis",
    "Hashimoto thyroiditis", "Celiac disease", "Sjögren syndrome", "Scleroderma", "Ankylosing spondylitis",
])
DISEASE_CATALOG += _entries("Nutritional and blood", "condition", [
    "Iron deficiency anemia", "Vitamin B12 deficiency", "Folate deficiency", "Vitamin D deficiency", "Calcium deficiency",
    "Magnesium deficiency", "Zinc deficiency", "Malnutrition", "Sarcopenia", "Osteopenia",
])
DISEASE_CATALOG += _entries("Bone and joint", "condition", [
    "Osteoporosis", "Osteoarthritis", "Rheumatoid arthritis", "Gout", "Chronic back pain", "Fibromyalgia",
    "Sarcopenia", "Fracture recovery", "Joint hypermobility",
])
DISEASE_CATALOG += _entries("Neurological", "condition", [
    "Migraine", "Epilepsy", "Parkinson disease", "Alzheimer disease", "Dementia", "Multiple sclerosis", "Celiac neuropathy",
    "Peripheral neuropathy", "Dysphagia", "Traumatic brain injury",
])
DISEASE_CATALOG += _entries("Respiratory and other", "condition", [
    "Asthma", "Chronic obstructive pulmonary disease", "Sleep apnea", "Cystic fibrosis", "Tuberculosis recovery",
    "Cancer treatment", "Eating disorder recovery", "Pregnancy", "Breastfeeding", "Food insecurity",
])
DISEASE_CATALOG += _entries("Hormonal and reproductive", "condition", [
    "Endometriosis", "Menopause", "Premenstrual dysphoric disorder", "Infertility", "Gestational hypertension",
    "Preeclampsia history", "Amenorrhea", "Hyperprolactinemia", "Adrenal insufficiency", "Cushing syndrome",
])


# Conditions whose dietary management depends on laboratory values, medicines or
# disease stage.  The app keeps their selection and shows a clear caution rather
# than pretending its recipe data can provide a clinical prescription.
CLINICIAN_REVIEW_CONDITIONS = {
    "Chronic kidney disease", "Kidney failure", "Dialysis", "Acute kidney injury", "Hyperkalemia",
    "Type 1 diabetes", "Gestational diabetes", "Pregnancy", "Breastfeeding", "Cancer treatment",
    "Eating disorder recovery", "Phenylketonuria", "Galactosemia", "Cystic fibrosis", "Dysphagia",
    "Cirrhosis", "Heart failure", "Pancreatitis", "Short bowel syndrome",
}

# Terms are matched against the recipe's actual ingredient names, not just the
# recipe title. They intentionally cover only clear ingredient relationships.
ALLERGY_INGREDIENT_TERMS = {
    "Cow's milk allergy": ["milk", "paneer", "curd", "yogurt", "cheese", "ghee", "butter", "cream"],
    "Casein allergy": ["milk", "paneer", "curd", "yogurt", "cheese", "ghee", "butter", "cream"],
    "Whey allergy": ["milk", "paneer", "curd", "yogurt", "cheese", "cream"],
    "Lactose intolerance": ["milk", "paneer", "curd", "yogurt", "cheese", "cream"],
    "Peanut allergy": ["peanut"], "Almond allergy": ["almond"], "Cashew allergy": ["cashew"],
    "Walnut allergy": ["walnut"], "Pistachio allergy": ["pistachio"], "Sesame allergy": ["sesame"],
    "Mustard allergy": ["mustard"], "Soy allergy": ["soy", "soya"], "Chickpea allergy": ["chickpea", "besan"],
    "Lentil allergy": ["dal", "lentil"], "Fish allergy": ["fish"], "Shellfish allergy": ["prawn", "shrimp", "crab", "lobster"],
    "Shrimp allergy": ["prawn", "shrimp"], "Prawn allergy": ["prawn", "shrimp"], "Egg allergy": ["egg"],
    "Wheat allergy": ["wheat", "atta", "maida", "semolina", "vermicelli"],
    "Celiac disease": ["wheat", "atta", "maida", "semolina", "barley", "rye", "vermicelli"],
    "Gluten intolerance": ["wheat", "atta", "maida", "semolina", "barley", "rye", "vermicelli"],
    "Non-celiac gluten sensitivity": ["wheat", "atta", "maida", "semolina", "barley", "rye", "vermicelli"],
    "Banana allergy": ["banana"], "Tomato allergy": ["tomato"], "Potato allergy": ["potato"],
    "Onion allergy": ["onion"], "Garlic allergy": ["garlic"], "Mushroom allergy": ["mushroom"],
}

CONDITION_RULES = {
    "Type 2 diabetes": {"carbs_factor": 0.85, "note": "Carbohydrate target is conservatively reduced; portion and medication needs still require clinician guidance."},
    "Prediabetes": {"carbs_factor": 0.85, "note": "Carbohydrate target is conservatively reduced; favouring whole-food choices is still not a substitute for personalised care."},
    "Hypertension": {"max_salt_g": 3.0, "note": "Recipes with a high added-salt proxy are excluded; packaged-food sodium is not modelled."},
    "High cholesterol": {"fat_factor": 0.85, "note": "Total-fat target is conservatively reduced; the catalog does not model saturated fat."},
    "High triglycerides": {"carbs_factor": 0.85, "note": "Carbohydrate target is conservatively reduced; alcohol and added-sugar data are not fully modelled."},
    "Celiac disease": {"avoid_terms": ALLERGY_INGREDIENT_TERMS["Celiac disease"], "note": "Only recipes without detected gluten ingredients are considered; cross-contamination cannot be verified."},
    "Gastroesophageal reflux disease": {"avoid_terms": ["green chilli", "red chilli", "garam masala"], "note": "Potentially spicy recipes are excluded as a conservative comfort measure."},
}
