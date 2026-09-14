import { useState } from 'react'

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
const MEAL_TYPES = ['Breakfast', 'Lunch', 'Dinner']

export default function MealPlanGrid({ meals = [], onSwapClick }) {
  const [expandedExplanationId, setExpandedExplanationId] = useState(null)

  // Index meals by day and meal_type
  const mealMap = {}
  meals.forEach((m) => {
    const key = `${m.day?.toLowerCase()}_${m.meal_type?.toLowerCase()}`
    mealMap[key] = m
  })

  const toggleExplanation = (id) => {
    setExpandedExplanationId((prev) => (prev === id ? null : id))
  }

  const getMealTypeColor = (type) => {
    switch (type.toLowerCase()) {
      case 'breakfast':
        return 'text-amber-700 bg-amber-50 border-amber-200'
      case 'lunch':
        return 'text-emerald-700 bg-emerald-50 border-emerald-200'
      case 'dinner':
        return 'text-indigo-700 bg-indigo-50 border-indigo-200'
      default:
        return 'text-gray-700 bg-gray-50 border-gray-200'
    }
  }

  return (
    <div className="w-full overflow-x-auto pb-4">
      <div className="min-w-[1020px]">
        {/* Days Header */}
        <div className="grid grid-cols-7 gap-3 mb-3">
          {DAYS.map((day) => (
            <div
              key={day}
              className="text-center py-2.5 px-2 bg-cream rounded-xl border border-border-light shadow-xs"
            >
              <span className="text-sm font-bold text-text-primary">{day}</span>
            </div>
          ))}
        </div>

        {/* Meal rows */}
        <div className="space-y-4">
          {MEAL_TYPES.map((mtype) => (
            <div key={mtype} className="space-y-2">
              <div className="flex items-center gap-2 px-1">
                <span className="text-xs font-bold uppercase tracking-wider text-text-muted">
                  {mtype}
                </span>
                <div className="h-px flex-1 bg-border-light/80" />
              </div>

              <div className="grid grid-cols-7 gap-3">
                {DAYS.map((day) => {
                  const key = `${day.toLowerCase()}_${mtype.toLowerCase()}`
                  const meal = mealMap[key]

                  if (!meal) {
                    return (
                      <div
                        key={day}
                        className="rounded-2xl border border-dashed border-border-light bg-surface/50 p-4 text-center flex flex-col items-center justify-center min-h-[160px]"
                      >
                        <span className="text-xs text-text-muted">No meal scheduled</span>
                      </div>
                    )
                  }

                  const isExpanded = expandedExplanationId === meal.id

                  return (
                    <div
                      key={day}
                      className="group relative rounded-2xl border border-border-light/80 bg-white p-3.5 shadow-sm hover:shadow-md hover:border-primary-300 transition-all flex flex-col justify-between min-h-[190px]"
                    >
                      {/* Top Row: Type badge + Cost */}
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span
                            className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${getMealTypeColor(
                              mtype
                            )}`}
                          >
                            {mtype}
                          </span>
                          {meal.cost !== undefined && meal.cost !== null && (
                            <span className="text-xs font-bold text-text-primary">
                              ₹{Math.round(meal.cost)}
                            </span>
                          )}
                        </div>

                        {/* Recipe Title */}
                        <h4 className="text-sm font-bold text-text-primary leading-tight line-clamp-2 mb-1.5 group-hover:text-primary-700 transition-colors">
                          {meal.recipe_name}
                        </h4>

                        {/* Macros Pill Strip */}
                        {(meal.calories || meal.protein) && (
                          <div className="flex items-center gap-1.5 text-[11px] text-text-secondary mb-2 flex-wrap">
                            {meal.calories && (
                              <span className="bg-cream px-1.5 py-0.5 rounded text-amber-800 font-medium">
                                {Math.round(meal.calories)} kcal
                              </span>
                            )}
                            {meal.protein && (
                              <span className="bg-cream px-1.5 py-0.5 rounded text-emerald-800 font-medium">
                                {Math.round(meal.protein)}g P
                              </span>
                            )}
                          </div>
                        )}

                        {/* Dietary Tags */}
                        {meal.dietary_tags && meal.dietary_tags.length > 0 && (
                          <div className="flex flex-wrap gap-1 mb-2">
                            {meal.dietary_tags.slice(0, 2).map((t, idx) => (
                              <span
                                key={idx}
                                className="text-[10px] px-1.5 py-0.2 rounded-md bg-surface border border-border-light text-text-muted capitalize"
                              >
                                {t.replace('_', ' ')}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>

                      {/* Bottom row: Why this meal + Swap button */}
                      <div className="pt-2 border-t border-border-light/60 mt-1">
                        <div className="flex items-center justify-between gap-1">
                          {meal.explanation ? (
                            <button
                              type="button"
                              onClick={() => toggleExplanation(meal.id)}
                              className="text-[11px] text-primary-600 hover:text-primary-800 font-medium flex items-center gap-1 transition-colors"
                              title="Why was this recipe selected?"
                            >
                              <span>💡 Why?</span>
                            </button>
                          ) : (
                            <div />
                          )}

                          <button
                            type="button"
                            onClick={() => onSwapClick(meal)}
                            className="text-[11px] px-2 py-1 rounded-lg text-text-secondary hover:text-primary-700 hover:bg-primary-50 transition-colors flex items-center gap-1 font-medium"
                            title="Swap with another recipe"
                          >
                            <span>🔄 Swap</span>
                          </button>
                        </div>

                        {/* Expanded explanation popover */}
                        {isExpanded && meal.explanation && (
                          <div className="mt-2 text-[11px] text-text-secondary bg-primary-50/60 p-2.5 rounded-xl border border-primary-100 animate-fadeIn">
                            <p className="leading-relaxed">{meal.explanation}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
