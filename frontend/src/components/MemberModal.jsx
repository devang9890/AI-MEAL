import { useState, useEffect } from 'react'

const ACTIVITY_OPTIONS = [
  { value: 'sedentary', label: 'Sedentary (1.2×)', desc: 'Desk job, little to no weekly exercise' },
  { value: 'light', label: 'Light Active (1.375×)', desc: 'Light exercise / walks 1–3 days/week' },
  { value: 'moderate', label: 'Moderately Active (1.55×)', desc: 'Moderate workouts / sports 3–5 days/week' },
  { value: 'active', label: 'Very Active (1.725×)', desc: 'Vigorous training 6–7 days/week' },
  { value: 'very_active', label: 'Extremely Active (1.9×)', desc: 'Athletic competition or physical labor' },
]

const DIETARY_OPTIONS = [
  { value: 'vegetarian', label: 'Vegetarian' },
  { value: 'vegan', label: 'Vegan' },
  { value: 'eggetarian', label: 'Eggetarian' },
  { value: 'non_vegetarian', label: 'Non-Vegetarian' },
  { value: 'pescatarian', label: 'Pescatarian' },
]

function MemberModal({ isOpen, onClose, onSave, initialData = null, isSaving = false }) {
  const [name, setName] = useState('')
  const [age, setAge] = useState('')
  const [gender, setGender] = useState('male')
  const [heightCm, setHeightCm] = useState('')
  const [weightKg, setWeightKg] = useState('')
  const [activityLevel, setActivityLevel] = useState('moderate')
  const [dietaryPreference, setDietaryPreference] = useState('vegetarian')
  const [allergiesText, setAllergiesText] = useState('')
  const [restrictionsText, setRestrictionsText] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    if (initialData) {
      setName(initialData.name || '')
      setAge(initialData.age ? String(initialData.age) : '')
      setGender(initialData.gender || 'male')
      setHeightCm(initialData.height_cm ? String(initialData.height_cm) : '')
      setWeightKg(initialData.weight_kg ? String(initialData.weight_kg) : '')
      setActivityLevel(initialData.activity_level || 'moderate')
      setDietaryPreference(initialData.dietary_preference || 'vegetarian')
      setAllergiesText(Array.isArray(initialData.allergies) ? initialData.allergies.join(', ') : '')
      setRestrictionsText(Array.isArray(initialData.dietary_restrictions) ? initialData.dietary_restrictions.join(', ') : '')
    } else {
      setName('')
      setAge('')
      setGender('male')
      setHeightCm('')
      setWeightKg('')
      setActivityLevel('moderate')
      setDietaryPreference('vegetarian')
      setAllergiesText('')
      setRestrictionsText('')
    }
    setError('')
  }, [initialData, isOpen])

  if (!isOpen) return null

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!name.trim()) {
      setError('Please enter member name.')
      return
    }
    const ageNum = parseInt(age, 10)
    if (isNaN(ageNum) || ageNum <= 0) {
      setError('Age must be a positive number greater than 0.')
      return
    }
    const heightNum = parseFloat(heightCm)
    if (isNaN(heightNum) || heightNum <= 0) {
      setError('Height must be a positive number (cm).')
      return
    }
    const weightNum = parseFloat(weightKg)
    if (isNaN(weightNum) || weightNum <= 0) {
      setError('Weight must be a positive number (kg).')
      return
    }

    const allergies = allergiesText
      ? allergiesText.split(',').map((s) => s.trim().toLowerCase()).filter(Boolean)
      : []

    const restrictions = restrictionsText
      ? restrictionsText.split(',').map((s) => s.trim().toLowerCase()).filter(Boolean)
      : []

    onSave({
      name: name.trim(),
      age: ageNum,
      gender,
      height_cm: heightNum,
      weight_kg: weightNum,
      activity_level: activityLevel,
      dietary_preference: dietaryPreference,
      allergies,
      dietary_restrictions: restrictions,
    })
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm animate-fade-in overflow-y-auto">
      <div className="relative w-full max-w-xl max-h-[90vh] overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl transition-all my-8">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-border-light">
          <div>
            <h3 className="text-xl font-bold text-text-primary">
              {initialData ? 'Edit Family Member' : 'Add Family Member'}
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

        {/* Error message */}
        {error && (
          <div className="mt-4 rounded-xl bg-red-50 border border-red-200 p-3 text-xs font-medium text-red-700">
            {error}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="mt-5 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Name */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-text-secondary mb-1">
                Full Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                placeholder="e.g. Rahul, Priya, Grandfather"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full rounded-xl border border-border-light bg-cream/40 px-3.5 py-2.5 text-sm font-medium text-text-primary placeholder:text-text-muted focus:border-primary-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary-500/20 transition-all"
                required
              />
            </div>

            {/* Age */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-text-secondary mb-1">
                Age (Years) <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                min="1"
                max="120"
                placeholder="e.g. 28"
                value={age}
                onChange={(e) => setAge(e.target.value)}
                className="w-full rounded-xl border border-border-light bg-cream/40 px-3.5 py-2.5 text-sm font-medium text-text-primary placeholder:text-text-muted focus:border-primary-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary-500/20 transition-all"
                required
              />
            </div>
          </div>

          {/* Gender */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-text-secondary mb-1">
              Biological Sex <span className="text-red-500">*</span>
            </label>
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setGender('male')}
                className={`flex items-center justify-center gap-2 rounded-xl border py-2.5 text-sm font-semibold transition-all ${
                  gender === 'male'
                    ? 'border-primary-600 bg-primary-50 text-primary-800 shadow-sm'
                    : 'border-border-light bg-white text-text-secondary hover:bg-cream'
                }`}
              >
                <span>👨 Male</span>
              </button>
              <button
                type="button"
                onClick={() => setGender('female')}
                className={`flex items-center justify-center gap-2 rounded-xl border py-2.5 text-sm font-semibold transition-all ${
                  gender === 'female'
                    ? 'border-primary-600 bg-primary-50 text-primary-800 shadow-sm'
                    : 'border-border-light bg-white text-text-secondary hover:bg-cream'
                }`}
              >
                <span>👩 Female</span>
              </button>
            </div>
          </div>

          {/* Height & Weight */}
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
                value={heightCm}
                onChange={(e) => setHeightCm(e.target.value)}
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
                value={weightKg}
                onChange={(e) => setWeightKg(e.target.value)}
                className="w-full rounded-xl border border-border-light bg-cream/40 px-3.5 py-2.5 text-sm font-medium text-text-primary placeholder:text-text-muted focus:border-primary-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary-500/20 transition-all"
                required
              />
            </div>
          </div>

          {/* Physical Activity Level */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-text-secondary mb-1">
              Physical Activity Level <span className="text-red-500">*</span>
            </label>
            <select
              value={activityLevel}
              onChange={(e) => setActivityLevel(e.target.value)}
              className="w-full rounded-xl border border-border-light bg-cream/40 px-3.5 py-2.5 text-sm font-medium text-text-primary focus:border-primary-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary-500/20 transition-all"
            >
              {ACTIVITY_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label} — {opt.desc}
                </option>
              ))}
            </select>
          </div>

          {/* Dietary Preference */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-text-secondary mb-1">
              Dietary Preference <span className="text-red-500">*</span>
            </label>
            <select
              value={dietaryPreference}
              onChange={(e) => setDietaryPreference(e.target.value)}
              className="w-full rounded-xl border border-border-light bg-cream/40 px-3.5 py-2.5 text-sm font-medium text-text-primary focus:border-primary-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary-500/20 transition-all"
            >
              {DIETARY_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          {/* Allergies & Dietary Restrictions */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-text-secondary mb-1">
                Allergies (comma-separated)
              </label>
              <input
                type="text"
                placeholder="e.g. peanuts, dairy, gluten"
                value={allergiesText}
                onChange={(e) => setAllergiesText(e.target.value)}
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
                value={restrictionsText}
                onChange={(e) => setRestrictionsText(e.target.value)}
                className="w-full rounded-xl border border-border-light bg-cream/40 px-3.5 py-2.5 text-sm font-medium text-text-primary placeholder:text-text-muted focus:border-primary-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary-500/20 transition-all"
              />
            </div>
          </div>

          {/* Action buttons */}
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
                <span>{initialData ? 'Update Member' : 'Save Member'}</span>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default MemberModal
