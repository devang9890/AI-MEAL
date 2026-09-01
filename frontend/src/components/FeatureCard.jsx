function FeatureCard({ icon, title, description, accent = 'primary' }) {
  const styles = {
    primary: 'bg-primary-50 text-primary-600 group-hover:bg-primary-100',
    amber:   'bg-amber-50 text-amber-600 group-hover:bg-amber-100',
    orange:  'bg-orange-50 text-orange-600 group-hover:bg-orange-100',
    emerald: 'bg-emerald-50 text-emerald-600 group-hover:bg-emerald-100',
    sky:     'bg-sky-50 text-sky-600 group-hover:bg-sky-100',
    violet:  'bg-violet-50 text-violet-600 group-hover:bg-violet-100',
  }

  return (
    <div className="group rounded-2xl border border-border-light bg-white p-6 transition-all duration-300 hover:border-primary-200/60 hover:shadow-lg hover:shadow-black/[0.04]">
      <div className={`mb-5 flex h-12 w-12 items-center justify-center rounded-xl transition-colors duration-300 ${styles[accent]}`}>
        {icon}
      </div>
      <h3 className="mb-2 text-[15px] font-bold text-text-primary">{title}</h3>
      <p className="text-sm leading-relaxed text-text-secondary">{description}</p>
    </div>
  )
}

export default FeatureCard
