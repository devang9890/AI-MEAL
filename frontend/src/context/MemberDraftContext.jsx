import { createContext, useCallback, useContext, useMemo, useState } from 'react'

export const MEMBER_DRAFT_KEY = 'aiMeal.memberDraft'
export const MEMBER_DRAFT_FLOW = 'member-draft'

export const emptyMemberDraft = (overrides = {}) => ({
  flow: MEMBER_DRAFT_FLOW,
  isEdit: false,
  memberId: null,
  householdId: null,
  name: '',
  age: '',
  gender: 'male',
  height_cm: '',
  weight_kg: '',
  activity_level: 'moderate',
  dietary_preference: 'vegetarian',
  allergies: '',
  diseases: '',
  dietary_restrictions: '',
  ...overrides,
})

export function readMemberDraft() {
  try {
    const raw = sessionStorage.getItem(MEMBER_DRAFT_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw)
    if (!parsed || parsed.flow !== MEMBER_DRAFT_FLOW) return null
    return { ...emptyMemberDraft(), ...parsed, flow: MEMBER_DRAFT_FLOW }
  } catch {
    return null
  }
}

export function writeMemberDraft(draft) {
  const next = { ...emptyMemberDraft(), ...draft, flow: MEMBER_DRAFT_FLOW }
  sessionStorage.setItem(MEMBER_DRAFT_KEY, JSON.stringify(next))
  return next
}

export function clearMemberDraftStorage() {
  sessionStorage.removeItem(MEMBER_DRAFT_KEY)
}

/** Map a saved member (API) or prior draft into the draft shape. */
export function memberToDraft(member, { householdId = null, isEdit = false } = {}) {
  if (!member) {
    return emptyMemberDraft({ householdId })
  }
  return emptyMemberDraft({
    isEdit: isEdit || Boolean(member.id),
    memberId: member.id ?? member.memberId ?? null,
    householdId: householdId ?? member.householdId ?? null,
    name: member.name ?? '',
    age: member.age != null && member.age !== '' ? String(member.age) : '',
    gender: member.gender || 'male',
    height_cm:
      member.height_cm != null && member.height_cm !== ''
        ? String(member.height_cm)
        : '',
    weight_kg:
      member.weight_kg != null && member.weight_kg !== ''
        ? String(member.weight_kg)
        : '',
    activity_level: member.activity_level || 'moderate',
    dietary_preference: member.dietary_preference || 'vegetarian',
    allergies: member.allergies || '',
    diseases: member.diseases || '',
    dietary_restrictions:
      member.dietary_restrictions || member.restrictions || '',
  })
}

const MemberDraftContext = createContext(null)

export function MemberDraftProvider({ children }) {
  const [draft, setDraft] = useState(() => readMemberDraft())

  const persist = useCallback((next) => {
    const saved = writeMemberDraft(next)
    setDraft(saved)
    return saved
  }, [])

  const startDraft = useCallback(
    (seed = {}) => persist(emptyMemberDraft(seed)),
    [persist]
  )

  const updateDraft = useCallback(
    (patch) => {
      const current = readMemberDraft() || emptyMemberDraft()
      return persist({ ...current, ...patch, flow: MEMBER_DRAFT_FLOW })
    },
    [persist]
  )

  const patchField = useCallback(
    (field, value) => {
      const current = readMemberDraft() || emptyMemberDraft()
      return persist({ ...current, [field]: value, flow: MEMBER_DRAFT_FLOW })
    },
    [persist]
  )

  const clearDraft = useCallback(() => {
    clearMemberDraftStorage()
    setDraft(null)
  }, [])

  const refreshFromStorage = useCallback(() => {
    const current = readMemberDraft()
    setDraft(current)
    return current
  }, [])

  const value = useMemo(
    () => ({
      draft,
      hasDraft: Boolean(draft),
      startDraft,
      updateDraft,
      patchField,
      clearDraft,
      refreshFromStorage,
      readMemberDraft,
    }),
    [draft, startDraft, updateDraft, patchField, clearDraft, refreshFromStorage]
  )

  return (
    <MemberDraftContext.Provider value={value}>
      {children}
    </MemberDraftContext.Provider>
  )
}

export function useMemberDraft() {
  const ctx = useContext(MemberDraftContext)
  if (!ctx) {
    throw new Error('useMemberDraft must be used within MemberDraftProvider')
  }
  return ctx
}
