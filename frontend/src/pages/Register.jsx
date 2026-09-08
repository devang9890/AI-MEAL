import { Link } from 'react-router-dom'
import { SignUp } from '@clerk/clerk-react'

function Register() {
  return (
    <div className="flex min-h-screen bg-surface">
      {/* Left decorative panel — hidden on mobile */}
      <div className="hidden w-1/2 bg-gradient-to-br from-primary-600 via-primary-700 to-primary-800 lg:flex lg:flex-col lg:items-center lg:justify-center lg:p-12">
        <div className="max-w-md text-center">
          <div className="mb-8 inline-flex items-center justify-center rounded-2xl bg-white/10 p-5 backdrop-blur-sm">
            <span className="text-5xl">🍽</span>
          </div>
          <h2 className="mb-4 text-3xl font-bold text-white">AI Meal Planner</h2>
          <p className="text-lg leading-relaxed text-primary-100">
            Join thousands of families who plan smarter, eat better, and save more every week.
          </p>
          <div className="mt-10 space-y-4">
            {[
              { icon: '✅', text: 'Personalized nutrition for every family member' },
              { icon: '✅', text: 'Meals that fit your weekly food budget' },
              { icon: '✅', text: 'Smart grocery lists & meal swaps' },
              { icon: '✅', text: 'Completely free to use' },
            ].map(({ icon, text }) => (
              <div key={text} className="flex items-center gap-3 rounded-xl bg-white/10 px-5 py-3 backdrop-blur-sm">
                <span className="text-lg">{icon}</span>
                <span className="text-sm text-primary-50">{text}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right panel — Clerk SignUp */}
      <div className="flex w-full flex-col items-center justify-center px-5 py-12 lg:w-1/2">
        <div className="w-full max-w-md">
          {/* Back to home */}
          <Link
            to="/"
            className="mb-8 inline-flex items-center gap-1.5 text-sm text-text-muted transition-colors hover:text-primary-600"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Back to Home
          </Link>

          {/* Mobile logo */}
          <div className="mb-6 flex items-center gap-2.5 lg:hidden">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary-600 text-sm text-white">
              🍽
            </span>
            <span className="text-lg font-bold text-text-primary">AI Meal Planner</span>
          </div>

          {/* Clerk SignUp component — handles all registration flows */}
          <SignUp
            routing="hash"
            signInUrl="/login"
            appearance={{
              elements: {
                card: 'shadow-none border border-border-light rounded-2xl',
                headerTitle: 'text-2xl font-bold text-text-primary',
                headerSubtitle: 'text-sm text-text-secondary',
                formButtonPrimary:
                  'bg-primary-600 hover:bg-primary-700 text-sm font-semibold rounded-xl',
                footerActionLink: 'text-primary-600 hover:text-primary-700 font-semibold',
              },
            }}
          />
        </div>
      </div>
    </div>
  )
}

export default Register
