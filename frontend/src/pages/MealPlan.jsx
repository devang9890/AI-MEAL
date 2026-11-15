import { useState, useEffect, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth, SignedIn, SignedOut } from '@clerk/clerk-react'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'
import MealPlanGrid from '../components/MealPlanGrid'
import SwapMealModal from '../components/SwapMealModal'

export default function MealPlan() {
  const { isSignedIn, isLoaded, getToken } = useAuth()
  const navigate = useNavigate()

  const [households, setHouseholds] = useState([])
  const [selectedHouseholdId, setSelectedHouseholdId] = useState(null)
  const [currentPlan, setCurrentPlan] = useState(null)
  const [loadingHouseholds, setLoadingHouseholds] = useState(true)
  const [loadingPlan, setLoadingPlan] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState(null)
  const getTokenRef = useRef(getToken)
  const requestIdRef = useRef(0)

  // Clerk can refresh the getToken callback while React is rendering. Keeping
  // it in a ref prevents that refresh from restarting protected API requests.
  useEffect(() => {
    getTokenRef.current = getToken
  }, [getToken])

  const authorizedFetch = async (url, options = {}) => {
    const request = async (freshToken = false) => {
      const token = await getTokenRef.current(freshToken ? { skipCache: true } : undefined)
      if (!token) throw new Error('Your sign-in session is not ready. Please refresh the page or sign in again.')
      return fetch(url, {
        ...options,
        headers: { ...(options.headers || {}), Authorization: `Bearer ${token}` },
      })
    }

    let response = await request()
    // Clerk may retain an expired session JWT briefly after a page reload.
    // Retry once with a newly minted token before surfacing an auth failure.
    if (response.status === 401) response = await request(true)
    return response
  }

  // Swap modal state
  const [swapModalOpen, setSwapModalOpen] = useState(false)
  const [selectedSlotForSwap, setSelectedSlotForSwap] = useState(null)

  // Fetch households on mount
  useEffect(() => {
    if (!isLoaded || !isSignedIn) return

    const fetchHouseholds = async () => {
      setLoadingHouseholds(true)
      setError(null)
      try {
        const res = await authorizedFetch('http://localhost:8000/api/households')
        if (!res.ok) throw new Error('Failed to load households')
        const data = await res.json()
        setHouseholds(data)
        if (data.length > 0) {
          setSelectedHouseholdId(data[0].id)
        }
      } catch (err) {
        setError(err.message)
      } finally {
        setLoadingHouseholds(false)
      }
    }

    fetchHouseholds()
  }, [isLoaded, isSignedIn])

  // Fetch active meal plan when selected household changes
  useEffect(() => {
    if (!selectedHouseholdId || !isLoaded || !isSignedIn) return

    const fetchLatestPlan = async () => {
      const requestId = ++requestIdRef.current
      setLoadingPlan(true)
      setError(null)
      try {
        const res = await authorizedFetch(`http://localhost:8000/api/households/${selectedHouseholdId}/plans`)
        if (!res.ok) {
          if (res.status === 401) throw new Error('Your session expired. Please sign out and sign in again.')
          throw new Error('Failed to load meal plans')
        }
        const plans = await res.json()
        if (requestId !== requestIdRef.current) return
        if (plans.length > 0) {
          // Fetch full plan detail for the newest plan
          const latestId = plans[0].id
          const detailRes = await authorizedFetch(`http://localhost:8000/api/households/${selectedHouseholdId}/plans/${latestId}`)
          if (detailRes.ok) {
            const detailData = await detailRes.json()
            if (requestId === requestIdRef.current) setCurrentPlan(detailData)
          } else {
            if (detailRes.status === 401) throw new Error('Your session expired. Please sign out and sign in again.')
            if (requestId === requestIdRef.current) setCurrentPlan(plans[0])
          }
        } else {
          if (requestId === requestIdRef.current) setCurrentPlan(null)
        }
      } catch (err) {
        if (requestId === requestIdRef.current) {
          console.error(err)
          setCurrentPlan(null)
          setError(err.message)
        }
      } finally {
        if (requestId === requestIdRef.current) setLoadingPlan(false)
      }
    }

    fetchLatestPlan()
  }, [selectedHouseholdId, isLoaded, isSignedIn])

  const handleGeneratePlan = async () => {
    if (!selectedHouseholdId || generating) return
    setGenerating(true)
    setError(null)
    try {
      const res = await authorizedFetch(
        `http://localhost:8000/api/households/${selectedHouseholdId}/generate-plan`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      )

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData.detail || 'Failed to generate meal plan')
      }

      const newPlan = await res.json()
      setCurrentPlan(newPlan)
    } catch (err) {
      setError(err.message)
    } finally {
      setGenerating(false)
    }
  }

  const handleOpenSwap = (meal) => {
    setSelectedSlotForSwap(meal)
    setSwapModalOpen(true)
  }

  const handleSwapSuccess = (updatedMeal) => {
    if (!currentPlan) return
    // Update meals array
    const updatedMeals = currentPlan.meals.map((m) =>
      m.day === updatedMeal.day && m.meal_type === updatedMeal.meal_type ? updatedMeal : m
    )
    const newTotalCost = updatedMeals.reduce((acc, m) => acc + (m.cost || 0), 0)
    setCurrentPlan({
      ...currentPlan,
      meals: updatedMeals,
      total_cost: Math.round(newTotalCost),
    })
  }

  const activeHousehold = households.find((h) => h.id === selectedHouseholdId)

  return (
    <div className="min-h-screen bg-surface flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <SignedOut>
          <div className="rounded-3xl border border-border-light bg-white p-12 text-center shadow-sm max-w-xl mx-auto my-12">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-primary-100 text-primary-700 mb-6 text-2xl">
              🗓️
            </div>
            <h2 className="text-2xl font-bold text-text-primary mb-3">
              Sign In to View Your Meal Plans
            </h2>
            <p className="text-text-secondary text-sm mb-6">
              Create and manage weekly family meal plans with our AI Integer Linear Programming solver.
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
          {/* Header & Household Selector */}
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-8">
            <div>
              <h1 className="text-3xl font-bold tracking-tight text-text-primary">
                Weekly Meal Plan
              </h1>
              <p className="text-sm text-text-secondary mt-1">
                Cost-optimized, macro-balanced Indian meal schedules for your household.
              </p>
            </div>

            {/* Household Switcher & Action buttons */}
            <div className="flex items-center gap-3 flex-wrap">
              {households.length > 0 && (
                <select
                  value={selectedHouseholdId || ''}
                  onChange={(e) => setSelectedHouseholdId(Number(e.target.value))}
                  className="rounded-xl border border-border bg-white px-3 py-2 text-sm font-medium text-text-primary focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                >
                  {households.map((h) => (
                    <option key={h.id} value={h.id}>
                      {h.name} ({h.member_count ?? h.members?.length ?? 0} members)
                    </option>
                  ))}
                </select>
              )}

              {currentPlan && (
                <Link
                  to={`/grocery-list?householdId=${selectedHouseholdId}&planId=${currentPlan.id}`}
                  className="inline-flex items-center gap-2 rounded-xl border border-primary-200 bg-primary-50 px-4 py-2 text-sm font-semibold text-primary-700 hover:bg-primary-100 transition-colors shadow-xs"
                >
                  <span>Grocery List</span>
                </Link>
              )}

              <button
                onClick={handleGeneratePlan}
                disabled={generating || households.length === 0}
                className="inline-flex items-center gap-2 rounded-xl bg-primary-600 px-5 py-2 text-sm font-semibold text-white shadow-sm shadow-primary-600/20 hover:bg-primary-700 active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {generating ? (
                  <>
                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                    <span>Solving Plan...</span>
                  </>
                ) : (
                  <>
                    <span></span>
                    <span>{currentPlan ? 'Regenerate Plan' : 'Generate Plan'}</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Error Banner */}
          {error && (
            <div className="mb-6 rounded-2xl bg-red-50 border border-red-200 p-4 text-sm text-red-700 flex items-start gap-3">
              <span className="text-lg">⚠️</span>
              <div className="flex-1">
                <p className="font-semibold">Unable to complete request</p>
                <p className="mt-0.5">{error}</p>
                {error.includes('members') && (
                  <Link
                    to="/household"
                    className="inline-block mt-2 font-medium underline text-red-800"
                  >
                    Go to Household setup to add members →
                  </Link>
                )}
              </div>
            </div>
          )}

          {/* Loading Households */}
          {loadingHouseholds ? (
            <div className="flex flex-col items-center justify-center py-20 text-text-muted">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary-600 border-t-transparent mb-3" />
              <p className="text-sm">Loading your households...</p>
            </div>
          ) : households.length === 0 ? (
            <div className="rounded-3xl border border-dashed border-border p-12 text-center bg-white">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-cream text-3xl mb-4">
                🏡
              </div>
              <h3 className="text-xl font-bold text-text-primary mb-2">No Household Found</h3>
              <p className="text-sm text-text-secondary max-w-md mx-auto mb-6">
                Before generating meal plans, create your household profile with family members, dietary preferences, and target budget.
              </p>
              <Link
                to="/household"
                className="inline-flex items-center rounded-xl bg-primary-600 px-6 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-primary-700"
              >
                Set Up Household
              </Link>
            </div>
          ) : loadingPlan ? (
            <div className="flex flex-col items-center justify-center py-20 text-text-muted">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary-600 border-t-transparent mb-3" />
              <p className="text-sm">Retrieving weekly meal plan...</p>
            </div>
          ) : !currentPlan ? (
            /* Empty State: Household has no plan yet */
            <div className="rounded-3xl border border-border-light bg-white p-12 text-center shadow-xs">
              <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-3xl bg-primary-50 text-primary-600 text-4xl mb-5 shadow-inner">
                ✨
              </div>
              <h3 className="text-2xl font-bold text-text-primary mb-2">
                Generate a 7-Day Optimized Meal Plan
              </h3>
              <p className="text-sm text-text-secondary max-w-lg mx-auto mb-8 leading-relaxed">
                Antigravity's Integer Linear Programming solver will scan Indian recipes to find
                the exact schedule that satisfies your family's calorie targets, macro floors, and dietary preferences while minimizing weekly grocery costs.
              </p>

              {activeHousehold && (
                <div className="inline-flex items-center gap-6 bg-cream/70 border border-border-light px-6 py-3 rounded-2xl text-xs text-text-secondary mb-8">
                  <span>
                    👥 <strong>{activeHousehold.member_count ?? activeHousehold.members?.length ?? 0}</strong> Members
                  </span>
                  <span>
                    💰 Budget: <strong>₹{activeHousehold.weekly_budget || 'Flexible'}</strong>/week
                  </span>
                </div>
              )}

              <div>
                <button
                  onClick={handleGeneratePlan}
                  disabled={generating}
                  className="inline-flex items-center gap-2 rounded-xl bg-primary-600 px-8 py-3.5 text-base font-semibold text-white shadow-md shadow-primary-600/20 hover:bg-primary-700 hover:shadow-lg transition-all"
                >
                  {generating ? 'Optimizing with PuLP solver...' : '⚡ Generate 7-Day Plan'}
                </button>
              </div>
            </div>
          ) : (
            /* Active Meal Plan View */
            <div className="space-y-6">
              {/* Plan Summary Bar */}
              <div className="rounded-2xl border border-border-light bg-white p-5 shadow-xs grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Cost & Budget */}
                <div>
                  <span className="text-xs font-semibold text-text-muted uppercase tracking-wider">
                    Total Estimated Cost
                  </span>
                  <div className="flex items-baseline gap-2 mt-1">
                    <span className="text-2xl font-extrabold text-text-primary">
                      ₹{Math.round(currentPlan.total_cost || 0)}
                    </span>
                    {activeHousehold?.weekly_budget && (
                      <span className="text-xs text-text-secondary">
                        / ₹{activeHousehold.weekly_budget} budget
                      </span>
                    )}
                  </div>
                </div>

                {/* Budget Utilization */}
                {activeHousehold?.weekly_budget && (
                  <div>
                    <span className="text-xs font-semibold text-text-muted uppercase tracking-wider">
                      Budget Utilization
                    </span>
                    <div className="mt-2">
                      <div className="flex justify-between text-xs font-bold text-text-primary mb-1">
                        <span>
                          {Math.round(
                            ((currentPlan.total_cost || 0) / activeHousehold.weekly_budget) * 100
                          )}
                          %
                        </span>
                        <span>
                          {currentPlan.total_cost <= activeHousehold.weekly_budget
                            ? '✅ Within Budget'
                            : '⚠️ Over Budget'}
                        </span>
                      </div>
                      <div className="h-2 w-full bg-cream rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${
                            (currentPlan.total_cost || 0) <= activeHousehold.weekly_budget
                              ? 'bg-primary-600'
                              : 'bg-red-500'
                          }`}
                          style={{
                            width: `${Math.min(
                              100,
                              ((currentPlan.total_cost || 0) / activeHousehold.weekly_budget) * 100
                            )}%`,
                          }}
                        />
                      </div>
                    </div>
                  </div>
                )}

                {/* Plan Status */}
                <div>
                  <span className="text-xs font-semibold text-text-muted uppercase tracking-wider">
                    Plan Period
                  </span>
                  <p className="text-base font-bold text-text-primary mt-1">
                    Week of {currentPlan.week_start_date || 'Current Week'}
                  </p>
                  <span className={`inline-block mt-0.5 text-xs font-medium px-2 py-0.5 rounded-md ${currentPlan.status === 'needs_regeneration' ? 'text-amber-800 bg-amber-100' : 'text-emerald-700 bg-emerald-50'}`}>
                    {currentPlan.status === 'needs_regeneration' ? 'Update needed' : 'Active plan'}
                  </span>
                </div>

                {/* Total Meals */}
                <div>
                  <span className="text-xs font-semibold text-text-muted uppercase tracking-wider">
                    Meals Scheduled
                  </span>
                  <p className="text-2xl font-extrabold text-text-primary mt-1">
                    {currentPlan.meals?.length || 0} / 28
                  </p>
                </div>
              </div>

              {currentPlan.status === 'needs_regeneration' && (
                <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-950 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div><strong>Household details changed.</strong><p className="mt-0.5 text-xs text-amber-800">This saved plan is retained for reference, but it may no longer match current allergies, conditions, targets, preferences, or budget.</p></div>
                  <button onClick={handleGeneratePlan} disabled={generating} className="shrink-0 rounded-xl bg-amber-700 px-4 py-2 text-xs font-bold text-white hover:bg-amber-800 disabled:opacity-50">{generating ? 'Updating…' : 'Update plan'}</button>
                </div>
              )}

              {/* Relaxations Banner if any applied */}
              {currentPlan.relaxations_applied && currentPlan.relaxations_applied.length > 0 && (
                <div className="rounded-2xl bg-amber-50 border border-amber-200 p-4 text-xs text-amber-900 flex items-center gap-2">
                  <span>ℹ️</span>
                  <span>
                    <strong>Optimization Notice:</strong> To ensure a complete 7-day schedule with your dietary choices, the optimizer applied constraint adjustments: {currentPlan.relaxations_applied.join(', ')}.
                  </span>
                </div>
              )}

              {currentPlan.safety_notes && currentPlan.safety_notes.length > 0 && (
                <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-xs leading-relaxed text-rose-950">
                  <strong>Health-profile caution:</strong>
                  <ul className="mt-1 list-disc space-y-1 pl-4">{currentPlan.safety_notes.map((note) => <li key={note}>{note}</li>)}</ul>
                </div>
              )}

              {currentPlan.member_nutrition_dashboard?.length > 0 && (
                <section className="rounded-2xl border border-border-light bg-white p-5 shadow-xs">
                  <div className="mb-4">
                    <h3 className="font-bold text-text-primary">Individual nutrition progress</h3>
                    <p className="text-xs text-text-secondary mt-1">Planned intake is calculated from each member’s personalized Monday options. Gaps are shown rather than filled with unsafe foods.</p>
                  </div>
                  <div className="grid gap-3 lg:grid-cols-2">
                    {currentPlan.member_nutrition_dashboard.map((member) => (
                      <div key={member.member_id} className="rounded-xl border border-border-light bg-surface/40 p-3">
                        <div className="font-semibold text-sm text-text-primary mb-2">{member.member_name}</div>
                        <div className="grid grid-cols-5 gap-1 text-center text-[10px]">
                          {['calories', 'protein', 'carbs', 'fat', 'fiber'].map((nutrient) => {
                            const target = member.targets[nutrient] || 0
                            const planned = member.planned[nutrient] || 0
                            return <div key={nutrient}><div className="capitalize text-text-muted">{nutrient === 'calories' ? 'kcal' : nutrient}</div><div className="font-bold text-text-primary">{Math.round(planned)}/{Math.round(target)}</div><div className="h-1.5 bg-cream rounded-full mt-1 overflow-hidden"><div className="h-full bg-primary-600" style={{width: `${Math.min(100, target ? planned / target * 100 : 0)}%`}} /></div></div>
                          })}
                        </div>
                        {member.unresolved?.length > 0 && <p className="mt-2 text-[11px] text-rose-700">{member.unresolved.join(' · ')}</p>}
                      </div>
                    ))}
                  </div>
                </section>
              )}

              {/* 7-Day Grid */}
              <MealPlanGrid
                meals={currentPlan.meals || []}
                onSwapClick={handleOpenSwap}
              />
            </div>
          )}
        </SignedIn>
      </main>

      {/* Swap Modal */}
      {swapModalOpen && selectedSlotForSwap && (
        <SwapMealModal
          isOpen={swapModalOpen}
          onClose={() => setSwapModalOpen(false)}
          slot={selectedSlotForSwap}
          householdId={selectedHouseholdId}
          planId={currentPlan?.id}
          onSwapSuccess={handleSwapSuccess}
        />
      )}

      <Footer />
    </div>
  )
}
