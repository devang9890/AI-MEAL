import { useState, useEffect, useMemo } from 'react'
import { useAuth } from '@clerk/clerk-react'

export default function SwapMealModal({
  isOpen,
  onClose,
  slot,
  householdId,
  planId,
  onSwapSuccess,
}) {
  const { getToken } = useAuth()
  const [recipes, setRecipes] = useState([])
  const [loading, setLoading] = useState(false)
  const [swapping, setSwapping] = useState(false)
  const [error, setError] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedRecipeId, setSelectedRecipeId] = useState(null)

  useEffect(() => {
    if (!isOpen || !slot) return

    const fetchAlternatives = async () => {
      setLoading(true)
      setError(null)
      setSelectedRecipeId(null)
      try {
        const mealType = slot.meal_type?.toLowerCase() || ''
        const res = await fetch(`http://localhost:8000/api/recipes?limit=120&meal_type=${mealType}`)
        if (!res.ok) throw new Error('Failed to load alternative recipes')
        const data = await res.json()
        // Filter out current recipe
        const alternatives = (data.items || []).filter((r) => r.id !== slot.recipe_id)
        setRecipes(alternatives)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchAlternatives()
  }, [isOpen, slot])

  const filteredRecipes = useMemo(() => {
    if (!searchQuery.trim()) return recipes
    const q = searchQuery.toLowerCase()
    return recipes.filter(
      (r) =>
        r.name.toLowerCase().includes(q) ||
        r.cuisine?.toLowerCase().includes(q) ||
        r.dietary_tags?.some((t) => t.toLowerCase().includes(q))
    )
  }, [recipes, searchQuery])

  const handleConfirmSwap = async () => {
    if (!selectedRecipeId || swapping) return
    setSwapping(true)
    setError(null)
    try {
      const token = await getToken()
      const res = await fetch(
        `http://localhost:8000/api/households/${householdId}/plans/${planId}/swap-meal`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            day: slot.day,
            meal_type: slot.meal_type,
            new_recipe_id: selectedRecipeId,
          }),
        }
      )

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData.detail || 'Failed to swap meal')
      }

      const updatedMeal = await res.json()
      onSwapSuccess(updatedMeal)
      onClose()
    } catch (err) {
      setError(err.message)
    } finally {
      setSwapping(false)
    }
  }

  if (!isOpen || !slot) return null

  const currentCost = slot.cost || 0
  const selectedRecipe = recipes.find((r) => r.id === selectedRecipeId)

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Modal Dialog */}
      <div className="relative z-10 w-full max-w-2xl overflow-hidden rounded-2xl bg-white shadow-2xl border border-border-light flex flex-col max-h-[88vh]">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border-light px-6 py-4 bg-cream/50">
          <div>
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center rounded-md bg-primary-100 px-2 py-0.5 text-xs font-semibold uppercase tracking-wider text-primary-800">
                {slot.day} · {slot.meal_type}
              </span>
              <h3 className="text-lg font-bold text-text-primary">Swap Meal</h3>
            </div>
            <p className="text-xs text-text-secondary mt-0.5">
              Current: <strong className="text-text-primary">{slot.recipe_name}</strong> (₹{currentCost.toFixed(0)})
            </p>
          </div>
          <button
            onClick={onClose}
            className="flex h-8 w-8 items-center justify-center rounded-lg text-text-muted hover:bg-cream-dark transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Search and Filters */}
        <div className="px-6 py-3 border-b border-border-light bg-surface">
          <input
            type="text"
            placeholder="Search recipes by name, cuisine, tag..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-xl border border-border px-4 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20"
          />
        </div>

        {/* Recipe list */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-2">
          {error && (
            <div className="rounded-xl bg-red-50 p-3 text-sm text-red-700 border border-red-200">
              {error}
            </div>
          )}

          {loading ? (
            <div className="flex flex-col items-center justify-center py-12 text-text-muted">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary-500 border-t-transparent mb-3" />
              <p className="text-sm">Loading eligible {slot.meal_type} recipes...</p>
            </div>
          ) : filteredRecipes.length === 0 ? (
            <div className="text-center py-10 text-text-muted">
              <p>No matching alternative recipes found.</p>
            </div>
          ) : (
            filteredRecipes.map((r) => {
              const isSelected = selectedRecipeId === r.id
              const costDiff = (r.estimated_cost || 0) - currentCost
              return (
                <div
                  key={r.id}
                  onClick={() => setSelectedRecipeId(r.id)}
                  className={`flex items-center justify-between rounded-xl p-3.5 border cursor-pointer transition-all ${
                    isSelected
                      ? 'border-primary-600 bg-primary-50/70 shadow-sm'
                      : 'border-border-light hover:border-primary-300 hover:bg-cream/40'
                  }`}
                >
                  <div className="flex-1 min-w-0 pr-3">
                    <div className="flex items-center gap-2">
                      <h4 className="text-sm font-semibold text-text-primary truncate">
                        {r.name}
                      </h4>
                      {r.cuisine && (
                        <span className="text-[11px] px-2 py-0.5 rounded-full bg-cream-dark text-text-secondary font-medium">
                          {r.cuisine}
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-3 mt-1 text-xs text-text-secondary">
                      {r.nutrition && (
                        <>
                          <span>🔥 {Math.round(r.nutrition.calories || 0)} kcal</span>
                          <span>🥩 {Math.round(r.nutrition.protein_g || 0)}g protein</span>
                        </>
                      )}
                      <span>⏱️ {(r.preparation_time || 0) + (r.cooking_time || 0)} min</span>
                    </div>

                    {r.dietary_tags && r.dietary_tags.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-1.5">
                        {r.dietary_tags.slice(0, 3).map((tag, idx) => (
                          <span
                            key={idx}
                            className="text-[10px] px-1.5 py-0.2 rounded bg-surface border border-border-light text-text-muted"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="text-right flex flex-col items-end justify-center shrink-0">
                    <span className="text-sm font-bold text-text-primary">
                      ₹{Math.round(r.estimated_cost || 0)}
                    </span>
                    <span
                      className={`text-[11px] font-medium ${
                        costDiff > 0
                          ? 'text-amber-600'
                          : costDiff < 0
                          ? 'text-emerald-600'
                          : 'text-text-muted'
                      }`}
                    >
                      {costDiff > 0
                        ? `+₹${Math.round(costDiff)}`
                        : costDiff < 0
                        ? `-₹${Math.round(Math.abs(costDiff))}`
                        : 'Same cost'}
                    </span>
                    <input
                      type="radio"
                      name="selectedRecipe"
                      checked={isSelected}
                      onChange={() => setSelectedRecipeId(r.id)}
                      className="mt-2 text-primary-600 focus:ring-primary-500"
                    />
                  </div>
                </div>
              )
            })
          )}
        </div>

        {/* Footer actions */}
        <div className="border-t border-border-light px-6 py-4 bg-cream/30 flex items-center justify-between">
          <div>
            {selectedRecipe && (
              <p className="text-xs text-text-secondary">
                Selected: <strong className="text-text-primary">{selectedRecipe.name}</strong>
              </p>
            )}
          </div>
          <div className="flex gap-2">
            <button
              onClick={onClose}
              disabled={swapping}
              className="rounded-xl px-4 py-2 text-sm font-semibold text-text-secondary hover:bg-cream-dark transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleConfirmSwap}
              disabled={!selectedRecipeId || swapping}
              className="flex items-center gap-2 rounded-xl bg-primary-600 px-5 py-2 text-sm font-semibold text-white shadow-sm shadow-primary-600/20 hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {swapping ? (
                <>
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  <span>Swapping...</span>
                </>
              ) : (
                'Confirm Swap'
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
