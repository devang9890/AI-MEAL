import React from 'react'

function MetabolicModal({ isOpen, onClose, member, target }) {
  if (!isOpen || !member || !target) return null

  const isMale = member.gender === 'male'
  const baseVal = 10 * member.weight_kg + 6.25 * member.height_cm - 5 * member.age
  const constant = isMale ? 5 : -161
  const bmr = (baseVal + constant).toFixed(1)

  const activityMultipliers = {
    sedentary: 1.2,
    light: 1.375,
    moderate: 1.55,
    active: 1.725,
    very_active: 1.9,
  }
  const multiplier = activityMultipliers[member.activity_level] || 1.55
  const tdee = target.daily_calories ? target.daily_calories.toFixed(1) : (bmr * multiplier).toFixed(1)

  const proteinKcal = (target.daily_calories * 0.2).toFixed(0)
  const carbsKcal = (target.daily_calories * 0.5).toFixed(0)
  const fatKcal = (target.daily_calories * 0.3).toFixed(0)

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm animate-fade-in overflow-y-auto">
      <div className="relative w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-3xl bg-white p-6 sm:p-8 shadow-2xl transition-all my-8">
        {/* Header */}
        <div className="flex items-start justify-between pb-4 border-b border-border-light">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full bg-primary-50 px-3 py-1 text-xs font-bold text-primary-700 mb-2">
              <span>🧬 Mifflin–St Jeor Metabolic Model</span>
            </div>
            <h3 className="text-2xl font-black text-text-primary">
              Metabolic Breakdown for {member.name}
            </h3>
            <p className="text-xs text-text-muted mt-1">
              {member.age} yrs • {member.gender === 'male' ? 'Male' : 'Female'} • {member.height_cm} cm • {member.weight_kg} kg • Activity: {member.activity_level}
            </p>
          </div>
          <button
            onClick={onClose}
            className="rounded-xl p-2 text-text-muted hover:bg-cream hover:text-text-primary transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Steps */}
        <div className="mt-6 space-y-6">
          {/* Step 1: BMR */}
          <div className="rounded-2xl border border-primary-100 bg-primary-50/40 p-4 sm:p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-primary-700">Step 1 — Basal Metabolic Rate (BMR)</span>
              <span className="text-lg font-black text-primary-800">{bmr} kcal</span>
            </div>
            <p className="text-xs text-text-secondary mt-1">
              Minimum energy required to keep vital organs functioning at complete rest.
            </p>
            <div className="mt-3 rounded-xl bg-white/90 p-3 font-mono text-xs text-text-secondary border border-primary-100">
              <div className="text-[11px] text-text-muted mb-1">Mifflin-St Jeor formula ({isMale ? 'Male' : 'Female'}):</div>
              <div>BMR = (10 × {member.weight_kg} kg) + (6.25 × {member.height_cm} cm) - (5 × {member.age} yrs) {constant >= 0 ? `+ ${constant}` : `${constant}`}</div>
              <div className="mt-1 text-primary-700 font-bold">= {10 * member.weight_kg} + {(6.25 * member.height_cm).toFixed(1)} - {5 * member.age} {constant >= 0 ? `+ ${constant}` : `${constant}`} = {bmr} kcal</div>
            </div>
          </div>

          {/* Step 2: TDEE */}
          <div className="rounded-2xl border border-amber-200/80 bg-amber-50/40 p-4 sm:p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-amber-800">Step 2 — Total Daily Energy Expenditure (TDEE)</span>
              <span className="text-lg font-black text-amber-900">{tdee} kcal</span>
            </div>
            <p className="text-xs text-text-secondary mt-1">
              Caloric demand scaling BMR with physical activity level ({member.activity_level}).
            </p>
            <div className="mt-3 rounded-xl bg-white/90 p-3 font-mono text-xs text-text-secondary border border-amber-200/60">
              <div>TDEE = BMR × Activity Multiplier</div>
              <div className="mt-1 text-amber-800 font-bold">= {bmr} kcal × {multiplier} = {tdee} kcal / day</div>
            </div>
          </div>

          {/* Step 3: Macronutrients & Fiber */}
          <div className="rounded-2xl border border-border-light bg-cream/40 p-4 sm:p-5">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-text-secondary">Step 3 — Macronutrient & Fiber Split</span>
              <span className="text-xs font-medium text-text-muted">Target Ratios</span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-3">
              {/* Protein */}
              <div className="rounded-xl border border-emerald-200 bg-emerald-50/70 p-3 text-center">
                <div className="text-[10px] font-bold uppercase tracking-wider text-emerald-700">Protein (20%)</div>
                <div className="text-xl font-black text-emerald-800 mt-1">{target.daily_protein_g}g</div>
                <div className="text-[10px] text-emerald-600 mt-0.5">{proteinKcal} kcal (4 kcal/g)</div>
              </div>

              {/* Carbs */}
              <div className="rounded-xl border border-amber-200 bg-amber-50/70 p-3 text-center">
                <div className="text-[10px] font-bold uppercase tracking-wider text-amber-700">Carbs (50%)</div>
                <div className="text-xl font-black text-amber-800 mt-1">{target.daily_carbs_g}g</div>
                <div className="text-[10px] text-amber-600 mt-0.5">{carbsKcal} kcal (4 kcal/g)</div>
              </div>

              {/* Fat */}
              <div className="rounded-xl border border-rose-200 bg-rose-50/70 p-3 text-center">
                <div className="text-[10px] font-bold uppercase tracking-wider text-rose-700">Fat (30%)</div>
                <div className="text-xl font-black text-rose-800 mt-1">{target.daily_fat_g}g</div>
                <div className="text-[10px] text-rose-600 mt-0.5">{fatKcal} kcal (9 kcal/g)</div>
              </div>

              {/* Fiber */}
              <div className="rounded-xl border border-teal-200 bg-teal-50/70 p-3 text-center">
                <div className="text-[10px] font-bold uppercase tracking-wider text-teal-700">Fiber</div>
                <div className="text-xl font-black text-teal-800 mt-1">{target.daily_fiber_g}g</div>
                <div className="text-[10px] text-teal-600 mt-0.5">14g / 1,000 kcal</div>
              </div>
            </div>
          </div>

          {/* Educational Disclaimer */}
          <div className="rounded-xl bg-gray-50 border border-border-light p-3.5 text-xs text-text-muted">
            <div className="flex items-center gap-1.5 font-bold text-text-secondary mb-1">
              <span>ℹ️ Educational Disclaimer</span>
            </div>
            These calculations represent mathematical estimates intended for algorithmic meal planning and educational purposes. Individuals with medical conditions or clinical requirements should consult a licensed healthcare professional.
          </div>
        </div>

        {/* Footer */}
        <div className="mt-6 flex justify-end">
          <button
            onClick={onClose}
            className="rounded-xl bg-text-primary px-6 py-2.5 text-sm font-semibold text-white hover:bg-black transition-colors"
          >
            Close Breakdown
          </button>
        </div>
      </div>
    </div>
  )
}

export default MetabolicModal
