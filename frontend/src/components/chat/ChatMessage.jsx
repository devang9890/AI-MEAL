import React from 'react'

/**
 * Renders an individual chat message (User or AI Assistant).
 * Supports simple markdown formatting: bold (**text**), bullet lines (- item), and paragraphs.
 */
export default function ChatMessage({ message }) {
  const isUser = message.role === 'user'

  // Format AI text nicely (bullet points, bolding, paragraphs) without external heavy deps
  const renderFormattedText = (text) => {
    if (!text) return null
    const lines = text.split('\n')

    return lines.map((line, lineIdx) => {
      const trimmed = line.trim()

      if (!trimmed) {
        return <div key={lineIdx} className="h-2" />
      }

      // Check for bullet line
      if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
        const itemText = trimmed.slice(2)
        return (
          <div key={lineIdx} className="flex items-start gap-2 my-0.5 pl-1">
            <span className="text-primary-600 mt-1 font-bold text-xs leading-none">•</span>
            <span className="flex-1">{formatInline(itemText)}</span>
          </div>
        )
      }

      // Check for numbered list (e.g. "1. ")
      const numMatch = trimmed.match(/^(\d+)\.\s+(.*)/)
      if (numMatch) {
        return (
          <div key={lineIdx} className="flex items-start gap-2 my-0.5 pl-1">
            <span className="text-primary-700 font-semibold text-xs min-w-4">{numMatch[1]}.</span>
            <span className="flex-1">{formatInline(numMatch[2])}</span>
          </div>
        )
      }

      return (
        <p key={lineIdx} className="my-1 leading-relaxed">
          {formatInline(trimmed)}
        </p>
      )
    })
  }

  // Parses **bold** segments
  const formatInline = (text) => {
    const parts = text.split(/(\*\*.*?\*\*)/g)
    return parts.map((part, idx) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={idx} className="font-semibold text-text-primary">{part.slice(2, -2)}</strong>
      }
      return part
    })
  }

  return (
    <div
      className={`flex w-full my-2.5 transition-all ${
        isUser ? 'justify-end' : 'justify-start'
      }`}
    >
      <div className={`flex max-w-[88%] sm:max-w-[84%] gap-2.5 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        {/* Avatar indicator */}
        {!isUser && (
          <div
            className="flex h-7 w-7 shrink-0 items-center justify-center rounded-xl bg-primary-50 border border-primary-100 text-primary-700 shadow-2xs mt-0.5"
            aria-hidden="true"
          >
            <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2a2 2 0 0 1 2 2v2a2 2 0 0 1-2 2 2 2 0 0 1-2-2V4a2 2 0 0 1 2-2z" />
              <rect x="4" y="8" width="16" height="12" rx="4" />
              <path d="M9 13h.01" />
              <path d="M15 13h.01" />
              <path d="M10 17h4" />
            </svg>
          </div>
        )}

        {/* Message Bubble */}
        <div
          className={`rounded-2xl px-4 py-3 text-sm transition-shadow ${
            isUser
              ? 'bg-primary-600 text-white rounded-tr-xs shadow-sm shadow-primary-600/10'
              : 'bg-white border border-border-light text-text-secondary rounded-tl-xs shadow-2xs'
          }`}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap break-words leading-relaxed text-white">
              {message.content}
            </p>
          ) : (
            <div className="text-text-secondary text-[13.5px] break-words">
              {renderFormattedText(message.content)}
            </div>
          )}

          {/* Time display if available */}
          {message.timestamp && (
            <span
              className={`block mt-1.5 text-[10px] select-none ${
                isUser ? 'text-primary-100 text-right' : 'text-text-muted text-left'
              }`}
            >
              {message.timestamp}
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
