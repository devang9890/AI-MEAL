import { useState, useEffect } from 'react'

export default function RecipeModal({ recipeId, onClose }) {
  const [recipe, setRecipe] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showPerServing, setShowPerServing] = useState(true)

  useEffect(() => {
    if (!recipeId) return

    const fetchDetail = async () => {
      setLoading(true)
      setError(null)
      try {
        const res = await fetch(`http://localhost:8000/api/recipes/${recipeId}`)
        if (!res.ok) throw new Error(`HTTP ${res.status}: Failed to load recipe`)
        const data = await res.json()
        setRecipe(data)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchDetail()
  }, [recipeId])

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [onClose])

  if (!recipeId) return null

  const activeNutrition = showPerServing
    ? recipe?.nutrition_per_serving
    : recipe?.nutrition_total

  return (
    <div
      id="recipe-detail-modal-backdrop"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm transition-all"
      onClick={(e) => {
        if (e.target.id === 'recipe-detail-modal-backdrop') onClose()
      }}
    >
      <div className="relative flex max-h-[90vh] w-full max-w-3xl flex-col overflow-hidden rounded-3xl bg-white shadow-2xl">
        {/* Header Bar */}
        <div className="flex items-center justify-between border-b border-border-light/80 px-6 py-4">
          <div className="flex items-center gap-2">
            <span className="rounded-full bg-primary-100 px-3 py-1 text-xs font-bold uppercase tracking-wider text-primary-700">
              {recipe?.meal_type || 'Recipe'}
            </span>
            {recipe?.cuisine && (
              <span className="rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700 border border-amber-200/60">
                {recipe.cuisine}
              </span>
            )}
          </div>
          <button
            id="close-recipe-modal-btn"
            onClick={onClose}
            className="flex h-9 w-9 items-center justify-center rounded-full text-text-muted transition-colors hover:bg-cream hover:text-text-primary"
            aria-label="Close modal"
          >
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Modal Body */}
        <div className="overflow-y-auto px-6 py-6 space-y-6">
          {loading && (
            <div className="flex flex-col items-center justify-center py-16 text-text-muted">
              <div className="h-8 w-8 animate-spin rounded-full border-3 border-primary-600 border-t-transparent mb-3" />
              <p className="text-sm">Loading recipe details...</p>
            </div>
          )}

          {error && (
            <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-600">
              Failed to load recipe: {error}
            </div>
          )}

          {recipe && (
            <>
              {/* Title & Description */}
              <div>
                <h2 className="text-2xl font-bold tracking-tight text-text-primary sm:text-3xl">
                  {recipe.name}
                </h2>
                <p className="mt-2 text-sm leading-relaxed text-text-secondary">
                  {recipe.description}
                </p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {recipe.dietary_tags?.map((tag) => (
                    <span
                      key={tag}
                      className="rounded-lg bg-cream px-2.5 py-1 text-xs font-medium text-text-secondary border border-border-light"
                    >
                      #{tag}
                    </span>
                  ))}
                </div>
              </div>

              {/* Key Quick Stats */}
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                <div className="rounded-2xl border border-border-light bg-cream/50 p-3.5 text-center">
                  <p className="text-[11px] font-semibold text-text-muted uppercase">Servings</p>
                  <p className="mt-1 text-lg font-bold text-text-primary">{recipe.servings} people</p>
                </div>
                <div className="rounded-2xl border border-border-light bg-cream/50 p-3.5 text-center">
                  <p className="text-[11px] font-semibold text-text-muted uppercase">Prep Time</p>
                  <p className="mt-1 text-lg font-bold text-text-primary">{recipe.preparation_time} min</p>
                </div>
                <div className="rounded-2xl border border-border-light bg-cream/50 p-3.5 text-center">
                  <p className="text-[11px] font-semibold text-text-muted uppercase">Cook Time</p>
                  <p className="mt-1 text-lg font-bold text-text-primary">{recipe.cooking_time} min</p>
                </div>
                <div className="rounded-2xl border border-primary-200/80 bg-primary-50/50 p-3.5 text-center">
                  <p className="text-[11px] font-semibold text-primary-700 uppercase">Estimated Cost</p>
                  <p className="mt-1 text-lg font-extrabold text-primary-700">₹{recipe.estimated_cost?.toFixed(2)}</p>
                </div>
              </div>

              {/* Nutrition Card with Toggle */}
              <div className="rounded-2xl border border-border-light bg-white p-5 shadow-sm">
                <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
                  <div>
                    <h3 className="text-sm font-bold text-text-primary">Nutritional Breakdown</h3>
                    <p className="text-xs text-text-muted">Calculated from raw ingredient composition</p>
                  </div>
                  <div className="inline-flex rounded-xl bg-cream p-1 border border-border-light">
                    <button
                      id="toggle-per-serving-btn"
                      onClick={() => setShowPerServing(true)}
                      className={`rounded-lg px-3 py-1 text-xs font-semibold transition-all ${
                        showPerServing
                          ? 'bg-white text-primary-700 shadow-sm'
                          : 'text-text-muted hover:text-text-primary'
                      }`}
                    >
                      Per Serving
                    </button>
                    <button
                      id="toggle-total-recipe-btn"
                      onClick={() => setShowPerServing(false)}
                      className={`rounded-lg px-3 py-1 text-xs font-semibold transition-all ${
                        !showPerServing
                          ? 'bg-white text-primary-700 shadow-sm'
                          : 'text-text-muted hover:text-text-primary'
                      }`}
                    >
                      Total Recipe
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-5">
                  <div className="rounded-xl bg-amber-50/60 border border-amber-100 p-3 text-center">
                    <span className="text-[10px] font-bold text-amber-800 uppercase">Calories</span>
                    <p className="text-base font-extrabold text-amber-900">{activeNutrition?.calories} <span className="text-xs font-normal">kcal</span></p>
                  </div>
                  <div className="rounded-xl bg-emerald-50/60 border border-emerald-100 p-3 text-center">
                    <span className="text-[10px] font-bold text-emerald-800 uppercase">Protein</span>
                    <p className="text-base font-extrabold text-emerald-900">{activeNutrition?.protein}g</p>
                  </div>
                  <div className="rounded-xl bg-sky-50/60 border border-sky-100 p-3 text-center">
                    <span className="text-[10px] font-bold text-sky-800 uppercase">Carbs</span>
                    <p className="text-base font-extrabold text-sky-900">{activeNutrition?.carbohydrates}g</p>
                  </div>
                  <div className="rounded-xl bg-rose-50/60 border border-rose-100 p-3 text-center">
                    <span className="text-[10px] font-bold text-rose-800 uppercase">Fat</span>
                    <p className="text-base font-extrabold text-rose-900">{activeNutrition?.fat}g</p>
                  </div>
                  <div className="rounded-xl bg-teal-50/60 border border-teal-100 p-3 text-center">
                    <span className="text-[10px] font-bold text-teal-800 uppercase">Fiber</span>
                    <p className="text-base font-extrabold text-teal-900">{activeNutrition?.fiber}g</p>
                  </div>
                </div>
              </div>

              {/* Ingredients List */}
              <div>
                <h3 className="text-sm font-bold text-text-primary mb-3">
                  Ingredients ({recipe.ingredients?.length})
                </h3>
                <div className="overflow-hidden rounded-2xl border border-border-light">
                  <table className="w-full text-left text-xs">
                    <thead className="border-b border-border-light bg-cream/70 text-text-muted">
                      <tr>
                        <th className="px-4 py-2.5 font-semibold">Ingredient</th>
                        <th className="px-3 py-2.5 font-semibold">Portion</th>
                        <th className="px-3 py-2.5 font-semibold">Calories</th>
                        <th className="px-3 py-2.5 font-semibold">Protein</th>
                        <th className="px-4 py-2.5 text-right font-semibold">Cost (₹)</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border-light/60 bg-white">
                      {recipe.ingredients?.map((item) => (
                        <tr key={item.id} className="hover:bg-cream/30 transition-colors">
                          <td className="px-4 py-2.5 font-medium text-text-primary">
                            {item.name}
                            <span className="ml-1.5 text-[10px] text-text-muted">({item.category})</span>
                          </td>
                          <td className="px-3 py-2.5 font-semibold text-text-secondary">
                            {item.quantity} {item.unit}
                          </td>
                          <td className="px-3 py-2.5 text-text-secondary">
                            {item.calories_contribution} kcal
                          </td>
                          <td className="px-3 py-2.5 text-text-secondary">
                            {item.protein_contribution}g
                          </td>
                          <td className="px-4 py-2.5 text-right font-semibold text-primary-700">
                            ₹{item.price_contribution.toFixed(2)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Instructions */}
              <div>
                <h3 className="text-sm font-bold text-text-primary mb-3">Preparation Instructions</h3>
                <div className="rounded-2xl border border-border-light bg-cream/30 p-4 text-sm leading-relaxed text-text-secondary space-y-2">
                  {recipe.instructions}
                </div>
              </div>
            </>
          )}
        </div>

        {/* Footer Bar */}
        <div className="flex justify-end border-t border-border-light/80 px-6 py-4 bg-white">
          <button
            id="modal-close-footer-btn"
            onClick={onClose}
            className="rounded-xl border border-border-light bg-cream px-5 py-2.5 text-sm font-semibold text-text-primary transition-all hover:bg-cream-dark"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
