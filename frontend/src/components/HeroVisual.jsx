function HeroVisual() {
  return (
    <div className="relative mx-auto w-full max-w-sm sm:max-w-md lg:max-w-lg">
      <div
        className="relative overflow-hidden rounded-3xl bg-cream p-3 sm:p-5"
        style={{
          backgroundImage: 'radial-gradient(circle, rgba(214,209,203,0.3) 1px, transparent 1px)',
          backgroundSize: '16px 16px',
        }}
      >
        {/* Decorative blurs */}
        <div className="absolute -right-16 -top-16 h-48 w-48 rounded-full bg-primary-200/25 blur-3xl" />
        <div className="absolute -bottom-12 -left-12 h-40 w-40 rounded-full bg-amber-200/25 blur-3xl" />

        {/* Floating: Weekly Budget */}
        <div className="animate-float-slow absolute -right-2 top-2 z-20 hidden rounded-2xl bg-white px-4 py-3 shadow-lg shadow-black/[0.06] sm:block">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-text-muted">Weekly Budget</p>
          <p className="mt-0.5 text-xl font-extrabold text-primary-700">&#8377;5,000</p>
          <div className="mt-2 h-1.5 w-28 overflow-hidden rounded-full bg-primary-100">
            <div className="h-full w-[65%] rounded-full bg-primary-500" />
          </div>
          <p className="mt-1 text-[9px] text-text-muted">&#8377;3,275 remaining</p>
        </div>

        {/* Main meal-plan card */}
        <div className="relative z-10 mt-8 rounded-2xl bg-white p-4 shadow-xl shadow-black/[0.06] sm:mx-2 sm:mt-12 sm:p-5">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-border-light pb-3">
            <div>
              <h3 className="text-sm font-bold text-text-primary">Today&rsquo;s Meals</h3>
              <p className="mt-0.5 text-[11px] text-text-muted">Monday, Sep 1</p>
            </div>
            <span className="rounded-full bg-primary-50 px-3 py-1 text-[10px] font-bold text-primary-700">3 meals</span>
          </div>

          {/* Rows */}
          <div className="mt-3 space-y-2">
            {/* Breakfast */}
            <div className="flex items-center gap-3 rounded-xl bg-amber-50/60 p-2.5">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-amber-100/80">
                <svg className="h-4 w-4 text-amber-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="4" />
                  <path d="M12 2v2m0 16v2M4.93 4.93l1.41 1.41m11.32 11.32l1.41 1.41M2 12h2m16 0h2M4.93 19.07l1.41-1.41m11.32-11.32l1.41-1.41" />
                </svg>
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-xs font-semibold text-text-primary">Vegetable Poha</p>
                <p className="text-[10px] text-text-muted">Protein 8g &middot; 250 cal</p>
              </div>
              <span className="text-sm font-bold text-text-primary">&#8377;35</span>
            </div>

            {/* Lunch */}
            <div className="flex items-center gap-3 rounded-xl bg-emerald-50/60 p-2.5">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-emerald-100/80">
                <svg className="h-4 w-4 text-emerald-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M3 2v7c0 1.1.9 2 2 2h4a2 2 0 002-2V2M7 2v20M21 15V2a5 5 0 00-5 5v6c0 1.1.9 2 2 2h3zM21 15v7" />
                </svg>
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-xs font-semibold text-text-primary">Dal Rice + Salad</p>
                <p className="text-[10px] text-text-muted">Protein 16g &middot; 420 cal</p>
              </div>
              <span className="text-sm font-bold text-text-primary">&#8377;55</span>
            </div>

            {/* Dinner */}
            <div className="flex items-center gap-3 rounded-xl bg-orange-50/60 p-2.5">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-orange-100/80">
                <svg className="h-4 w-4 text-orange-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="5" />
                </svg>
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-xs font-semibold text-text-primary">Paneer Roti Bowl</p>
                <p className="text-[10px] text-text-muted">Protein 28g &middot; 550 cal</p>
              </div>
              <span className="text-sm font-bold text-text-primary">&#8377;85</span>
            </div>
          </div>

          {/* Total */}
          <div className="mt-3 flex items-center justify-between rounded-xl bg-primary-50 p-3">
            <span className="text-xs font-medium text-primary-700">Daily Total</span>
            <span className="text-base font-extrabold text-primary-700">&#8377;175</span>
          </div>
        </div>

        {/* Bottom floating badges */}
        <div className="relative z-10 mt-3 flex flex-wrap gap-2 sm:mx-2 sm:mt-4">
          <div className="animate-float-delayed rounded-xl bg-white px-3 py-2 shadow-md shadow-black/[0.04]">
            <p className="text-[10px] text-text-muted">Protein</p>
            <p className="text-xs font-bold text-primary-600">52g / day</p>
          </div>
          <div className="animate-float flex items-center gap-1.5 rounded-full bg-primary-600 px-4 py-2 shadow-md shadow-primary-600/20">
            <svg className="h-3.5 w-3.5 text-white" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
            <span className="text-[11px] font-semibold text-white">Budget Friendly</span>
          </div>
          <div className="animate-float-slow rounded-xl bg-white px-3 py-2 shadow-md shadow-black/[0.04]">
            <p className="text-[10px] text-text-muted">Calories</p>
            <p className="text-xs font-bold text-accent-orange">1,220 cal</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default HeroVisual
