function HowItWorksStep({ step, icon, title, description }) {
  return (
    <div className="flex flex-col items-center text-center">
      {/* Step number */}
      <div className="flex h-[52px] w-[52px] items-center justify-center rounded-2xl bg-primary-600 text-lg font-bold text-white shadow-md shadow-primary-600/20">
        {step}
      </div>

      {/* Icon */}
      <div className="mt-5 flex h-11 w-11 items-center justify-center rounded-xl bg-cream text-primary-700">
        {icon}
      </div>

      {/* Text */}
      <h3 className="mt-4 text-[15px] font-bold text-text-primary">{title}</h3>
      <p className="mt-2 max-w-[240px] text-sm leading-relaxed text-text-secondary">{description}</p>
    </div>
  )
}

export default HowItWorksStep
