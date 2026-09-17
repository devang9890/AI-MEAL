import React, { useRef, useEffect, useState } from 'react'
import ChatMessage from './ChatMessage'
import QuickQuestions from './QuickQuestions'

export default function ChatWindow({
  isOpen,
  onClose,
  messages,
  onSendMessage,
  loading,
  error
}) {
  const [inputText, setInputText] = useState('')
  const [showQuickQuestions, setShowQuickQuestions] = useState(true)
  const messagesContainerRef = useRef(null)
  const messagesEndRef = useRef(null)
  const textareaRef = useRef(null)

  // Auto-scroll to bottom of messages container
  const scrollToBottom = (behavior = 'smooth') => {
    messagesEndRef.current?.scrollIntoView({ behavior })
  }

  useEffect(() => {
    if (isOpen) {
      if (messages.length <= 1) {
        if (messagesContainerRef.current) {
          messagesContainerRef.current.scrollTop = 0
        }
      } else {
        scrollToBottom('smooth')
      }
      // Focus input on desktop
      if (window.innerWidth > 640) {
        setTimeout(() => textareaRef.current?.focus(), 150)
      }
    }
  }, [isOpen, messages, loading])

  if (!isOpen) return null

  const handleSend = () => {
    const trimmed = inputText.trim()
    if (!trimmed || loading) return
    onSendMessage(trimmed)
    setInputText('')
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div
      role="dialog"
      aria-label="AI Meal Planner Chatbot"
      className="fixed bottom-24 right-4 sm:right-6 z-50 flex flex-col w-[calc(100vw-2rem)] sm:w-[410px] h-[560px] max-h-[82vh] bg-surface rounded-3xl border border-border-light shadow-2xl overflow-hidden animate-in fade-in slide-in-from-bottom-5 duration-200"
    >
      {/* HEADER */}
      <div className="flex items-center justify-between px-5 py-4 bg-white border-b border-border-light select-none">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary-600 text-white shadow-xs">
            <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2a2 2 0 0 1 2 2v2a2 2 0 0 1-2 2 2 2 0 0 1-2-2V4a2 2 0 0 1 2-2z" />
              <rect x="4" y="8" width="16" height="12" rx="4" />
              <path d="M9 13h.01" />
              <path d="M15 13h.01" />
              <path d="M10 17h4" />
            </svg>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-text-primary tracking-tight">
                AI Meal Planner
              </h3>
              <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[10px] font-semibold bg-primary-50 text-primary-700 border border-primary-100">
                <span className="h-1.5 w-1.5 rounded-full bg-primary-500 animate-pulse" />
                Online
              </span>
            </div>
            <p className="text-xs text-text-secondary">
              Your personal nutrition assistant
            </p>
          </div>
        </div>

        {/* Close Button */}
        <button
          type="button"
          onClick={onClose}
          aria-label="Close chat"
          className="rounded-xl p-1.5 text-text-muted hover:bg-cream hover:text-text-primary transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500/20"
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* CHAT MESSAGES AREA */}
      <div ref={messagesContainerRef} className="flex-1 overflow-y-auto px-4 py-3 space-y-1">
        {messages.map((msg, index) => (
          <ChatMessage key={index} message={msg} />
        ))}

        {/* Loading / Typing Indicator */}
        {loading && (
          <div className="flex items-center gap-2.5 my-3 pl-1 text-xs text-text-muted">
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-xl bg-primary-50 border border-primary-100 text-primary-700">
              <svg className="h-3.5 w-3.5 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            </div>
            <div className="inline-flex items-center gap-1.5 bg-white border border-border-light rounded-2xl px-3.5 py-2 text-text-secondary text-xs shadow-2xs">
              <span className="h-1.5 w-1.5 rounded-full bg-primary-600 animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="h-1.5 w-1.5 rounded-full bg-primary-600 animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="h-1.5 w-1.5 rounded-full bg-primary-600 animate-bounce" style={{ animationDelay: '300ms' }} />
              <span className="ml-1 text-text-secondary font-medium">AI is thinking...</span>
            </div>
          </div>
        )}

        {/* Error Banner if any */}
        {error && (
          <div className="my-2 rounded-xl bg-red-50 border border-red-200 p-2.5 text-xs text-red-700 flex items-center gap-2">
            <svg className="h-4 w-4 shrink-0 text-red-500" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            <span>{error}</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* QUICK QUESTIONS ACCORDION / CONTAINER */}
      <div className="shrink-0">
        <div className="flex items-center justify-between px-3 pt-1 text-[11px] bg-cream/40 border-t border-border-light/60">
          <button
            type="button"
            onClick={() => setShowQuickQuestions((prev) => !prev)}
            className="flex items-center gap-1 font-semibold text-text-secondary hover:text-primary-700 py-1 transition-colors"
          >
            <span>{showQuickQuestions ? 'Hide Suggestions' : 'Show Suggestions'}</span>
            <svg
              className={`h-3.5 w-3.5 transition-transform ${showQuickQuestions ? 'rotate-180' : ''}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        </div>

        {showQuickQuestions && (
          <QuickQuestions
            onSelectQuestion={(q) => {
              onSendMessage(q)
            }}
            disabled={loading}
          />
        )}
      </div>

      {/* INPUT CONTAINER */}
      <div className="p-3 bg-white border-t border-border-light shrink-0">
        <div className="flex items-center gap-2 rounded-2xl border border-border-light bg-surface px-3 py-1.5 focus-within:border-primary-500 focus-within:ring-2 focus-within:ring-primary-500/20 transition-all shadow-inner">
          <textarea
            ref={textareaRef}
            rows="1"
            value={inputText}
            onChange={(e) => setInputText(e.target.value.slice(0, 2000))}
            onKeyDown={handleKeyDown}
            placeholder="Ask about your meals, nutrition or budget..."
            disabled={loading}
            aria-label="Ask about your meals, nutrition or budget"
            className="flex-1 max-h-24 resize-none bg-transparent py-1.5 text-xs text-text-primary placeholder:text-text-muted focus:outline-none leading-relaxed"
          />

          <button
            type="button"
            onClick={handleSend}
            disabled={!inputText.trim() || loading}
            aria-label="Send message"
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-primary-600 text-white shadow-xs hover:bg-primary-700 disabled:opacity-40 disabled:cursor-not-allowed transition-all focus:outline-none focus:ring-2 focus:ring-primary-500/30"
          >
            <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          </button>
        </div>
        <div className="flex items-center justify-between mt-1 px-1 text-[10px] text-text-muted">
          <span>Press Enter to send, Shift+Enter for new line</span>
          {inputText.length > 1500 && (
            <span>{inputText.length}/2000</span>
          )}
        </div>
      </div>
    </div>
  )
}
