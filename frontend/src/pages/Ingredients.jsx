import { useState, useEffect, useMemo } from 'react'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'

const CATEGORIES = [
  'all',
  'Grains & Cereals',
  'Pulses & Legumes',
  'Vegetables',
  'Dairy',
  'Poultry & Meat',
  'Seafood',
  'Nuts & Seeds',
  'Oils & Fats',
  'Spices & Seasonings',
  'Fruits',
]

export default function Ingredients() {
  const [ingredients, setIngredients] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('all')

  useEffect(() => {
    const fetchIngredients = async () => {
      setLoading(true)
      setError(null)
      try {
        const res = await fetch('http://localhost:8000/api/ingredients?limit=150')
        if (!res.ok) throw new Error(`HTTP ${res.status}: Failed to load ingredients`)
        const data = await res.json()
        setIngredients(data.items || [])
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchIngredients()
  }, [])

  const filtered = useMemo(() => {
    return ingredients.filter((ing) => {
      if (selectedCategory !== 'all') {
        if (ing.category?.toLowerCase() !== selectedCategory.toLowerCase()) return false
      }

      if (searchTerm.trim()) {
        const q = searchTerm.toLowerCase()
        const matchName = ing.name?.toLowerCase().includes(q)
        const matchCat = ing.category?.toLowerCase().includes(q)
        if (!matchName && !matchCat) return false
      }

      return true
    })
  }, [ingredients, selectedCategory, searchTerm])

  // Summary Metrics
  const highProteinCount = useMemo(() => {
    return ingredients.filter((i) => (i.protein || 0) >= 15).length
  }, [ingredients])

  const highFiberCount = useMemo(() => {
    return ingredients.filter((i) => (i.fiber || 0) >= 8).length
  }, [ingredients])

  return (
    <div className="min-h-screen bg-surface flex flex-col">
      <Navbar />

      {/* Header */}
      <div className="border-b border-border-light bg-gradient-to-b from-white to-cream/40 py-10 sm:py-14">
        <div className="mx-auto max-w-7xl px-6">
          <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full border border-primary-200/80 bg-primary-50 px-3.5 py-1 text-xs font-semibold text-primary-700 mb-3">
                <span className="h-1.5 w-1.5 rounded-full bg-primary-500" />
                Indian Food Composition Standard (IFCT / ICMR)
              </div>
              <h1 className="text-3xl font-extrabold tracking-tight text-text-primary sm:text-4xl">
                Ingredients &amp; Nutrition Catalog
              </h1>
              <p className="mt-2 text-base text-text-secondary max-w-2xl">
                Normalized per 100g or 100ml with market price benchmarks in Indian Rupees (₹) and precise macronutrient breakdowns.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Container */}
      <div className="mx-auto max-w-7xl px-6 py-8 flex-1 w-full space-y-6">
        {/* Search & Category Pills */}
        <div className="rounded-2xl border border-border-light bg-white p-5 shadow-sm space-y-4">
          <div className="relative">
            <svg
              className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              id="ingredient-search-input"
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search ingredient by name or food category (e.g. Paneer, Moong Dal, Oats, Atta)..."
              className="w-full rounded-xl border border-border-light bg-surface pl-10 pr-4 py-2.5 text-sm text-text-primary placeholder:text-text-muted focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20 transition-all"
            />
          </div>

          <div className="flex flex-wrap items-center gap-1.5 pt-1 border-t border-border-light/60">
            {CATEGORIES.map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`rounded-xl px-3 py-1.5 text-xs font-semibold transition-all ${
                  selectedCategory.toLowerCase() === cat.toLowerCase()
                    ? 'bg-primary-600 text-white shadow-sm'
                    : 'bg-cream text-text-secondary hover:bg-cream-dark hover:text-text-primary'
                }`}
              >
                {cat === 'all' ? 'All Categories' : cat}
              </button>
            ))}
          </div>
        </div>

        {/* Results Info */}
        <div className="flex items-center justify-between text-xs text-text-muted px-1">
          <span>
            Showing <strong className="text-text-primary">{filtered.length}</strong> items (all values per 100g / 100ml)
          </span>
          <span className="text-[11px] text-text-muted">Standard: INR (₹) / 100g &middot; kcal / 100g</span>
        </div>

        {/* Loading / Error States */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-20 text-text-muted">
            <div className="h-10 w-10 animate-spin rounded-full border-3 border-primary-600 border-t-transparent mb-3" />
            <p className="text-sm font-medium">Loading ingredient catalog...</p>
          </div>
        )}

        {error && (
          <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-center text-sm text-red-700">
            Error loading ingredients: {error}
          </div>
        )}

        {/* Ingredient Cards Grid */}
        {!loading && !error && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {filtered.map((item) => {
              const isHighProtein = (item.protein || 0) >= 15
              const isHighFiber = (item.fiber || 0) >= 8

              return (
                <div
                  key={item.id}
                  className="rounded-2xl border border-border-light bg-white p-5 shadow-sm transition-all duration-200 hover:border-primary-300 hover:shadow-md"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <span className="rounded-md bg-cream px-2 py-0.5 text-[10px] font-semibold text-text-muted uppercase tracking-wider border border-border-light/60">
                        {item.category}
                      </span>
                      <h3 className="mt-1.5 text-base font-bold text-text-primary">
                        {item.name}
                      </h3>
                    </div>
                    <div className="text-right shrink-0">
                      <span className="text-base font-extrabold text-primary-700">
                        ₹{item.price_per_unit ? item.price_per_unit.toFixed(2) : '0.00'}
                      </span>
                      <p className="text-[10px] text-text-muted">per {item.unit}</p>
                    </div>
                  </div>

                  {/* Highlights */}
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {isHighProtein && (
                      <span className="rounded-md bg-emerald-50 px-2 py-0.5 text-[10px] font-bold text-emerald-700 border border-emerald-200/60">
                        High Protein
                      </span>
                    )}
                    {isHighFiber && (
                      <span className="rounded-md bg-teal-50 px-2 py-0.5 text-[10px] font-bold text-teal-700 border border-teal-200/60">
                        High Fiber
                      </span>
                    )}
                  </div>

                  {/* Macros Strip */}
                  <div className="mt-4 grid grid-cols-5 gap-1.5 rounded-xl bg-cream/50 p-2.5 text-center border border-border-light/60">
                    <div>
                      <span className="text-[9px] font-bold text-text-muted uppercase">Energy</span>
                      <p className="text-xs font-extrabold text-text-primary">{item.calories || 0}</p>
                      <span className="text-[8px] text-text-muted">kcal</span>
                    </div>
                    <div>
                      <span className="text-[9px] font-bold text-emerald-700 uppercase">Protein</span>
                      <p className="text-xs font-extrabold text-emerald-800">{item.protein || 0}g</p>
                    </div>
                    <div>
                      <span className="text-[9px] font-bold text-sky-700 uppercase">Carbs</span>
                      <p className="text-xs font-extrabold text-sky-800">{item.carbohydrates || 0}g</p>
                    </div>
                    <div>
                      <span className="text-[9px] font-bold text-rose-700 uppercase">Fat</span>
                      <p className="text-xs font-extrabold text-rose-800">{item.fat || 0}g</p>
                    </div>
                    <div>
                      <span className="text-[9px] font-bold text-teal-700 uppercase">Fiber</span>
                      <p className="text-xs font-extrabold text-teal-800">{item.fiber || 0}g</p>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      <Footer />
    </div>
  )
}
