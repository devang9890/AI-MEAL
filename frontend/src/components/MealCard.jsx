function MealCard({ type, name, price, protein, calories, color }) {
  const palette = {
    amber: {
      bg: 'bg-gradient-to-br from-amber-50 to-amber-100/80',
      iconBg: 'bg-amber-200/60',
      iconText: 'text-amber-700',
      badge: 'bg-amber-500/90 text-white',
    },
    emerald: {
      bg: 'bg-gradient-to-br from-emerald-50 to-emerald-100/80',
      iconBg: 'bg-emerald-200/60',
      iconText: 'text-emerald-700',
      badge: 'bg-emerald-600/90 text-white',
    },
    orange: {
      bg: 'bg-gradient-to-br from-orange-50 to-orange-100/80',
      iconBg: 'bg-orange-200/60',
      iconText: 'text-orange-700',
      badge: 'bg-orange-500/90 text-white',
    },
    lime: {
      bg: 'bg-gradient-to-br from-lime-50 to-lime-100/80',
      iconBg: 'bg-lime-200/60',
      iconText: 'text-lime-700',
      badge: 'bg-lime-600/90 text-white',
    },
  }

  const c = palette[color]

  const iconsByColor = {
    amber: (
      <svg className={`h-7 w-7 ${c.iconText}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="4" />
        <path d="M12 2v2m0 16v2M4.93 4.93l1.41 1.41m11.32 11.32l1.41 1.41M2 12h2m16 0h2M4.93 19.07l1.41-1.41m11.32-11.32l1.41-1.41" />
      </svg>
    ),
    emerald: (
      <svg className={`h-7 w-7 ${c.iconText}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 2v7c0 1.1.9 2 2 2h4a2 2 0 002-2V2M7 2v20M21 15V2a5 5 0 00-5 5v6c0 1.1.9 2 2 2h3zM21 15v7" />
      </svg>
    ),
    orange: (
      <svg className={`h-7 w-7 ${c.iconText}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="5" />
      </svg>
    ),
    lime: (
      <svg className={`h-7 w-7 ${c.iconText}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M11 20A7 7 0 019.8 6.9C15.5 4.9 17 3.5 17 3.5s1 2.5-.5 7.5" />
        <path d="M11 20v-6.5a3 3 0 00-3-3H5" />
      </svg>
    ),
  }

  return (
    <div className="group overflow-hidden rounded-2xl border border-border-light bg-white transition-all duration-300 hover:border-border hover:shadow-lg hover:shadow-black/[0.06]">
      {/* Header */}
      <div className={`relative flex h-40 items-center justify-center ${c.bg}`}>
        <div className={`flex h-16 w-16 items-center justify-center rounded-2xl ${c.iconBg} transition-transform duration-300 group-hover:scale-110`}>
          {iconsByColor[color]}
        </div>
        <span className={`absolute left-4 top-4 rounded-full px-3 py-1 text-[10px] font-bold uppercase tracking-wider ${c.badge}`}>
          {type}
        </span>
      </div>

      {/* Content */}
      <div className="p-5">
        <h3 className="text-base font-bold text-text-primary">{name}</h3>
        <div className="mt-3 flex items-baseline gap-1">
          <span className="text-xl font-extrabold text-primary-600">{price}</span>
          <span className="text-xs text-text-muted">/ serving</span>
        </div>
        <div className="mt-3 flex items-center gap-4 text-xs text-text-secondary">
          <span className="font-medium">Protein {protein}</span>
          <span className="text-text-muted">{calories}</span>
        </div>
      </div>
    </div>
  )
}

export default MealCard
