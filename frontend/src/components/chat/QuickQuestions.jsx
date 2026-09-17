import React from 'react'

export const QUICK_QUESTIONS = [
  "How many calories does my household need per day?",
  "How much protein do we need every day?",
  "What does my nutrition target mean?",
  "How can I plan healthy meals on a low budget?",
  "Which recipes are high in protein?",
  "What ingredients can I use for affordable meals?"
]

export default function QuickQuestions({ onSelectQuestion, disabled = false }) {
  return (
    <div className="py-2.5 px-3 border-t border-border-light/70 bg-cream/40">
      <div className="flex items-center justify-between mb-2">
        <span className="text-[11px] font-bold uppercase tracking-wider text-text-muted">
          Suggested Questions
        </span>
        <span className="text-[10px] text-text-muted">Click to ask</span>
      </div>
      <div className="flex flex-wrap gap-1.5 max-h-36 overflow-y-auto pr-1">
        {QUICK_QUESTIONS.map((question, index) => (
          <button
            key={index}
            type="button"
            onClick={() => onSelectQuestion(question)}
            disabled={disabled}
            className="text-left text-xs text-text-secondary bg-white hover:bg-primary-50 hover:text-primary-700 hover:border-primary-200 border border-border-light rounded-xl px-2.5 py-1.5 transition-all shadow-2xs disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-primary-500/20"
          >
            {question}
          </button>
        ))}
      </div>
    </div>
  )
}
