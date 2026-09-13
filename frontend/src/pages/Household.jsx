import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { useAuth, useUser, SignedIn, SignedOut } from '@clerk/clerk-react'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'
import HouseholdModal from '../components/HouseholdModal'
import MemberModal from '../components/MemberModal'
import MetabolicModal from '../components/MetabolicModal'

const API_BASE = 'http://localhost:8000/api'

export default function Household() {
  const { isSignedIn, getToken } = useAuth()
  const { user } = useUser()

  // Data state
  const [households, setHouseholds] = useState([])
  const [activeHousehold, setActiveHousehold] = useState(null)
  const [members, setMembers] = useState([])
  const [nutritionTargets, setNutritionTargets] = useState({}) // { [member_id]: targetObj }

  // UI state
  const [loading, setLoading] = useState(true)
  const [calculatingMemberId, setCalculatingMemberId] = useState(null)
  const [error, setError] = useState(null)
  const [successMessage, setSuccessMessage] = useState(null)

  // Modal states
  const [isHouseholdModalOpen, setIsHouseholdModalOpen] = useState(false)
  const [editingHousehold, setEditingHousehold] = useState(null)
  const [isMemberModalOpen, setIsMemberModalOpen] = useState(false)
  const [editingMember, setEditingMember] = useState(null)
  const [isMetabolicModalOpen, setIsMetabolicModalOpen] = useState(false)
  const [metabolicModalData, setMetabolicModalData] = useState({ member: null, target: null })

  const showToast = (msg) => {
    setSuccessMessage(msg)
    setTimeout(() => setSuccessMessage(null), 4000)
  }

  // Fetch user households
  const fetchHouseholds = useCallback(async () => {
    if (!isSignedIn) return
    try {
      setLoading(true)
      const token = await getToken()
      const res = await fetch(`${API_BASE}/households`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      if (!res.ok) throw new Error('Failed to load households')
      const data = await res.json()
      setHouseholds(data)
      if (data.length > 0) {
        // Keep active household or set to first
        setActiveHousehold((prev) => (prev ? data.find((h) => h.id === prev.id) || data[0] : data[0]))
      } else {
        setActiveHousehold(null)
        setMembers([])
      }
    } catch (err) {
      console.error(err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [isSignedIn, getToken])

  // Fetch members for active household
  const fetchMembers = useCallback(async () => {
    if (!activeHousehold) return
    try {
      const token = await getToken()
      const res = await fetch(`${API_BASE}/households/${activeHousehold.id}/members`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      if (!res.ok) throw new Error('Failed to load members')
      const membersData = await res.json()
      setMembers(membersData)

      // Fetch nutrition targets for members who have one
      const targetsMap = {}
      for (const m of membersData) {
        if (m.has_nutrition_target) {
          try {
            const nRes = await fetch(`${API_BASE}/members/${m.id}/nutrition`, {
              headers: { Authorization: `Bearer ${token}` }
            })
            if (nRes.ok) {
              const nData = await nRes.json()
              targetsMap[m.id] = nData
            }
          } catch (e) {
            console.error(`Failed to fetch target for member ${m.id}:`, e)
          }
        }
      }
      setNutritionTargets(targetsMap)
    } catch (err) {
      console.error(err)
      setError(err.message)
    }
  }, [activeHousehold, getToken])

  useEffect(() => {
    if (isSignedIn) {
      fetchHouseholds()
    }
  }, [isSignedIn, fetchHouseholds])

  useEffect(() => {
    if (activeHousehold) {
      fetchMembers()
    }
  }, [activeHousehold, fetchMembers])

  // Save Household (Create / Update)
  const handleSaveHousehold = async (payload) => {
    try {
      const token = await getToken()
      let res
      if (editingHousehold) {
        res = await fetch(`${API_BASE}/households/${editingHousehold.id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify(payload)
        })
      } else {
        res = await fetch(`${API_BASE}/households`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify(payload)
        })
      }

      if (!res.ok) {
        const errData = await res.json()
        throw new Error(errData.detail || 'Failed to save household')
      }

      setIsHouseholdModalOpen(false)
      setEditingHousehold(null)
      showToast(editingHousehold ? 'Household updated successfully!' : 'Household created successfully!')
      fetchHouseholds()
    } catch (err) {
      alert(err.message)
    }
  }

  // Save Member (Create / Update)
  const handleSaveMember = async (payload) => {
    if (!activeHousehold) return
    try {
      const token = await getToken()
      let res
      if (editingMember) {
        res = await fetch(`${API_BASE}/households/${activeHousehold.id}/members/${editingMember.id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify(payload)
        })
      } else {
        res = await fetch(`${API_BASE}/households/${activeHousehold.id}/members`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify(payload)
        })
      }

      if (!res.ok) {
        const errData = await res.json()
        throw new Error(errData.detail || 'Failed to save member')
      }

      setIsMemberModalOpen(false)
      setEditingMember(null)
      showToast(editingMember ? 'Member updated successfully!' : 'Member added to household!')
      fetchMembers()
    } catch (err) {
      alert(err.message)
    }
  }

  // Delete Member
  const handleDeleteMember = async (memberId) => {
    if (!window.confirm('Are you sure you want to remove this family member? This will also remove their nutrition targets.')) {
      return
    }
    try {
      const token = await getToken()
      const res = await fetch(`${API_BASE}/households/${activeHousehold.id}/members/${memberId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      })
      if (!res.ok) throw new Error('Failed to delete member')
      showToast('Family member removed')
      fetchMembers()
    } catch (err) {
      alert(err.message)
    }
  }

  // Calculate Nutrition Target
  const handleCalculateNutrition = async (member) => {
    try {
      setCalculatingMemberId(member.id)
      const token = await getToken()
      const res = await fetch(`${API_BASE}/members/${member.id}/nutrition/calculate`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      })
      if (!res.ok) {
        const errData = await res.json()
        throw new Error(errData.detail || 'Failed to calculate nutrition target')
      }
      const result = await res.json()

      // Update state
      setNutritionTargets((prev) => ({
        ...prev,
        [member.id]: {
          id: member.id,
          member_id: member.id,
          daily_calories: result.daily_calories,
          daily_protein_g: result.daily_protein_g,
          daily_carbs_g: result.daily_carbs_g,
          daily_fat_g: result.daily_fat_g,
          daily_fiber_g: result.daily_fiber_g,
        }
      }))
      showToast(`Nutrition target computed for ${member.name}: ${result.daily_calories} kcal/day!`)
      fetchMembers()
    } catch (err) {
      alert(err.message)
    } finally {
      setCalculatingMemberId(null)
    }
  }

  // Open Metabolic Modal
  const openMetabolicBreakdown = (member) => {
    const target = nutritionTargets[member.id]
    if (!target) return
    setMetabolicModalData({ member, target })
    setIsMetabolicModalOpen(true)
  }

  // Aggregate stats
  const totalCalories = Object.values(nutritionTargets).reduce((acc, t) => acc + (t.daily_calories || 0), 0)
  const totalProtein = Object.values(nutritionTargets).reduce((acc, t) => acc + (t.daily_protein_g || 0), 0)
  const totalCarbs = Object.values(nutritionTargets).reduce((acc, t) => acc + (t.daily_carbs_g || 0), 0)
  const totalFat = Object.values(nutritionTargets).reduce((acc, t) => acc + (t.daily_fat_g || 0), 0)
  const totalFiber = Object.values(nutritionTargets).reduce((acc, t) => acc + (t.daily_fiber_g || 0), 0)

  const weeklyBudget = activeHousehold?.weekly_budget || 0
  const dailyPerPersonBudget = (weeklyBudget && members.length > 0)
    ? (weeklyBudget / 7 / members.length).toFixed(1)
    : null

  return (
    <div className="flex min-h-screen flex-col bg-surface text-text-primary">
      <Navbar />

      <main className="flex-1 pb-16 pt-8">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">

          {/* Signed Out View */}
          <SignedOut>
            <div className="mx-auto max-w-3xl rounded-3xl border border-border-light bg-white p-8 sm:p-12 text-center shadow-xl">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-primary-100 text-primary-700 shadow-inner mb-6">
                <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
              </div>
              <h1 className="text-3xl font-black tracking-tight text-text-primary sm:text-4xl">
                Household & Family Nutrition
              </h1>
              <p className="mt-4 text-base text-text-secondary max-w-xl mx-auto">
                Organize your family members, track specific biometric and dietary requirements, and compute clinical-grade Mifflin–St Jeor daily caloric and macronutrient targets.
              </p>

              <div className="mt-8 flex items-center justify-center gap-4">
                <Link
                  to="/login"
                  className="rounded-xl border border-border-light bg-white px-6 py-3 text-sm font-semibold text-text-secondary hover:bg-cream transition-colors shadow-sm"
                >
                  Log In
                </Link>
                <Link
                  to="/register"
                  className="rounded-xl bg-primary-600 px-7 py-3 text-sm font-semibold text-white shadow-lg shadow-primary-600/25 hover:bg-primary-700 transition-all hover:scale-[1.02]"
                >
                  Create Free Account
                </Link>
              </div>

              {/* Feature preview list */}
              <div className="mt-12 grid grid-cols-1 sm:grid-cols-3 gap-6 pt-10 border-t border-border-light text-left">
                <div className="p-4 rounded-2xl bg-cream/50 border border-border-light">
                  <div className="text-2xl mb-2">👨‍👩‍👧‍👦</div>
                  <h4 className="font-bold text-sm text-text-primary">Multi-Member Profiles</h4>
                  <p className="text-xs text-text-muted mt-1">Individual age, sex, weight, height, activity level, and dietary preferences.</p>
                </div>
                <div className="p-4 rounded-2xl bg-cream/50 border border-border-light">
                  <div className="text-2xl mb-2">⚡</div>
                  <h4 className="font-bold text-sm text-text-primary">Mifflin–St Jeor BMR</h4>
                  <p className="text-xs text-text-muted mt-1">Validated scientific formula with accurate activity multipliers (1.2x to 1.9x).</p>
                </div>
                <div className="p-4 rounded-2xl bg-cream/50 border border-border-light">
                  <div className="text-2xl mb-2">🥗</div>
                  <h4 className="font-bold text-sm text-text-primary">Custom Macro Splits</h4>
                  <p className="text-xs text-text-muted mt-1">20% Protein, 50% Carbs, 30% Fat, and 14g Fiber per 1,000 kcal.</p>
                </div>
              </div>
            </div>
          </SignedOut>

          {/* Signed In View */}
          <SignedIn>
            {/* Success Toast */}
            {successMessage && (
              <div className="mb-6 flex items-center justify-between rounded-2xl bg-emerald-50 border border-emerald-200 p-4 text-sm font-semibold text-emerald-800 shadow-sm animate-fade-in">
                <div className="flex items-center gap-2">
                  <span>✅</span>
                  <span>{successMessage}</span>
                </div>
                <button onClick={() => setSuccessMessage(null)} className="text-emerald-700 hover:text-emerald-900">
                  ✕
                </button>
              </div>
            )}

            {/* Page Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-border-light">
              <div>
                <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-primary-700">
                  <span>Household Management</span>
                  <span>•</span>
                  <span>Nutrition Engine</span>
                </div>
                <h1 className="text-3xl font-black tracking-tight text-text-primary mt-1">
                  Family & Nutrition Hub
                </h1>
                <p className="text-sm text-text-secondary mt-1">
                  Welcome back, <span className="font-semibold text-text-primary">{user?.firstName || user?.fullName || 'User'}</span>. Manage your family members and daily metabolic targets.
                </p>
              </div>

              <div className="flex items-center gap-3">
                {activeHousehold && (
                  <button
                    onClick={() => {
                      setEditingMember(null)
                      setIsMemberModalOpen(true)
                    }}
                    className="inline-flex items-center gap-2 rounded-xl bg-primary-600 px-4 py-2.5 text-sm font-semibold text-white shadow-md shadow-primary-600/20 hover:bg-primary-700 transition-all hover:scale-[1.02]"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
                    </svg>
                    <span>Add Member</span>
                  </button>
                )}
                <button
                  onClick={() => {
                    setEditingHousehold(activeHousehold || null)
                    setIsHouseholdModalOpen(true)
                  }}
                  className="rounded-xl border border-border-light bg-white px-4 py-2.5 text-sm font-medium text-text-secondary hover:bg-cream transition-colors"
                >
                  {activeHousehold ? 'Edit Household' : 'Create Household'}
                </button>
              </div>
            </div>

            {loading ? (
              <div className="py-20 text-center">
                <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
                <p className="mt-4 text-sm font-medium text-text-muted">Loading household data...</p>
              </div>
            ) : households.length === 0 ? (
              /* No Household Onboarding */
              <div className="mt-12 mx-auto max-w-lg rounded-3xl border border-dashed border-border-light bg-white p-10 text-center shadow-lg">
                <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-cream-dark text-text-secondary mb-4">
                  🏠
                </div>
                <h3 className="text-xl font-bold text-text-primary">No Household Found</h3>
                <p className="mt-2 text-sm text-text-secondary">
                  Create your first household space to add family members, set a weekly grocery budget, and compute nutrition targets.
                </p>
                <button
                  onClick={() => {
                    setEditingHousehold(null)
                    setIsHouseholdModalOpen(true)
                  }}
                  className="mt-6 rounded-xl bg-primary-600 px-6 py-3 text-sm font-semibold text-white shadow-md shadow-primary-600/20 hover:bg-primary-700 transition-all"
                >
                  + Create Your Household
                </button>
              </div>
            ) : (
              /* Active Household Overview & Members */
              <div className="mt-8 space-y-8">
                {/* Household Switcher / Meta bar */}
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
                  {/* Household Profile Card */}
                  <div className="rounded-3xl border border-border-light bg-white p-6 shadow-sm">
                    <div className="text-xs font-bold uppercase tracking-wider text-text-muted">Household</div>
                    <div className="mt-1 text-2xl font-black text-text-primary">{activeHousehold.name}</div>
                    <div className="mt-4 flex flex-wrap items-center gap-2">
                      <span className="inline-flex items-center rounded-lg bg-primary-50 px-2.5 py-1 text-xs font-semibold text-primary-700">
                        👥 {members.length} {members.length === 1 ? 'Member' : 'Members'}
                      </span>
                      {weeklyBudget ? (
                        <span className="inline-flex items-center rounded-lg bg-amber-50 px-2.5 py-1 text-xs font-semibold text-amber-800">
                          💰 ₹{weeklyBudget.toLocaleString()} / wk
                        </span>
                      ) : (
                        <span className="text-xs text-text-muted">No budget set</span>
                      )}
                    </div>
                    {dailyPerPersonBudget && (
                      <p className="mt-3 text-xs text-text-muted">
                        ~₹{dailyPerPersonBudget} / person / day
                      </p>
                    )}
                  </div>

                  {/* Aggregate Nutrition Summary Cards */}
                  <div className="lg:col-span-3 rounded-3xl border border-border-light bg-white p-6 shadow-sm flex flex-col justify-between">
                    <div>
                      <div className="flex items-center justify-between">
                        <div className="text-xs font-bold uppercase tracking-wider text-text-muted">
                          Household Daily Nutritional Demand
                        </div>
                        <div className="text-xs font-medium text-text-muted">
                          {Object.keys(nutritionTargets).length} of {members.length} calculated
                        </div>
                      </div>
                      <div className="mt-2 text-3xl font-black text-primary-700">
                        {totalCalories.toLocaleString(undefined, { maximumFractionDigits: 0 })} <span className="text-lg font-bold text-text-muted">kcal / day</span>
                      </div>
                    </div>

                    <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-3 pt-4 border-t border-border-light">
                      <div className="rounded-xl bg-emerald-50/80 p-2.5 text-center">
                        <div className="text-[10px] font-bold uppercase text-emerald-700">Protein</div>
                        <div className="text-base font-black text-emerald-900 mt-0.5">{totalProtein.toFixed(1)}g</div>
                      </div>
                      <div className="rounded-xl bg-amber-50/80 p-2.5 text-center">
                        <div className="text-[10px] font-bold uppercase text-amber-700">Carbohydrates</div>
                        <div className="text-base font-black text-amber-900 mt-0.5">{totalCarbs.toFixed(1)}g</div>
                      </div>
                      <div className="rounded-xl bg-rose-50/80 p-2.5 text-center">
                        <div className="text-[10px] font-bold uppercase text-rose-700">Dietary Fat</div>
                        <div className="text-base font-black text-rose-900 mt-0.5">{totalFat.toFixed(1)}g</div>
                      </div>
                      <div className="rounded-xl bg-teal-50/80 p-2.5 text-center">
                        <div className="text-[10px] font-bold uppercase text-teal-700">Dietary Fiber</div>
                        <div className="text-base font-black text-teal-900 mt-0.5">{totalFiber.toFixed(1)}g</div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Family Members Section */}
                <div>
                  <div className="flex items-center justify-between mb-6">
                    <div>
                      <h2 className="text-xl font-bold text-text-primary">Family Members ({members.length})</h2>
                      <p className="text-xs text-text-muted mt-0.5">Biometric profiles and individual nutritional equations</p>
                    </div>
                    <button
                      onClick={() => {
                        setEditingMember(null)
                        setIsMemberModalOpen(true)
                      }}
                      className="inline-flex items-center gap-1.5 rounded-xl border border-border-light bg-white px-3.5 py-2 text-xs font-semibold text-text-secondary hover:bg-cream transition-colors"
                    >
                      + Add Member
                    </button>
                  </div>

                  {members.length === 0 ? (
                    <div className="rounded-3xl border border-dashed border-border-light bg-white p-8 text-center">
                      <p className="text-sm text-text-secondary">No family members in this household yet.</p>
                      <button
                        onClick={() => {
                          setEditingMember(null)
                          setIsMemberModalOpen(true)
                        }}
                        className="mt-4 rounded-xl bg-primary-600 px-5 py-2 text-xs font-semibold text-white shadow hover:bg-primary-700 transition-all"
                      >
                        Add Your First Family Member
                      </button>
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                      {members.map((member) => {
                        const target = nutritionTargets[member.id]
                        const isCalculating = calculatingMemberId === member.id

                        return (
                          <div
                            key={member.id}
                            className="group relative flex flex-col justify-between rounded-3xl border border-border-light bg-white p-6 shadow-sm transition-all hover:shadow-md hover:border-primary-200"
                          >
                            <div>
                              {/* Member Header */}
                              <div className="flex items-start justify-between">
                                <div className="flex items-center gap-3">
                                  <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-cream-dark text-xl font-bold text-text-primary shadow-inner">
                                    {member.gender === 'male' ? '👨' : '👩'}
                                  </div>
                                  <div>
                                    <h3 className="text-lg font-bold text-text-primary leading-snug">
                                      {member.name}
                                    </h3>
                                    <span className="text-xs text-text-muted">
                                      {member.age} yrs • {member.gender === 'male' ? 'Male' : 'Female'}
                                    </span>
                                  </div>
                                </div>

                                {/* Edit / Delete Menu */}
                                <div className="flex items-center gap-1">
                                  <button
                                    onClick={() => {
                                      setEditingMember(member)
                                      setIsMemberModalOpen(true)
                                    }}
                                    className="rounded-lg p-1.5 text-text-muted hover:bg-cream hover:text-text-primary transition-colors"
                                    title="Edit Member"
                                  >
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                                    </svg>
                                  </button>
                                  <button
                                    onClick={() => handleDeleteMember(member.id)}
                                    className="rounded-lg p-1.5 text-text-muted hover:bg-rose-50 hover:text-rose-600 transition-colors"
                                    title="Remove Member"
                                  >
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                    </svg>
                                  </button>
                                </div>
                              </div>

                              {/* Biometrics badge row */}
                              <div className="mt-4 grid grid-cols-3 gap-2 rounded-2xl bg-cream/50 p-3 text-center border border-border-light/60">
                                <div>
                                  <div className="text-[10px] uppercase font-bold text-text-muted">Height</div>
                                  <div className="text-xs font-bold text-text-primary mt-0.5">{member.height_cm} cm</div>
                                </div>
                                <div>
                                  <div className="text-[10px] uppercase font-bold text-text-muted">Weight</div>
                                  <div className="text-xs font-bold text-text-primary mt-0.5">{member.weight_kg} kg</div>
                                </div>
                                <div>
                                  <div className="text-[10px] uppercase font-bold text-text-muted">Activity</div>
                                  <div className="text-xs font-bold text-text-primary mt-0.5 capitalize">{member.activity_level.replace('_', ' ')}</div>
                                </div>
                              </div>

                              {/* Dietary Preference & Allergies */}
                              <div className="mt-3 flex flex-wrap items-center gap-1.5">
                                <span className="inline-flex items-center rounded-lg bg-primary-50 px-2 py-0.5 text-[11px] font-bold text-primary-700 capitalize">
                                  🥗 {member.dietary_preference.replace('_', ' ')}
                                </span>
                                {member.allergies && member.allergies.map((allergy, idx) => (
                                  <span key={idx} className="inline-flex items-center rounded-lg bg-rose-50 px-2 py-0.5 text-[11px] font-medium text-rose-700">
                                    🚫 {allergy}
                                  </span>
                                ))}
                                {member.dietary_restrictions && member.dietary_restrictions.map((res, idx) => (
                                  <span key={idx} className="inline-flex items-center rounded-lg bg-amber-50 px-2 py-0.5 text-[11px] font-medium text-amber-700">
                                    ⚠️ {res}
                                  </span>
                                ))}
                              </div>

                              {/* Nutrition Target Section */}
                              <div className="mt-5 pt-4 border-t border-border-light">
                                {target ? (
                                  <div>
                                    <div className="flex items-baseline justify-between mb-2">
                                      <span className="text-xs font-bold uppercase tracking-wider text-text-muted">Daily Calorie Target</span>
                                      <span className="text-xl font-black text-primary-700">{target.daily_calories} <span className="text-xs font-semibold text-text-muted">kcal</span></span>
                                    </div>

                                    {/* Macro mini bars */}
                                    <div className="grid grid-cols-3 gap-2 mt-2">
                                      <div className="rounded-xl border border-emerald-100 bg-emerald-50/60 p-2 text-center">
                                        <div className="text-[10px] font-bold text-emerald-700">Protein</div>
                                        <div className="text-sm font-black text-emerald-900 mt-0.5">{target.daily_protein_g}g</div>
                                        <div className="text-[9px] text-emerald-600">20%</div>
                                      </div>
                                      <div className="rounded-xl border border-amber-100 bg-amber-50/60 p-2 text-center">
                                        <div className="text-[10px] font-bold text-amber-700">Carbs</div>
                                        <div className="text-sm font-black text-amber-900 mt-0.5">{target.daily_carbs_g}g</div>
                                        <div className="text-[9px] text-amber-600">50%</div>
                                      </div>
                                      <div className="rounded-xl border border-rose-100 bg-rose-50/60 p-2 text-center">
                                        <div className="text-[10px] font-bold text-rose-700">Fat</div>
                                        <div className="text-sm font-black text-rose-900 mt-0.5">{target.daily_fat_g}g</div>
                                        <div className="text-[9px] text-rose-600">30%</div>
                                      </div>
                                    </div>

                                    {/* Fiber note */}
                                    <div className="mt-2 text-center text-[11px] font-medium text-teal-700 bg-teal-50/70 rounded-lg py-1">
                                      🌾 Fiber Target: <span className="font-bold">{target.daily_fiber_g}g</span> / day
                                    </div>
                                  </div>
                                ) : (
                                  <div className="rounded-2xl bg-cream/50 p-4 text-center border border-border-light/60">
                                    <p className="text-xs text-text-muted">Nutrition targets not yet calculated.</p>
                                    <p className="text-[11px] text-text-secondary mt-0.5">Click below to compute personalized BMR & macros.</p>
                                  </div>
                                )}
                              </div>
                            </div>

                            {/* Card Footer Actions */}
                            <div className="mt-5 pt-3 border-t border-border-light flex items-center justify-between gap-2">
                              {target ? (
                                <>
                                  <button
                                    onClick={() => openMetabolicBreakdown(member)}
                                    className="inline-flex items-center gap-1 text-xs font-semibold text-primary-700 hover:text-primary-800 transition-colors"
                                  >
                                    <span>🔬 Formula Details</span>
                                  </button>
                                  <button
                                    onClick={() => handleCalculateNutrition(member)}
                                    disabled={isCalculating}
                                    className="rounded-xl border border-border-light bg-white px-3 py-1.5 text-xs font-semibold text-text-secondary hover:bg-cream transition-colors disabled:opacity-50"
                                  >
                                    {isCalculating ? 'Computing...' : 'Recalculate'}
                                  </button>
                                </>
                              ) : (
                                <button
                                  onClick={() => handleCalculateNutrition(member)}
                                  disabled={isCalculating}
                                  className="w-full inline-flex items-center justify-center gap-2 rounded-xl bg-primary-600 px-4 py-2.5 text-xs font-bold text-white shadow-sm hover:bg-primary-700 transition-all disabled:opacity-50"
                                >
                                  {isCalculating ? (
                                    <span>Calculating BMR & Macros...</span>
                                  ) : (
                                    <>
                                      <span>⚡ Calculate Nutrition Target</span>
                                    </>
                                  )}
                                </button>
                              )}
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  )}
                </div>

                {/* Educational Disclaimer footer */}
                <div className="rounded-2xl border border-border-light bg-cream/30 p-4 text-center text-xs text-text-muted">
                  <span className="font-bold text-text-secondary">Disclaimer: </span>
                  Nutritional targets are modeled using the Mifflin–St Jeor resting metabolic equation for algorithmic meal planning purposes and are not intended as clinical or medical dietary advice.
                </div>
              </div>
            )}
          </SignedIn>

        </div>
      </main>

      <Footer />

      {/* Modals */}
      <HouseholdModal
        isOpen={isHouseholdModalOpen}
        onClose={() => setIsHouseholdModalOpen(false)}
        onSave={handleSaveHousehold}
        initialData={editingHousehold}
      />

      <MemberModal
        isOpen={isMemberModalOpen}
        onClose={() => setIsMemberModalOpen(false)}
        onSave={handleSaveMember}
        initialData={editingMember}
      />

      <MetabolicModal
        isOpen={isMetabolicModalOpen}
        onClose={() => setIsMetabolicModalOpen(false)}
        member={metabolicModalData.member}
        target={metabolicModalData.target}
      />
    </div>
  )
}
