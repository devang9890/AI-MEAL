/* The profile selector deliberately resets local selection when its member changes. */
/* eslint-disable react-hooks/set-state-in-effect */
import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth, SignedIn, SignedOut } from '@clerk/clerk-react'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'
import {
  useMemberDraft,
  readMemberDraft,
  MEMBER_DRAFT_FLOW,
} from '../context/MemberDraftContext'

const API_BASE = 'http://localhost:8000/api'

export default function HealthSelection({ type }) {
  const isAllergies = type === 'allergies'
  const field = isAllergies ? 'allergies' : 'diseases'
  const title = isAllergies ? 'Food allergies & intolerances' : 'Health conditions'
  const { isSignedIn, getToken } = useAuth()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { patchField, refreshFromStorage } = useMemberDraft()

  const draftFromStorage = readMemberDraft()
  const draftMode =
    draftFromStorage?.flow === MEMBER_DRAFT_FLOW ||
    searchParams.get('flow') === 'member-draft'

  const [catalog, setCatalog] = useState([])
  const [households, setHouseholds] = useState([])
  const [householdId, setHouseholdId] = useState('')
  const [members, setMembers] = useState([])
  const [memberId, setMemberId] = useState('')
  const [selected, setSelected] = useState(new Set())
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('all')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    fetch(`${API_BASE}/health/${type}`)
      .then((res) => (res.ok ? res.json() : Promise.reject(new Error('Unable to load the catalog.'))))
      .then(setCatalog)
      .catch((err) => setError(err.message))
  }, [type])

  useEffect(() => {
    if (!isSignedIn || draftMode) {
      if (draftMode) setLoading(false)
      return
    }
    const loadHouseholds = async () => {
      try {
        setLoading(true)
        const token = await getToken()
        const res = await fetch(`${API_BASE}/households`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        if (!res.ok) throw new Error('Unable to load your households.')
        const data = await res.json()
        setHouseholds(data)
        setHouseholdId(data[0]?.id ? String(data[0].id) : '')
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }
    loadHouseholds()
  }, [isSignedIn, getToken, draftMode])

  const loadMembers = useCallback(async () => {
    if (!householdId) {
      setMembers([])
      return
    }
    try {
      const token = await getToken()
      const res = await fetch(`${API_BASE}/households/${householdId}/members`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('Unable to load family members.')
      const data = await res.json()
      setMembers(data)
      setMemberId(data[0]?.id ? String(data[0].id) : '')
    } catch (err) {
      setError(err.message)
    }
  }, [householdId, getToken])

  useEffect(() => {
    if (isSignedIn && !draftMode) loadMembers()
  }, [isSignedIn, loadMembers, draftMode])

  useEffect(() => {
    const latestDraft = readMemberDraft()
    const member = members.find((item) => String(item.id) === memberId)
    const sourceValue = draftMode ? latestDraft?.[field] : member?.[field]
    const names = (sourceValue || '')
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean)
    setSelected(new Set(names))
    setSaved(false)
  }, [memberId, members, field, draftMode])

  const categories = useMemo(
    () => ['all', ...new Set(catalog.map((item) => item.category))],
    [catalog]
  )
  const visible = useMemo(
    () =>
      catalog.filter((item) => {
        const matchesCategory = category === 'all' || item.category === category
        const query = search.trim().toLowerCase()
        return (
          matchesCategory &&
          (!query ||
            item.name.toLowerCase().includes(query) ||
            item.category.toLowerCase().includes(query))
        )
      }),
    [catalog, category, search]
  )

  const toggle = (name) =>
    setSelected((current) => {
      const next = new Set(current)
      next.has(name) ? next.delete(name) : next.add(name)
      return next
    })

  const save = async () => {
    const value = [...selected].sort().join(', ')

    // Draft mode: only patch the allergies/diseases field in client draft.
    // Never create or update a member in the database here.
    if (draftMode) {
      const latest = refreshFromStorage() || readMemberDraft()
      if (!latest) {
        setError('Your member form draft expired. Go back and re-open Add/Edit Member.')
        return
      }
      patchField(field, value)
      navigate('/household?resumeMemberDraft=1')
      return
    }

    if (!memberId) return
    try {
      setSaving(true)
      setError('')
      setSaved(false)
      const token = await getToken()
      const res = await fetch(
        `${API_BASE}/households/${householdId}/members/${memberId}`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ [field]: value || null }),
        }
      )
      if (!res.ok) {
        throw new Error(
          (await res.json().catch(() => ({}))).detail ||
            'Unable to save your selections.'
        )
      }
      const updated = await res.json()
      setMembers((current) =>
        current.map((member) => (member.id === updated.id ? updated : member))
      )
      setSaved(true)
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  const draft = readMemberDraft()

  return (
    <div className="min-h-screen bg-surface flex flex-col">
      <Navbar />
      <main className="mx-auto w-full max-w-7xl flex-1 px-6 py-10">
        <SignedOut>
          <div className="mx-auto max-w-xl rounded-3xl border border-border-light bg-white p-10 text-center">
            <h1 className="text-2xl font-bold">Sign in to manage health preferences</h1>
            <Link
              to="/login"
              className="mt-6 inline-flex rounded-xl bg-primary-600 px-5 py-3 text-sm font-semibold text-white"
            >
              Sign In
            </Link>
          </div>
        </SignedOut>
        <SignedIn>
          <div className="mb-7">
            <Link
              to={draftMode ? '/household?resumeMemberDraft=1' : '/household'}
              className="text-sm font-semibold text-primary-700"
            >
              ← Back to {draftMode ? 'member form' : 'Household'}
            </Link>
            <h1 className="mt-3 text-3xl font-extrabold text-text-primary">{title}</h1>
            <p className="mt-2 max-w-3xl text-sm leading-relaxed text-text-secondary">
              Choose items for one family member.{' '}
              {isAllergies
                ? 'Allergies, intolerances, and sensitivities are labelled separately. Confirmed allergies are excluded using actual recipe ingredients.'
                : 'Selections guide conservative recipe filters, with clear cautions where a clinician or dietitian must individualize advice.'}
            </p>
          </div>

          {draftMode ? (
            <div className="mb-6 rounded-2xl border border-primary-200 bg-primary-50 p-5 text-sm text-primary-950">
              Selecting for <strong>{draft?.name || 'new family member'}</strong>. Your
              unsaved member details will be restored after you save these selections.
              Nothing is written to the database until you click Save Member.
            </div>
          ) : (
            <div className="mb-6 grid gap-4 rounded-2xl border border-border-light bg-white p-5 md:grid-cols-2">
              <label className="text-xs font-bold uppercase tracking-wider text-text-secondary">
                Household
                <select
                  value={householdId}
                  onChange={(e) => setHouseholdId(e.target.value)}
                  className="mt-2 w-full rounded-xl border border-border-light bg-surface px-3 py-2.5 text-sm normal-case font-medium text-text-primary"
                >
                  {households.map((h) => (
                    <option key={h.id} value={h.id}>
                      {h.name}
                    </option>
                  ))}
                </select>
              </label>
              <label className="text-xs font-bold uppercase tracking-wider text-text-secondary">
                Family member
                <select
                  value={memberId}
                  onChange={(e) => setMemberId(e.target.value)}
                  className="mt-2 w-full rounded-xl border border-border-light bg-surface px-3 py-2.5 text-sm normal-case font-medium text-text-primary"
                >
                  {members.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.name}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          )}

          {error && (
            <div className="mb-5 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
              {error}
            </div>
          )}
          {saved && (
            <div className="mb-5 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm font-medium text-emerald-800">
              Saved for this family member. Future meal plans will use these selections.
            </div>
          )}

          <div className="rounded-2xl border border-border-light bg-white p-5">
            <div className="flex flex-col gap-3 md:flex-row">
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder={`Search ${isAllergies ? 'allergies, intolerances, or sensitivities' : 'conditions'}`}
                className="flex-1 rounded-xl border border-border-light bg-surface px-4 py-2.5 text-sm"
              />
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="rounded-xl border border-border-light bg-surface px-3 py-2.5 text-sm"
              >
                {categories.map((item) => (
                  <option key={item} value={item}>
                    {item === 'all' ? 'All categories' : item}
                  </option>
                ))}
              </select>
            </div>
            <div className="mt-4 flex items-center justify-between">
              <p className="text-sm text-text-secondary">
                {visible.length} available ·{' '}
                <strong className="text-primary-700">{selected.size} selected</strong>
              </p>
              <button
                onClick={save}
                disabled={(!memberId && !draftMode) || saving}
                className="rounded-xl bg-primary-600 px-5 py-2.5 text-sm font-bold text-white disabled:opacity-50"
              >
                {saving ? 'Saving…' : 'Save selections'}
              </button>
            </div>
            {loading ? (
              <p className="py-12 text-center text-sm text-text-muted">Loading your profile…</p>
            ) : visible.length === 0 ? (
              <p className="py-12 text-center text-sm text-text-muted">No matching entries found.</p>
            ) : (
              <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {visible.map((item) => (
                  <button
                    type="button"
                    key={item.id}
                    onClick={() => toggle(item.name)}
                    className={`rounded-xl border p-3 text-left transition-colors ${
                      selected.has(item.name)
                        ? 'border-primary-500 bg-primary-50 ring-1 ring-primary-300'
                        : 'border-border-light bg-surface hover:border-primary-300'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <span className="text-sm font-semibold text-text-primary">{item.name}</span>
                      <span className="text-xs">{selected.has(item.name) ? '✓' : ''}</span>
                    </div>
                    <p className="mt-1 text-[11px] text-text-muted">
                      {item.category} · {item.kind}
                    </p>
                  </button>
                ))}
              </div>
            )}
          </div>
        </SignedIn>
      </main>
      <Footer />
    </div>
  )
}
