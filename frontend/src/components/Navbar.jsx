import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { SignedIn, SignedOut, UserButton } from '@clerk/clerk-react'

function Navbar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const location = useLocation()
  const isLanding = location.pathname === '/'

  const scrollToSection = (id) => {
    setMobileMenuOpen(false)
    if (!isLanding) {
      window.location.href = `/#${id}`
      return
    }
    const el = document.getElementById(id)
    if (el) el.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <nav className="sticky top-0 z-50 border-b border-border-light/60 bg-white/95 backdrop-blur-lg">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary-600 shadow-sm shadow-primary-600/20">
            <svg className="h-[18px] w-[18px] text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 2v7c0 1.1.9 2 2 2h4a2 2 0 002-2V2" />
              <path d="M7 2v20" />
              <path d="M21 15V2a5 5 0 00-5 5v6c0 1.1.9 2 2 2h3z" />
              <path d="M21 15v7" />
            </svg>
          </div>
          <span className="text-lg font-bold tracking-tight text-text-primary">AI Meal Planner</span>
        </Link>

        {/* Desktop nav */}
        <div className="hidden items-center gap-1 md:flex">
          <Link
            to="/recipes"
            className={`rounded-lg px-3.5 py-2 text-sm font-medium transition-colors ${
              location.pathname === '/recipes'
                ? 'bg-primary-50 font-bold text-primary-700'
                : 'text-text-secondary hover:bg-cream hover:text-text-primary'
            }`}
          >
            Recipes
          </Link>
          <Link
            to="/ingredients"
            className={`rounded-lg px-3.5 py-2 text-sm font-medium transition-colors ${
              location.pathname === '/ingredients'
                ? 'bg-primary-50 font-bold text-primary-700'
                : 'text-text-secondary hover:bg-cream hover:text-text-primary'
            }`}
          >
            Ingredients
          </Link>
          <Link
            to="/household"
            className={`rounded-lg px-3.5 py-2 text-sm font-medium transition-colors ${
              location.pathname === '/household'
                ? 'bg-primary-50 font-bold text-primary-700'
                : 'text-text-secondary hover:bg-cream hover:text-text-primary'
            }`}
          >
            Household & Nutrition
          </Link>
          <button
            onClick={() => scrollToSection('how-it-works')}
            className="rounded-lg px-3.5 py-2 text-sm font-medium text-text-secondary transition-colors hover:bg-cream hover:text-text-primary"
          >
            How It Works
          </button>
          <button
            onClick={() => scrollToSection('features')}
            className="rounded-lg px-3.5 py-2 text-sm font-medium text-text-secondary transition-colors hover:bg-cream hover:text-text-primary"
          >
            Features
          </button>
          <div className="mx-3 h-5 w-px bg-border-light" />

          {/* Signed-out state: show Login / Sign up links */}
          <SignedOut>
            <Link
              to="/login"
              className="rounded-lg px-4 py-2 text-sm font-medium text-text-secondary transition-colors hover:bg-cream hover:text-text-primary"
            >
              Login
            </Link>
            <Link
              to="/register"
              className="ml-1 rounded-xl bg-primary-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm shadow-primary-600/20 transition-all hover:bg-primary-700 hover:shadow-md hover:shadow-primary-600/25 active:scale-[0.98]"
            >
              Sign Up
            </Link>
          </SignedOut>

          {/* Signed-in state: Clerk UserButton (avatar + profile menu) */}
          <SignedIn>
            <UserButton
              afterSignOutUrl="/"
              appearance={{
                elements: {
                  avatarBox: 'h-9 w-9',
                },
              }}
            />
          </SignedIn>
        </div>

        {/* Mobile toggle */}
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="flex h-10 w-10 items-center justify-center rounded-xl text-text-secondary transition-colors hover:bg-cream md:hidden"
          aria-label="Toggle menu"
        >
          {mobileMenuOpen ? (
            <svg className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
          ) : (
            <svg className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" /></svg>
          )}
        </button>
      </div>

      {/* Mobile menu */}
      {mobileMenuOpen && (
        <div className="border-t border-border-light bg-white px-6 py-5 md:hidden">
          <div className="flex flex-col gap-1">
            <Link
              to="/recipes"
              onClick={() => setMobileMenuOpen(false)}
              className="rounded-lg px-3 py-2.5 text-left text-sm font-medium text-text-secondary transition-colors hover:bg-cream hover:text-text-primary"
            >
              Recipes
            </Link>
            <Link
              to="/ingredients"
              onClick={() => setMobileMenuOpen(false)}
              className="rounded-lg px-3 py-2.5 text-left text-sm font-medium text-text-secondary transition-colors hover:bg-cream hover:text-text-primary"
            >
              Ingredients
            </Link>
            <Link
              to="/household"
              onClick={() => setMobileMenuOpen(false)}
              className="rounded-lg px-3 py-2.5 text-left text-sm font-medium text-text-secondary transition-colors hover:bg-cream hover:text-text-primary"
            >
              Household & Nutrition
            </Link>
            <button onClick={() => scrollToSection('how-it-works')} className="rounded-lg px-3 py-2.5 text-left text-sm font-medium text-text-secondary transition-colors hover:bg-cream hover:text-text-primary">How It Works</button>
            <button onClick={() => scrollToSection('features')} className="rounded-lg px-3 py-2.5 text-left text-sm font-medium text-text-secondary transition-colors hover:bg-cream hover:text-text-primary">Features</button>
            <div className="my-2 h-px bg-border-light" />
            <SignedOut>
              <Link to="/login" onClick={() => setMobileMenuOpen(false)} className="rounded-lg px-3 py-2.5 text-center text-sm font-medium text-text-secondary transition-colors hover:bg-cream hover:text-text-primary">Login</Link>
              <Link to="/register" onClick={() => setMobileMenuOpen(false)} className="rounded-xl bg-primary-600 px-3 py-2.5 text-center text-sm font-semibold text-white transition-colors hover:bg-primary-700">Sign Up</Link>
            </SignedOut>
            <SignedIn>
              <div className="flex items-center gap-3 px-3 py-2.5">
                <UserButton afterSignOutUrl="/" />
                <span className="text-sm font-medium text-text-secondary">My Account</span>
              </div>
            </SignedIn>
          </div>
        </div>
      )}

    </nav>
  )
}

export default Navbar
