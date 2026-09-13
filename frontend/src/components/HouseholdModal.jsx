import { useState, useEffect } from 'react'

function HouseholdModal({ isOpen, onClose, onSave, initialData = null, isSaving = false }) {
  const [name, setName] = useState('')
  const [weeklyBudget, setWeeklyBudget] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    if (initialData) {
      setName(initialData.name || '')
      setWeeklyBudget(initialData.weekly_budget ? String(initialData.weekly_budget) : '')
    } else {
      setName('')
      setWeeklyBudget('')
    }
    setError('')
  }, [initialData, isOpen])

  if (!isOpen) return null

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!name.trim()) {
      setError('Please enter a household name.')
      return
    }
    const budgetVal = weeklyBudget ? parseFloat(weeklyBudget) : null
    if (budgetVal !== null && (isNaN(budgetVal) || budgetVal < 0)) {
      setError('Weekly budget must be a positive number.')
      return
    }

    onSave({
      name: name.trim(),
      weekly_budget: budgetVal,
    })
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl transition-all">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-border-light">
          <div>
            <h3 className="text-xl font-bold text-text-primary">
              {initialData ? 'Edit Household' : 'Create New Household'}
            </h3>
            <p className="text-xs text-text-muted mt-0.5">
              Set up your shared meal-planning and grocery budget space
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
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-text-secondary mb-1">
              Household Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              placeholder="e.g. Sharma Family, Flat 402, The Roys"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full rounded-xl border border-border-light bg-cream/40 px-3.5 py-2.5 text-sm font-medium text-text-primary placeholder:text-text-muted focus:border-primary-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary-500/20 transition-all"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-text-secondary mb-1">
              Weekly Grocery Budget (₹)
            </label>
            <div className="relative">
              <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-sm font-semibold text-text-muted">
                ₹
              </span>
              <input
                type="number"
                min="0"
                step="50"
                placeholder="e.g. 3500 (optional)"
                value={weeklyBudget}
                onChange={(e) => setWeeklyBudget(e.target.value)}
                className="w-full rounded-xl border border-border-light bg-cream/40 pl-8 pr-3.5 py-2.5 text-sm font-medium text-text-primary placeholder:text-text-muted focus:border-primary-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary-500/20 transition-all"
              />
            </div>
            <p className="mt-1 text-[11px] text-text-muted">
              Used to optimize recipe costs and grocery lists for your family
            </p>
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
                <span>{initialData ? 'Update Household' : 'Create Household'}</span>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default HouseholdModal
