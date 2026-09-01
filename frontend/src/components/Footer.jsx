import { Link, useLocation } from 'react-router-dom'

function Footer() {
  const location = useLocation()
  const isLanding = location.pathname === '/'

  const scrollToSection = (id) => {
    if (!isLanding) {
      window.location.href = `/#${id}`
      return
    }
    const el = document.getElementById(id)
    if (el) el.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <footer className="border-t border-border-light bg-white">
      <div className="mx-auto max-w-7xl px-6 py-14">
        <div className="flex flex-col items-center gap-8 md:flex-row md:justify-between">
          {/* Brand */}
          <div className="text-center md:text-left">
            <div className="flex items-center justify-center gap-3 md:justify-start">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-600">
                <svg className="h-4 w-4 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M3 2v7c0 1.1.9 2 2 2h4a2 2 0 002-2V2" /><path d="M7 2v20" /><path d="M21 15V2a5 5 0 00-5 5v6c0 1.1.9 2 2 2h3z" /><path d="M21 15v7" />
                </svg>
              </div>
              <span className="text-base font-bold text-text-primary">AI Meal Planner</span>
            </div>
            <div className="mt-3 space-y-0.5">
              <p className="text-sm text-text-muted">Affordable meals.</p>
              <p className="text-sm text-text-muted">Smarter nutrition.</p>
              <p className="text-sm text-text-muted">Better planning.</p>
            </div>
          </div>

          {/* Links */}
          <div className="flex items-center gap-8">
            <button onClick={() => scrollToSection('how-it-works')} className="text-sm font-medium text-text-secondary transition-colors hover:text-primary-600">How It Works</button>
            <button onClick={() => scrollToSection('features')} className="text-sm font-medium text-text-secondary transition-colors hover:text-primary-600">Features</button>
            <Link to="/login" className="text-sm font-medium text-text-secondary transition-colors hover:text-primary-600">Login</Link>
          </div>
        </div>

        <div className="mt-10 border-t border-border-light pt-6 text-center">
          <p className="text-xs text-text-muted">&copy; 2026 AI Meal Planner</p>
        </div>
      </div>
    </footer>
  )
}

export default Footer
