import { useState, useEffect, useMemo } from 'react'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'
import RecipeModal from '../components/RecipeModal'

const MEAL_TYPES = ['all', 'breakfast', 'lunch', 'dinner', 'snack']
const DIETARY_OPTIONS = ['all', 'vegetarian', 'high_protein', 'vegan', 'non_vegetarian', 'egg']

export default function Recipes() {
  const [recipes, setRecipes] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Filters
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedMealType, setSelectedMealType] = useState('all')
  const [selectedDietary, setSelectedDietary] = useState('all')
  const [selectedCuisine, setSelectedCuisine] = useState('all')
  const [cuisinesList, setCuisinesList] = useState([])

  // Pagination
  const [page, setPage] = useState(1)
  const pageSize = 12

  // Selected Recipe for Modal
  const [activeRecipeId, setActiveRecipeId] = useState(null)

  useEffect(() => {
    const fetchAllRecipes = async () => {
      setLoading(true)
      setError(null)
      try {
        // Fetch recipes with higher limit for responsive client filtering
        const res = await fetch('http://localhost:8000/api/recipes?limit=150')
        if (!res.ok) throw new Error(`HTTP ${res.status}: Failed to load recipes`)
        const data = await res.json()
        setRecipes(data.items || [])

        // Extract unique cuisines
        const uniqueCuisines = Array.from(
          new Set((data.items || []).map((r) => r.cuisine).filter(Boolean))
        ).sort()
        setCuisinesList(uniqueCuisines)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchAllRecipes()
  }, [])

  // Filter recipes
  const filteredRecipes = useMemo(() => {
    return recipes.filter((r) => {
      // Meal Type
      if (selectedMealType !== 'all') {
        if (r.meal_type?.toLowerCase() !== selectedMealType.toLowerCase()) return false
      }

      // Dietary
      if (selectedDietary !== 'all') {
        const tags = r.dietary_tags?.map((t) => t.toLowerCase()) || []
        if (!tags.includes(selectedDietary.toLowerCase())) return false
      }

      // Cuisine
      if (selectedCuisine !== 'all') {
        if (r.cuisine !== selectedCuisine) return false
      }

      // Search term
      if (searchTerm.trim()) {
        const query = searchTerm.toLowerCase()
        const matchName = r.name?.toLowerCase().includes(query)
        const matchDesc = r.description?.toLowerCase().includes(query)
        const matchCuisine = r.cuisine?.toLowerCase().includes(query)
        if (!matchName && !matchDesc && !matchCuisine) return false
      }

      return true
    })
  }, [recipes, selectedMealType, selectedDietary, selectedCuisine, searchTerm])

  // Reset pagination on filter change
  useEffect(() => {
    setPage(1)
  }, [searchTerm, selectedMealType, selectedDietary, selectedCuisine])

  const totalPages = Math.ceil(filteredRecipes.length / pageSize) || 1
  const paginatedRecipes = useMemo(() => {
    const start = (page - 1) * pageSize
    return filteredRecipes.slice(start, start + pageSize)
  }, [filteredRecipes, page, pageSize])

  const getMealTypeColor = (type) => {
    switch (type?.toLowerCase()) {
      case 'breakfast':
        return 'bg-amber-100 text-amber-800'
      case 'lunch':
        return 'bg-emerald-100 text-emerald-800'
      case 'dinner':
        return 'bg-sky-100 text-sky-800'
      case 'snack':
        return 'bg-lime-100 text-lime-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="min-h-screen bg-surface flex flex-col">
      <Navbar />

      {/* Header Banner */}
      <div className="border-b border-border-light bg-gradient-to-b from-white to-cream/40 py-10 sm:py-14">
        <div className="mx-auto max-w-7xl px-6">
          <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full border border-primary-200/80 bg-primary-50 px-3.5 py-1 text-xs font-semibold text-primary-700 mb-3">
                <span className="h-1.5 w-1.5 rounded-full bg-primary-500" />
                Verified Food Database
              </div>
              <h1 className="text-3xl font-extrabold tracking-tight text-text-primary sm:text-4xl">
                Explore Indian Recipes
              </h1>
              <p className="mt-2 text-base text-text-secondary max-w-2xl">
                Browse 125 realistic household meals with exact ingredient measurements, macro breakdowns, and real-time cost estimations.
              </p>
            </div>
            <div className="rounded-2xl border border-border-light bg-white p-4 shadow-sm text-center shrink-0">
              <p className="text-xs font-semibold text-text-muted uppercase">Database Total</p>
              <p className="text-2xl font-extrabold text-primary-600">{recipes.length} Recipes</p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters & Content Section */}
      <div className="mx-auto max-w-7xl px-6 py-8 flex-1 w-full space-y-6">
        {/* Search & Filter Bar */}
        <div className="rounded-2xl border border-border-light bg-white p-5 shadow-sm space-y-4">
          {/* Top Row: Search Input & Cuisine Selector */}
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <svg
                className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                id="recipe-search-input"
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search recipes by name, ingredients, or cuisine (e.g. Poha, Rajma, Chicken)..."
                className="w-full rounded-xl border border-border-light bg-surface pl-10 pr-4 py-2.5 text-sm text-text-primary placeholder:text-text-muted focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20 transition-all"
              />
              {searchTerm && (
                <button
                  onClick={() => setSearchTerm('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-text-muted hover:text-text-primary"
                >
                  Clear
                </button>
              )}
            </div>

            <div className="sm:w-56">
              <select
                id="cuisine-filter-select"
                value={selectedCuisine}
                onChange={(e) => setSelectedCuisine(e.target.value)}
                className="w-full rounded-xl border border-border-light bg-surface px-3.5 py-2.5 text-sm text-text-primary focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20"
              >
                <option value="all">All Cuisines</option>
                {cuisinesList.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Meal Type Tabs */}
          <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-border-light/60">
            <span className="text-xs font-bold text-text-muted uppercase mr-1">Meal:</span>
            {MEAL_TYPES.map((type) => (
              <button
                key={type}
                onClick={() => setSelectedMealType(type)}
                className={`rounded-xl px-3.5 py-1.5 text-xs font-semibold capitalize transition-all ${
                  selectedMealType === type
                    ? 'bg-primary-600 text-white shadow-sm'
                    : 'bg-cream text-text-secondary hover:bg-cream-dark hover:text-text-primary'
                }`}
              >
                {type}
              </button>
            ))}

            <div className="hidden sm:block h-4 w-px bg-border-light mx-2" />

            <span className="text-xs font-bold text-text-muted uppercase mr-1">Diet:</span>
            {DIETARY_OPTIONS.map((tag) => (
              <button
                key={tag}
                onClick={() => setSelectedDietary(tag)}
                className={`rounded-xl px-3 py-1.5 text-xs font-semibold capitalize transition-all ${
                  selectedDietary === tag
                    ? 'bg-emerald-700 text-white shadow-sm'
                    : 'bg-cream text-text-secondary hover:bg-cream-dark hover:text-text-primary'
                }`}
              >
                {tag.replace('_', ' ')}
              </button>
            ))}

            {(searchTerm || selectedMealType !== 'all' || selectedDietary !== 'all' || selectedCuisine !== 'all') && (
              <button
                onClick={() => {
                  setSearchTerm('')
                  setSelectedMealType('all')
                  setSelectedDietary('all')
                  setSelectedCuisine('all')
                }}
                className="ml-auto text-xs font-semibold text-red-600 hover:text-red-700 underline"
              >
                Reset Filters
              </button>
            )}
          </div>
        </div>

        {/* Results Counter */}
        <div className="flex items-center justify-between text-xs text-text-muted px-1">
          <span>
            Showing <strong className="text-text-primary">{filteredRecipes.length}</strong> matching recipes
          </span>
          <span>Page {page} of {totalPages}</span>
        </div>

        {/* Loading / Error States */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-20 text-text-muted">
            <div className="h-10 w-10 animate-spin rounded-full border-3 border-primary-600 border-t-transparent mb-3" />
            <p className="text-sm font-medium">Loading recipe database...</p>
          </div>
        )}

        {error && (
          <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-center text-sm text-red-700">
            Error loading recipes: {error}
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && filteredRecipes.length === 0 && (
          <div className="rounded-3xl border border-border-light bg-white p-12 text-center">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-cream text-text-muted mb-4">
              <svg className="h-7 w-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-lg font-bold text-text-primary">No recipes match your criteria</h3>
            <p className="mt-1 text-sm text-text-secondary">Try clearing your filters or searching for something else.</p>
            <button
              onClick={() => {
                setSearchTerm('')
                setSelectedMealType('all')
                setSelectedDietary('all')
                setSelectedCuisine('all')
              }}
              className="mt-4 rounded-xl bg-primary-600 px-5 py-2.5 text-xs font-semibold text-white shadow-sm hover:bg-primary-700"
            >
              Show All Recipes
            </button>
          </div>
        )}

        {/* Recipe Grid */}
        {!loading && !error && paginatedRecipes.length > 0 && (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {paginatedRecipes.map((r) => (
              <div
                key={r.id}
                onClick={() => setActiveRecipeId(r.id)}
                className="group flex flex-col justify-between rounded-2xl border border-border-light bg-white p-5 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:border-primary-300 hover:shadow-lg hover:shadow-primary-600/5 cursor-pointer"
              >
                <div>
                  {/* Badges */}
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <span className={`rounded-full px-2.5 py-0.5 text-[11px] font-bold uppercase tracking-wider ${getMealTypeColor(r.meal_type)}`}>
                      {r.meal_type}
                    </span>
                    {r.cuisine && (
                      <span className="text-[11px] font-medium text-text-muted">
                        {r.cuisine}
                      </span>
                    )}
                  </div>

                  {/* Title */}
                  <h3 className="text-lg font-bold tracking-tight text-text-primary group-hover:text-primary-600 transition-colors">
                    {r.name}
                  </h3>

                  {/* Description */}
                  <p className="mt-2 text-xs leading-relaxed text-text-secondary line-clamp-2">
                    {r.description}
                  </p>

                  {/* Tags */}
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {r.dietary_tags?.slice(0, 3).map((tag) => (
                      <span
                        key={tag}
                        className="rounded-md bg-cream px-2 py-0.5 text-[10px] font-medium text-text-muted"
                      >
                        #{tag}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Bottom Meta & Price */}
                <div className="mt-5 pt-4 border-t border-border-light/70 flex items-center justify-between">
                  <div>
                    <span className="text-[10px] font-semibold text-text-muted uppercase">Estimated Cost</span>
                    <p className="text-base font-extrabold text-primary-700">
                      ₹{r.estimated_cost ? r.estimated_cost.toFixed(2) : '—'}
                    </p>
                  </div>
                  <div className="text-right">
                    <span className="text-[10px] text-text-muted">
                      {r.preparation_time + r.cooking_time} min &middot; {r.servings} serv
                    </span>
                    <p className="text-xs font-semibold text-primary-600 group-hover:translate-x-0.5 transition-transform">
                      View Details &rarr;
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Pagination Controls */}
        {!loading && !error && totalPages > 1 && (
          <div className="flex items-center justify-center gap-2 pt-6">
            <button
              id="recipes-prev-page-btn"
              disabled={page === 1}
              onClick={() => setPage((p) => Math.max(p - 1, 1))}
              className="rounded-xl border border-border-light bg-white px-4 py-2 text-xs font-semibold text-text-primary disabled:opacity-40 hover:bg-cream transition-all"
            >
              &larr; Previous
            </button>
            <span className="text-xs font-medium text-text-muted px-3">
              Page {page} of {totalPages}
            </span>
            <button
              id="recipes-next-page-btn"
              disabled={page === totalPages}
              onClick={() => setPage((p) => Math.min(p + 1, totalPages))}
              className="rounded-xl border border-border-light bg-white px-4 py-2 text-xs font-semibold text-text-primary disabled:opacity-40 hover:bg-cream transition-all"
            >
              Next &rarr;
            </button>
          </div>
        )}
      </div>

      {/* Recipe Detail Modal */}
      {activeRecipeId && (
        <RecipeModal
          recipeId={activeRecipeId}
          onClose={() => setActiveRecipeId(null)}
        />
      )}

      <Footer />
    </div>
  )
}
