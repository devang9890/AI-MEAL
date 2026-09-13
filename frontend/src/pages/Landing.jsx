import { Link } from 'react-router-dom'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'
import FeatureCard from '../components/FeatureCard'
import HowItWorksStep from '../components/HowItWorksStep'
import MealCard from '../components/MealCard'
import HeroVisual from '../components/HeroVisual'

/* ---- Shared tiny SVG helpers ---- */
const CheckIcon = ({ className = 'h-3.5 w-3.5' }) => (
  <svg className={className} viewBox="0 0 20 20" fill="currentColor">
    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
  </svg>
)

const ArrowRight = () => (
  <svg className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
  </svg>
)

const ArrowDown = () => (
  <svg className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
  </svg>
)

/* ================================================================ */

function Landing() {
  return (
    <div className="min-h-screen bg-surface">
      <Navbar />

      {/* ===== HERO ===== */}
      <section className="overflow-hidden bg-white">
        <div className="mx-auto max-w-7xl px-6 pb-16 pt-12 md:pb-24 md:pt-20 lg:pb-28 lg:pt-24">
          <div className="grid grid-cols-1 items-center gap-12 lg:grid-cols-2 lg:gap-20">
            {/* Left — copy */}
            <div>
              <div className="mb-6 inline-flex items-center gap-2.5 rounded-full border border-primary-200/60 bg-primary-50/50 px-4 py-2">
                <div className="h-1.5 w-1.5 rounded-full bg-primary-500" />
                <span className="text-[11px] font-semibold uppercase tracking-wider text-primary-700">
                  Smart Meal Planning for Every Household
                </span>
              </div>

              <h1 className="text-4xl font-extrabold leading-[1.1] tracking-tight text-text-primary sm:text-5xl lg:text-[3.25rem] xl:text-[3.5rem]">
                Welcome to{' '}
                <span className="text-primary-600">AI Meal Planner</span>
              </h1>

              <p className="mt-6 text-lg leading-relaxed text-text-secondary">
                Plan affordable, nutritious meals for your entire household while staying within your weekly food budget.
              </p>
              <p className="mt-3 text-base text-text-muted">
                Personalized nutrition, smarter budgeting and practical meal planning &mdash; all in one place.
              </p>

              <div className="mt-10 flex flex-col gap-4 sm:flex-row">
                <Link
                  to="/login"
                  className="inline-flex items-center justify-center gap-2.5 rounded-xl bg-primary-600 px-7 py-3.5 text-sm font-semibold text-white shadow-lg shadow-primary-600/20 transition-all hover:bg-primary-700 hover:shadow-xl hover:shadow-primary-600/25 active:scale-[0.98]"
                >
                  Know Your Budget Meal
                  <ArrowRight />
                </Link>
                <Link
                  to="/recipes"
                  className="inline-flex items-center justify-center gap-2.5 rounded-xl border border-primary-300 bg-primary-50/60 px-7 py-3.5 text-sm font-semibold text-primary-700 transition-all hover:bg-primary-100/70 active:scale-[0.98]"
                >
                  Browse 125+ Recipes
                  <ArrowRight />
                </Link>
                <a
                  href="#how-it-works"
                  className="inline-flex items-center justify-center gap-2.5 rounded-xl border border-border-light bg-white px-5 py-3.5 text-sm font-semibold text-text-primary transition-all hover:border-primary-200 hover:bg-primary-50 active:scale-[0.98]"
                >
                  How It Works
                  <ArrowDown />
                </a>
              </div>
            </div>

            {/* Right — product mockup */}
            <div>
              <HeroVisual />
            </div>
          </div>
        </div>
      </section>

      {/* ===== VALUE STRIP ===== */}
      <section className="border-y border-border-light bg-cream/50">
        <div className="mx-auto max-w-7xl px-6 py-8">
          <div className="grid grid-cols-2 gap-6 md:grid-cols-4">
            {[
              {
                label: 'Budget Friendly',
                desc: 'Plans within your budget',
                icon: (
                  <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M12 1v22M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6" />
                  </svg>
                ),
              },
              {
                label: '7-Day Meal Planning',
                desc: 'A full week of meals',
                icon: (
                  <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="3" y="4" width="18" height="18" rx="2" /><path d="M16 2v4M8 2v4M3 10h18" />
                  </svg>
                ),
              },
              {
                label: 'Personalized Nutrition',
                desc: 'Tailored to each member',
                icon: (
                  <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10" /><circle cx="12" cy="12" r="6" /><circle cx="12" cy="12" r="2" />
                  </svg>
                ),
              },
              {
                label: 'Family Focused',
                desc: 'One plan for everyone',
                icon: (
                  <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75" />
                  </svg>
                ),
              },
            ].map((item) => (
              <div key={item.label} className="flex items-center gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary-50 text-primary-600">
                  {item.icon}
                </div>
                <div>
                  <p className="text-sm font-semibold text-text-primary">{item.label}</p>
                  <p className="text-xs text-text-muted">{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ===== WHY AI MEAL PLANNER ===== */}
      <section className="bg-white py-20 md:py-28">
        <div className="mx-auto max-w-7xl px-6">
          <div className="grid grid-cols-1 items-center gap-14 lg:grid-cols-2">
            {/* Left — text & benefits */}
            <div>
              <h2 className="text-3xl font-bold tracking-tight text-text-primary md:text-4xl">
                Meal Planning That Understands Your Household
              </h2>
              <p className="mt-6 text-base leading-relaxed text-text-secondary">
                Different family members have different nutritional needs, preferences and dietary restrictions. At the same time, families often need to manage everything within one weekly food budget.
              </p>
              <p className="mt-4 text-base leading-relaxed text-text-secondary">
                AI Meal Planner brings these requirements together to create practical and affordable meal plans for the entire household.
              </p>
              <div className="mt-8 space-y-4">
                {[
                  'One plan for the whole household',
                  'Personalized nutrition targets',
                  'Budget-conscious meal selection',
                  'Dietary preferences and allergies considered',
                ].map((item) => (
                  <div key={item} className="flex items-center gap-3">
                    <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary-100 text-primary-600">
                      <CheckIcon />
                    </div>
                    <span className="text-sm font-medium text-text-primary">{item}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Right — household nutrition card */}
            <div className="rounded-2xl border border-border-light bg-cream p-5 sm:p-6">
              <h4 className="text-sm font-bold text-text-primary">Household Nutrition Overview</h4>
              <div className="mt-5 space-y-3">
                {[
                  { role: 'Adult (Male)', protein: '60g', cal: '2,200', pct: 85 },
                  { role: 'Adult (Female)', protein: '50g', cal: '1,800', pct: 72 },
                  { role: 'Teenager', protein: '45g', cal: '2,000', pct: 65 },
                  { role: 'Child', protein: '28g', cal: '1,400', pct: 50 },
                ].map((m) => (
                  <div key={m.role} className="rounded-xl bg-white p-3 shadow-sm shadow-black/[0.03]">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2.5">
                        <div className="flex h-7 w-7 items-center justify-center rounded-full bg-primary-50 text-primary-600">
                          <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" /><circle cx="12" cy="7" r="4" />
                          </svg>
                        </div>
                        <span className="text-xs font-semibold text-text-primary">{m.role}</span>
                      </div>
                      <span className="text-[10px] text-text-muted">Protein {m.protein} &middot; {m.cal} cal</span>
                    </div>
                    <div className="mt-2.5 h-1.5 w-full overflow-hidden rounded-full bg-primary-100">
                      <div className="h-full rounded-full bg-primary-500 transition-all" style={{ width: `${m.pct}%` }} />
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-4 flex items-center gap-2 rounded-xl bg-primary-50 p-3">
                <CheckIcon className="h-4 w-4 text-primary-600" />
                <span className="text-xs font-medium text-primary-700">All nutrition targets being considered</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ===== MEAL SHOWCASE ===== */}
      <section className="bg-cream py-20 md:py-28">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mb-14 text-center">
            <h2 className="text-3xl font-bold tracking-tight text-text-primary md:text-4xl">
              Meals Built Around Your Budget
            </h2>
            <p className="mx-auto mt-4 max-w-xl text-base text-text-secondary">
              Preview the kind of affordable, nutritious meals the system can plan for your household.
            </p>
          </div>
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
            <MealCard type="Breakfast" name="Vegetable Poha" price="&#8377;35" protein="8g" calories="250 cal" color="amber" />
            <MealCard type="Lunch" name="Dal Rice + Salad" price="&#8377;55" protein="16g" calories="420 cal" color="emerald" />
            <MealCard type="Dinner" name="Paneer Roti Bowl" price="&#8377;85" protein="28g" calories="550 cal" color="orange" />
            <MealCard type="Snack" name="Sprouts Chaat" price="&#8377;30" protein="10g" calories="180 cal" color="lime" />
          </div>
          <div className="mt-10 flex justify-center">
            <Link
              to="/recipes"
              className="inline-flex items-center gap-2 rounded-xl bg-primary-600 px-7 py-3.5 text-sm font-semibold text-white shadow-md shadow-primary-600/20 transition-all hover:bg-primary-700 hover:shadow-lg active:scale-[0.98]"
            >
              Browse All 125+ Recipes &amp; Nutrition Breakdown
              <ArrowRight />
            </Link>
          </div>

          <p className="mt-6 text-center text-xs text-text-muted">
            Sample meals shown for illustration. Actual plans are generated based on your household profile.
          </p>
        </div>
      </section>

      {/* ===== HOW IT WORKS ===== */}
      <section id="how-it-works" className="bg-white py-20 md:py-28">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mb-14 text-center">
            <h2 className="text-3xl font-bold tracking-tight text-text-primary md:text-4xl">How It Works</h2>
            <p className="mx-auto mt-4 max-w-xl text-base text-text-secondary">
              Four steps from your household profile to a complete weekly meal plan.
            </p>
          </div>
          <div className="grid grid-cols-1 gap-12 sm:grid-cols-2 lg:grid-cols-4">
            <HowItWorksStep
              step={1}
              title="Build Your Household"
              description="Add your family members, dietary preferences and allergies."
              icon={
                <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-4 0h4" />
                </svg>
              }
            />
            <HowItWorksStep
              step={2}
              title="Set Your Budget"
              description="Tell us how much you want to spend on food each week."
              icon={
                <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="2" y="5" width="20" height="14" rx="2" /><path d="M2 10h20" />
                </svg>
              }
            />
            <HowItWorksStep
              step={3}
              title="Get Your Meal Plan"
              description="AI Meal Planner creates a personalized seven-day meal plan balancing nutrition and cost."
              icon={
                <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2" /><rect x="9" y="3" width="6" height="4" rx="1" /><path d="M9 14l2 2 4-4" />
                </svg>
              }
            />
            <HowItWorksStep
              step={4}
              title="Shop &amp; Adjust"
              description="Get your grocery list, swap meals and ask the AI assistant for help."
              icon={
                <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="9" cy="21" r="1" /><circle cx="20" cy="21" r="1" /><path d="M1 1h4l2.68 13.39a2 2 0 002 1.61h9.72a2 2 0 002-1.61L23 6H6" />
                </svg>
              }
            />
          </div>
        </div>
      </section>

      {/* ===== NUTRITION + BUDGET ===== */}
      <section className="bg-cream py-20 md:py-28">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mb-14 text-center">
            <h2 className="text-3xl font-bold tracking-tight text-text-primary md:text-4xl">
              Nutrition Meets Your Budget
            </h2>
            <p className="mx-auto mt-4 max-w-xl text-base text-text-secondary">
              Everything optimized together so your household eats well without overspending.
            </p>
          </div>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
            {[
              {
                label: 'Weekly Budget',
                value: '&#8377;5,000',
                color: 'bg-primary-50 text-primary-600',
                icon: (
                  <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M12 1v22M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6" />
                  </svg>
                ),
              },
              {
                label: 'Nutrition',
                value: 'Balanced',
                color: 'bg-emerald-50 text-emerald-600',
                icon: <CheckIcon className="h-5 w-5" />,
              },
              {
                label: 'Protein',
                value: 'On Target',
                color: 'bg-amber-50 text-amber-600',
                icon: (
                  <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M12 20V10M18 20V4M6 20v-4" />
                  </svg>
                ),
              },
              {
                label: 'Meals',
                value: '7 Days',
                color: 'bg-sky-50 text-sky-600',
                icon: (
                  <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="3" y="4" width="18" height="18" rx="2" /><path d="M16 2v4M8 2v4M3 10h18" />
                  </svg>
                ),
              },
              {
                label: 'Groceries',
                value: 'Optimized',
                color: 'bg-violet-50 text-violet-600',
                icon: (
                  <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" />
                  </svg>
                ),
              },
            ].map((stat) => (
              <div key={stat.label} className="rounded-2xl border border-border-light bg-white p-5 text-center transition-shadow duration-300 hover:shadow-md hover:shadow-black/[0.04]">
                <div className={`mx-auto mb-3 flex h-11 w-11 items-center justify-center rounded-xl ${stat.color}`}>
                  {stat.icon}
                </div>
                <p className="text-xs font-medium text-text-muted">{stat.label}</p>
                <p className="mt-1 text-lg font-bold text-text-primary" dangerouslySetInnerHTML={{ __html: stat.value }} />
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ===== FEATURES ===== */}
      <section id="features" className="bg-white py-20 md:py-28">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mb-14 text-center">
            <h2 className="text-3xl font-bold tracking-tight text-text-primary md:text-4xl">
              Everything You Need to Plan Better Meals
            </h2>
          </div>
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            <FeatureCard
              accent="primary"
              title="Household Planning"
              description="Plan meals for the entire family instead of creating separate plans for everyone."
              icon={
                <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75" />
                </svg>
              }
            />
            <FeatureCard
              accent="amber"
              title="Budget Optimization"
              description="Stay within your weekly food budget while maximizing nutritional value."
              icon={
                <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 1v22M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6" />
                </svg>
              }
            />
            <FeatureCard
              accent="emerald"
              title="Personalized Nutrition"
              description="Different members can have different nutrition targets based on their needs."
              icon={
                <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10" /><circle cx="12" cy="12" r="6" /><circle cx="12" cy="12" r="2" />
                </svg>
              }
            />
            <FeatureCard
              accent="orange"
              title="Smart Grocery List"
              description="Get a consolidated shopping list generated from your weekly meal plan."
              icon={
                <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" />
                </svg>
              }
            />
            <FeatureCard
              accent="sky"
              title="Meal Swaps"
              description="Change meals while keeping the overall plan balanced and within budget."
              icon={
                <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M7 16V4m0 0L3 8m4-4l4 4M17 8v12m0 0l4-4m-4 4l-4-4" />
                </svg>
              }
            />
            <FeatureCard
              accent="violet"
              title="AI Assistant"
              description="Ask questions and adjust your plan naturally through conversation."
              icon={
                <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
                </svg>
              }
            />
          </div>
          {/* Disclaimer */}
          <p className="mt-10 text-center text-xs text-text-muted">
            AI Meal Planner is a meal planning and decision-support tool. It does not provide medical or clinical dietary advice.
          </p>
        </div>
      </section>

      {/* ===== FREE CTA ===== */}
      <section className="bg-cream py-20 md:py-28">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mx-auto max-w-2xl rounded-3xl border border-primary-200/30 bg-gradient-to-br from-primary-50 to-primary-100/50 p-10 text-center md:p-14">
            <h2 className="text-2xl font-bold text-text-primary md:text-3xl">
              Better Meal Planning Shouldn&rsquo;t Cost More
            </h2>
            <p className="mt-4 text-base leading-relaxed text-text-secondary">
              AI Meal Planner is designed as a free platform to help households plan affordable, nutritious meals and make better use of their weekly food budget.
            </p>
            <Link
              to="/login"
              className="mt-8 inline-flex items-center gap-2.5 rounded-xl bg-primary-600 px-8 py-3.5 text-sm font-semibold text-white shadow-lg shadow-primary-600/20 transition-all hover:bg-primary-700 hover:shadow-xl hover:shadow-primary-600/25 active:scale-[0.98]"
            >
              Start Planning for Free
              <ArrowRight />
            </Link>
          </div>
        </div>
      </section>

      {/* ===== FINAL CTA ===== */}
      <section className="bg-neutral-900 py-20 md:py-28">
        <div className="mx-auto max-w-7xl px-6 text-center">
          <h2 className="text-3xl font-bold text-white md:text-4xl">
            Your Week of Meals Starts Here.
          </h2>
          <p className="mx-auto mt-4 max-w-lg text-base leading-relaxed text-stone-400">
            Set your budget. Tell us about your household. We&rsquo;ll help you plan the rest.
          </p>
          <Link
            to="/login"
            className="mt-10 inline-flex items-center gap-2.5 rounded-xl bg-primary-500 px-8 py-4 text-sm font-semibold text-white shadow-lg transition-all hover:bg-primary-400 active:scale-[0.98]"
          >
            Know Your Budget Meal
            <ArrowRight />
          </Link>
        </div>
      </section>

      <Footer />
    </div>
  )
}

export default Landing
