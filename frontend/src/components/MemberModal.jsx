import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMemberDraft, memberToDraft } from '../context/MemberDraftContext'

const ACTIVITY_OPTIONS = [
  { value: 'sedentary', label: 'Sedentary (1.2x)', desc: 'Desk job, little to no weekly exercise' },
  { value: 'light', label: 'Light Active (1.375x)', desc: 'Light exercise / walks 1–3 days/week' },
  { value: 'moderate', label: 'Moderately Active (1.55x)', desc: 'Moderate workouts / sports 3–5 days/week' },
  { value: 'active', label: 'Very Active (1.725x)', desc: 'Vigorous training 6–7 days/week' },
  { value: 'very_active', label: 'Extremely Active (1.9x)', desc: 'Athletic competition or physical labor' },
]

const DIETARY_OPTIONS = [
  { value: 'vegetarian', label: 'Vegetarian' },
  { value: 'vegan', label: 'Vegan' },
  { value: 'eggitarian', label: 'Eggitarian' },
  { value: 'non_vegetarian', label: 'Non-Vegetarian' },
]

function MemberModal({ isOpen, onClose, onSave, initialData = null, householdId = null, isSaving = false }) {
  const navigate = useNavigate()
  const { draft, startDraft, updateDraft, refreshFromStorage } = useMemberDraft()
  const seededSession = useRef(null)
  const [error, setError] = useState('')

  // Hydrate / seed draft once per modal-open session. Prefer an existing
  // sessionStorage draft (allergy/disease round-trip) over a blank reset.
  useEffect(() => {
    if (!isOpen) {
      seededSession.current = null
      return
    }

    const sessionKey = initialData?.id
      ? `edit-${initialData.id}`
      : `add-${householdId ?? 'new'}`

    if (seededSession.current === sessionKey) return
    seededSession.current = sessionKey

    const existing = refreshFromStorage()
    const editingSameMember =
      existing &&
      initialData?.id &&
      String(existing.memberId) === String(initialData.id)

    const resumingAddDraft =
      existing &&
      !initialData?.id &&
      !existing.isEdit &&
      (existing.householdId == null ||
        String(existing.householdId) === String(householdId))

    if (editingSameMember || resumingAddDraft) {
      // Keep draft as-is; only refresh household id if missing.
      if (householdId && !existing.householdId) {
        updateDraft({ householdId })
      }
      setError('')
      return
    }

    if (initialData?.id) {
      startDraft(
        memberToDraft(initialData, { householdId, isEdit: true })
      )
    } else {
      startDraft(
        memberToDraft(null, { householdId, isEdit: false })
      )
    }
    setError('')
  }, [
    isOpen,
    initialData,
    householdId,
    refreshFromStorage,
    startDraft,
    updateDraft,
  ])

  if (!isOpen) return null

  const form = draft || memberToDraft(initialData, { householdId, isEdit: Boolean(initialData?.id) })
  const isEditingExistingMember = Boolean(form.isEdit && form.memberId)

  const setField = (field, value) => {
    updateDraft({ [field]: value })
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!form.name.trim()) {
      setError('Please enter member name.')
      return
    }
    const ageNum = parseInt(form.age, 10)
    if (isNaN(ageNum) || ageNum <= 0) {
      setError('Age must be a positive number greater than 0.')
      return
    }
    const heightNum = parseFloat(form.height_cm)
    if (isNaN(heightNum) || heightNum <= 0) {
      setError('Height must be a positive number (cm).')
      return
    }
    const weightNum = parseFloat(form.weight_kg)
    if (isNaN(weightNum) || weightNum <= 0) {
      setError('Weight must be a positive number (kg).')
      return
    }

    onSave({
      name: form.name.trim(),
      age: ageNum,
      gender: form.gender,
      height_cm: heightNum,
      weight_kg: weightNum,
      activity_level: form.activity_level,
      dietary_preference: form.dietary_preference,
      allergies: form.allergies.trim() ? form.allergies.trim() : null,
      diseases: form.diseases.trim() ? form.diseases.trim() : null,
      dietary_restrictions: form.dietary_restrictions.trim()
        ? form.dietary_restrictions.trim()
        : null,
    })
  }

  const browseHealthSelections = (destination) => {
    // Persist latest household linkage, then navigate. No API calls.
    updateDraft({
      householdId: householdId ?? form.householdId,
      isEdit: isEditingExistingMember,
      memberId: isEditingExistingMember ? form.memberId : null,
    })
    navigate(`/${destination}?flow=member-draft`)
  }

  const selectionCount = (value) =>
    (value || '')
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean).length

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm animate-fade-in overflow-y-auto">
      <div className="relative w-full max-w-xl max-h-[90vh] overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl transition-all my-8">
        <div className="flex items-center justify-between pb-4 border-b border-border-light">
          <div>
            <h3 className="text-xl font-bold text-text-primary">
              {isEditingExistingMember ? 'Edit Family Member' : 'Add Family Member'}
            </h3>
            <p className="text-xs text-text-muted mt-0.5">
              Accurate biometrics enable precise BMR & TDEE nutrition modeling
            </p>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-text-muted hover:bg-cream hover:text-text-primary transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {error && (
          <div className="mt-4 rounded-xl bg-red-50 border border-red-200 p-3 text-xs font-medium text-red-700">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-5 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-text-secondary mb-1">
                Full Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                placeholder="e.g. Rahul, Priya, Grandfather"
                value={form.name}
                onChange={(e) => setField('name', e.target.value)}
                className="w-full rounded-xl border border-border-light bg-cream/40 px-3.5 py-2.5 text-sm font-medium text-text-primary placeholder:text-text-muted focus:border-primary-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary-500/20 transition-all"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-text-secondary mb-1">
                Age (Years) <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                min="1"
                max="120"
                placeholder="e.g. 28"
                value={form.age}
                onChange={(e) => setField('age', e.target.value)}
                className="w-full rounded-xl border border-border-light bg-cream/40 px-3.5 py-2.5 text-sm font-medium text-text-primary placeholder:text-text-muted focus:border-primary-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary-500/20 transition-all"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-text-secondary mb-1">
              Biological Sex <span className="text-red-500">*</span>
            </label>
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setField('gender', 'male')}
                className={`flex items-center justify-center gap-2 rounded-xl border py-2.5 text-sm font-semibold transition-all ${
                  form.gender === 'male'
                    ? 'border-primary-600 bg-primary-50 text-primary-800 shadow-sm'
                    : 'border-border-light bg-white text-text-secondary hover:bg-cream'
                }`}
              >
                <span>👨 Male</span>
              </button>
              <button
                type="button"
                onClick={() => setField('gender', 'female')}
                className={`flex items-center justify-center gap-2 rounded-xl border py-2.5 text-sm font-semibold transition-all ${
                  form.gender === 'female'
                    ? 'border-primary-600 bg-primary-50 text-primary-800 shadow-sm'
                    : 'border-border-light bg-white text-text-secondary hover:bg-cream'
                }`}
              >
                <span>👩 Female</span>
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-text-secondary mb-1">
                Height (cm) <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                min="40"
                max="250"
                step="0.5"
                placeholder="e.g. 170"
                value={form.height_cm}
                onChange={(e) => setField('height_cm', e.target.value)}
                className="w-full rounded-xl border border-border-light bg-cream/40 px-3.5 py-2.5 text-sm font-medium text-text-primary placeholder:text-text-muted focus:border-primary-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary-500/20 transition-all"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-text-secondary mb-1">
                Weight (kg) <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                min="5"
                max="300"
                step="0.5"
                placeholder="e.g. 65"
                value={form.weight_kg}
                onChange={(e) => setField('weight_kg', e.target.value)}
                className="w-full rounded-xl border border-border-light bg-cream/40 px-3.5 py-2.5 text-sm font-medium text-text-primary placeholder:text-text-muted focus:border-primary-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary-500/20 transition-all"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-text-secondary mb-1">
              Physical Activity Level <span className="text-red-500">*</span>
            </label>
            <select
              value={form.activity_level}
              onChange={(e) => setField('activity_level', e.target.value)}
              className="w-full rounded-xl border border-border-light bg-cream/40 px-3.5 py-2.5 text-sm font-medium text-text-primary focus:border-primary-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary-500/20 transition-all"
            >
              {ACTIVITY_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label} — {opt.desc}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-text-secondary mb-1">
              Dietary Preference <span className="text-red-500">*</span>
            </label>
            <select
              value={form.dietary_preference}
              onChange={(e) => setField('dietary_preference', e.target.value)}
              className="w-full rounded-xl border border-border-light bg-cream/40 px-3.5 py-2.5 text-sm font-medium text-text-primary focus:border-primary-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary-500/20 transition-all"
            >
              {DIETARY_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
            <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2">
              <button
                type="button"
                onClick={() => browseHealthSelections('allergies')}
                className="rounded-xl border border-primary-200 bg-primary-50 px-3 py-2 text-center text-xs font-semibold text-primary-800 hover:bg-primary-100"
              >
                Browse Allergies
                {selectionCount(form.allergies)
                  ? ` · ${selectionCount(form.allergies)} selected`
                  : ''}
              </button>
              <button
                type="button"
                onClick={() => browseHealthSelections('diseases')}
                className="rounded-xl border border-primary-200 bg-primary-50 px-3 py-2 text-center text-xs font-semibold text-primary-800 hover:bg-primary-100"
              >
                Browse Diseases
                {selectionCount(form.diseases)
                  ? ` · ${selectionCount(form.diseases)} selected`
                  : ''}
              </button>
            </div>
            <p className="mt-2 text-[11px] text-text-muted">
              Selections stay with this form until you save the family member.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-text-secondary mb-1">
                Allergies (comma-separated)
              </label>
              <input
                type="text"
                placeholder="e.g. peanuts, dairy, gluten"
                value={form.allergies}
                onChange={(e) => setField('allergies', e.target.value)}
                className="w-full rounded-xl border border-border-light bg-cream/40 px-3.5 py-2.5 text-sm font-medium text-text-primary placeholder:text-text-muted focus:border-primary-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary-500/20 transition-all"
              />
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-text-secondary mb-1">
                Health conditions (selected)
              </label>
              <input
                type="text"
                placeholder="Use Browse Diseases to select"
                value={form.diseases}
                onChange={(e) => setField('diseases', e.target.value)}
                className="w-full rounded-xl border border-border-light bg-cream/40 px-3.5 py-2.5 text-sm font-medium text-text-primary placeholder:text-text-muted focus:border-primary-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary-500/20 transition-all"
              />
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-text-secondary mb-1">
                Restrictions (comma-separated)
              </label>
              <input
                type="text"
                placeholder="e.g. jain, halal, low-sodium"
                value={form.dietary_restrictions}
                onChange={(e) => setField('dietary_restrictions', e.target.value)}
                className="w-full rounded-xl border border-border-light bg-cream/40 px-3.5 py-2.5 text-sm font-medium text-text-primary placeholder:text-text-muted focus:border-primary-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary-500/20 transition-all"
              />
            </div>
          </div>

          <div className="mt-6 flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-xl border border-border-light px-4 py-2 text-sm font-medium text-text-secondary hover:bg-cream transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSaving}
              className="inline-flex items-center gap-2 rounded-xl bg-primary-600 px-5 py-2 text-sm font-semibold text-white shadow-sm shadow-primary-600/20 hover:bg-primary-700 disabled:opacity-50 transition-all"
            >
              {isSaving ? (
                <>
                  <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                  </svg>
                  <span>Saving...</span>
                </>
              ) : (
                <span>{isEditingExistingMember ? 'Update Member' : 'Save Member'}</span>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default MemberModal
