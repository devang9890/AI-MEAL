import React, { useState, useCallback } from 'react'
import ChatWindow from './ChatWindow'

const API_BASE = 'http://localhost:8000/api'

const INITIAL_WELCOME_MESSAGE = {
  role: 'assistant',
  content: "Hi! I'm your AI Meal Planner assistant. I can help you understand your household nutrition targets, meals, recipes, ingredients, and budget planning.\n\nWhat would you like to know?",
  timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

export default function ChatWidget({ getToken, householdId }) {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState([INITIAL_WELCOME_MESSAGE])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const toggleOpen = () => {
    setIsOpen((prev) => !prev)
    setError(null)
  }

  const handleSendMessage = useCallback(async (text) => {
    const trimmed = text.trim()
    if (!trimmed || loading) return

    const nowTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    const userMessage = {
      role: 'user',
      content: trimmed,
      timestamp: nowTime
    }

    // Append user message immediately
    const updatedMessages = [...messages, userMessage]
    setMessages(updatedMessages)
    setLoading(true)
    setError(null)

    try {
      // Build conversation payload for backend (only role and content)
      const conversationPayload = updatedMessages
        .slice(0, -1) // exclude the message just added
        .map((m) => ({
          role: m.role,
          content: m.content
        }))

      // Prepare headers with Clerk token if available
      const headers = {
        'Content-Type': 'application/json'
      }

      if (getToken) {
        try {
          const token = await getToken()
          if (token) {
            headers['Authorization'] = `Bearer ${token}`
          }
        } catch (tokenErr) {
          console.warn('Could not acquire Clerk token for chat:', tokenErr)
        }
      }

      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          message: trimmed,
          conversation: conversationPayload,
          household_id: householdId || null
        })
      })

      if (!response.ok) {
        throw new Error('Chat service network error')
      }

      const data = await response.json()

      const aiReplyTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

      if (data.success && data.reply) {
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: data.reply,
            timestamp: aiReplyTime
          }
        ])
      } else {
        // Friendly fallback
        const friendlyFallback = data.reply || "Sorry, I couldn't process that right now. Please try again."
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: friendlyFallback,
            timestamp: aiReplyTime
          }
        ])
        if (data.error) {
          setError(data.error === 'GROQ_API_KEY_NOT_CONFIGURED'
            ? 'Note: Add GROQ_API_KEY in backend/.env for live LLM responses.'
            : 'Temporary AI processing issue.'
          )
        }
      }
    } catch (err) {
      console.error('Chat error:', err)
      const aiReplyTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: "Sorry, I couldn't process that right now. Please try again.",
          timestamp: aiReplyTime
        }
      ])
      setError('Connection issue. Please try again in a moment.')
    } finally {
      setLoading(false)
    }
  }, [messages, loading, getToken, householdId])

  return (
    <>
      {/* Floating Chat Panel */}
      <ChatWindow
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        messages={messages}
        onSendMessage={handleSendMessage}
        loading={loading}
        error={error}
      />

      {/* Floating Action Button */}
      <div className="fixed bottom-6 right-6 z-50 select-none">
        <button
          type="button"
          onClick={toggleOpen}
          aria-label={isOpen ? 'Close AI nutrition assistant' : 'Open AI nutrition assistant'}
          className={`group flex items-center gap-2.5 rounded-full px-4 py-3 sm:px-5 sm:py-3.5 shadow-xl transition-all duration-300 transform active:scale-95 focus:outline-none focus:ring-4 focus:ring-primary-500/25 ${
            isOpen
              ? 'bg-white text-text-primary border border-border hover:bg-cream'
              : 'bg-primary-600 text-white hover:bg-primary-700 hover:shadow-2xl hover:scale-105'
          }`}
        >
          {isOpen ? (
            <>
              <svg className="h-5 w-5 text-text-secondary group-hover:rotate-90 transition-transform duration-200" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
              <span className="text-xs font-bold tracking-wide">Close</span>
            </>
          ) : (
            <>
              {/* AI sparkle/bot icon */}
              <div className="relative">
                <svg className="h-5 w-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2a2 2 0 0 1 2 2v2a2 2 0 0 1-2 2 2 2 0 0 1-2-2V4a2 2 0 0 1 2-2z" />
                  <rect x="4" y="8" width="16" height="12" rx="4" />
                  <path d="M9 13h.01" />
                  <path d="M15 13h.01" />
                  <path d="M10 17h4" />
                </svg>
                {/* Active indicator dot */}
                <span className="absolute -top-0.5 -right-0.5 flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary-200 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-primary-300"></span>
                </span>
              </div>
              <span className="text-xs font-bold tracking-wide">
                AI Assistant
              </span>
            </>
          )}
        </button>
      </div>
    </>
  )
}
