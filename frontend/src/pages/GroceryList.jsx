import { useState, useEffect, useMemo } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { useAuth, SignedIn, SignedOut } from '@clerk/clerk-react'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'

export default function GroceryList() {
  const { isSignedIn, getToken } = useAuth()
  const [searchParams] = useSearchParams()

  const householdId = searchParams.get('householdId')
  const planId = searchParams.get('planId')

  const [groceryData, setGroceryData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [checkedItems, setCheckedItems] = useState({})
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    if (!householdId || !planId || !isSignedIn) {
      setLoading(false)
      return
    }

    const fetchGroceryList = async () => {
      setLoading(true)
      setError(null)
      try {
        const token = await getToken()
        const res = await fetch(
          `http://localhost:8000/api/households/${householdId}/plans/${planId}/grocery-list`,
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        )
        if (!res.ok) throw new Error('Failed to load grocery list')
        const data = await res.json()
        setGroceryData(data)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchGroceryList()
  }, [householdId, planId, isSignedIn, getToken])

  // Group items by category
  const categorizedItems = useMemo(() => {
    if (!groceryData?.items) return {}
    const groups = {}
    groceryData.items.forEach((item) => {
      const cat = item.category || 'Other Groceries'
      if (!groups[cat]) groups[cat] = []
      groups[cat].push(item)
    })
    return groups
  }, [groceryData])

  const toggleItem = (ingredientId) => {
    setCheckedItems((prev) => ({
      ...prev,
      [ingredientId]: !prev[ingredientId],
    }))
  }

  const handleCopyToClipboard = () => {
    if (!groceryData?.items) return
    const text = Object.entries(categorizedItems)
      .map(([cat, items]) => {
        const itemLines = items
          .map((i) => `  - ${i.name}: ${i.display_quantity} (approx ₹${Math.round(i.estimated_cost)})`)
          .join('\n')
        return `[${cat}]\n${itemLines}`
      })
      .join('\n\n')

    const header = `Weekly Grocery Shopping List\nTotal Estimated Cost: ₹${Math.round(
      groceryData.total_cost
    )}\nItems: ${groceryData.item_count}\n\n`

    navigator.clipboard.writeText(header + text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const completedCount = Object.values(checkedItems).filter(Boolean).length
  const totalCount = groceryData?.items?.length || 0

  return (
    <div className="min-h-screen bg-surface flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <SignedOut>
          <div className="rounded-3xl border border-border-light bg-white p-12 text-center shadow-sm max-w-xl mx-auto my-12">
            <h2 className="text-2xl font-bold text-text-primary mb-3">Sign In Required</h2>
            <p className="text-text-secondary text-sm mb-6">
              Please sign in to view your household grocery list.
            </p>
            <Link
              to="/login"
              className="inline-flex items-center rounded-xl bg-primary-600 px-6 py-3 text-sm font-semibold text-white shadow-sm hover:bg-primary-700"
            >
              Sign In
            </Link>
          </div>
        </SignedOut>

        <SignedIn>
          {/* Top Breadcrumbs */}
          <div className="mb-6 flex items-center justify-between">
            <Link
              to="/meal-plan"
              className="inline-flex items-center gap-2 text-sm font-semibold text-primary-600 hover:text-primary-800 transition-colors"
            >
              ← Back to Meal Plan
            </Link>
            <div className="flex items-center gap-2">
              <button
                onClick={handleCopyToClipboard}
                className="inline-flex items-center gap-1.5 rounded-xl border border-border bg-white px-3.5 py-1.5 text-xs font-semibold text-text-secondary hover:bg-cream transition-colors shadow-2xs"
              >
                {copied ? '✅ Copied!' : '📋 Copy List'}
              </button>
              <button
                onClick={() => window.print()}
                className="inline-flex items-center gap-1.5 rounded-xl border border-border bg-white px-3.5 py-1.5 text-xs font-semibold text-text-secondary hover:bg-cream transition-colors shadow-2xs"
              >
                🖨️ Print
              </button>
            </div>
          </div>

          {!householdId || !planId ? (
            <div className="rounded-3xl border border-border-light bg-white p-12 text-center">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-amber-50 text-2xl mb-4">
                🛒
              </div>
              <h3 className="text-xl font-bold text-text-primary mb-2">No Meal Plan Specified</h3>
              <p className="text-sm text-text-secondary mb-6">
                Please generate or open a meal plan to view its consolidated weekly grocery list.
              </p>
              <Link
                to="/meal-plan"
                className="inline-flex items-center rounded-xl bg-primary-600 px-6 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-primary-700"
              >
                Go to Meal Plan
              </Link>
            </div>
          ) : loading ? (
            <div className="flex flex-col items-center justify-center py-20 text-text-muted">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary-600 border-t-transparent mb-3" />
              <p className="text-sm">Consolidating weekly grocery ingredients...</p>
            </div>
          ) : error ? (
            <div className="rounded-2xl bg-red-50 border border-red-200 p-6 text-center text-red-700">
              <p className="font-semibold">Unable to load grocery list</p>
              <p className="text-sm mt-1">{error}</p>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Summary Hero Card */}
              <div className="rounded-3xl border border-border-light bg-white p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div>
                  <span className="inline-flex items-center rounded-md bg-primary-100 px-2.5 py-1 text-xs font-bold text-primary-800 uppercase tracking-wider mb-2">
                    7-Day Consolidated
                  </span>
                  <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-text-primary">
                    Weekly Grocery List
                  </h1>
                  <p className="text-sm text-text-secondary mt-1">
                    Ingredients aggregated across all 21 scheduled household meals.
                  </p>
                </div>

                <div className="flex items-center gap-6 divide-x divide-border-light">
                  <div className="text-center sm:text-right pr-2">
                    <span className="text-xs text-text-muted font-medium">Estimated Total</span>
                    <p className="text-2xl font-extrabold text-text-primary">
                      ₹{Math.round(groceryData.total_cost || 0)}
                    </p>
                  </div>
                  <div className="text-center sm:text-right pl-6">
                    <span className="text-xs text-text-muted font-medium">Items to Buy</span>
                    <p className="text-2xl font-extrabold text-primary-700">
                      {completedCount} / {totalCount}
                    </p>
                  </div>
                </div>
              </div>

              {/* Progress bar */}
              {totalCount > 0 && (
                <div className="w-full bg-white rounded-2xl p-4 border border-border-light shadow-2xs">
                  <div className="flex justify-between text-xs font-semibold text-text-secondary mb-1.5">
                    <span>Shopping Progress</span>
                    <span>{Math.round((completedCount / totalCount) * 100)}% Completed</span>
                  </div>
                  <div className="h-2.5 w-full bg-cream rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary-600 transition-all duration-300 rounded-full"
                      style={{ width: `${(completedCount / totalCount) * 100}%` }}
                    />
                  </div>
                </div>
              )}

              {/* Categorized List */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {Object.entries(categorizedItems).map(([category, items]) => (
                  <div
                    key={category}
                    className="rounded-2xl border border-border-light bg-white p-5 shadow-2xs flex flex-col"
                  >
                    <div className="flex items-center justify-between border-b border-border-light/70 pb-3 mb-3">
                      <h3 className="text-base font-bold text-text-primary capitalize flex items-center gap-2">
                        <span>📦</span>
                        <span>{category}</span>
                      </h3>
                      <span className="text-xs font-medium text-text-muted bg-cream px-2 py-0.5 rounded-full">
                        {items.length} items
                      </span>
                    </div>

                    <div className="space-y-2 flex-1">
                      {items.map((item) => {
                        const isChecked = Boolean(checkedItems[item.ingredient_id])
                        return (
                          <label
                            key={item.ingredient_id}
                            className={`flex items-center justify-between p-2.5 rounded-xl border cursor-pointer transition-all ${
                              isChecked
                                ? 'bg-cream/50 border-border-light/50 line-through text-text-muted opacity-60'
                                : 'bg-surface hover:bg-cream/40 border-border-light'
                            }`}
                          >
                            <div className="flex items-center gap-3 min-w-0 pr-2">
                              <input
                                type="checkbox"
                                checked={isChecked}
                                onChange={() => toggleItem(item.ingredient_id)}
                                className="h-4 w-4 rounded border-border text-primary-600 focus:ring-primary-500"
                              />
                              <span
                                className={`text-sm font-medium truncate ${
                                  isChecked ? 'text-text-muted' : 'text-text-primary'
                                }`}
                              >
                                {item.name}
                              </span>
                            </div>

                            <div className="text-right shrink-0 flex items-center gap-3">
                              <span className="text-xs font-semibold text-text-secondary bg-white px-2 py-1 rounded-md border border-border-light/60">
                                {item.display_quantity}
                              </span>
                              <span className="text-xs font-bold text-text-primary w-12 text-right">
                                ₹{Math.round(item.estimated_cost)}
                              </span>
                            </div>
                          </label>
                        )
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </SignedIn>
      </main>

      <Footer />
    </div>
  )
}
