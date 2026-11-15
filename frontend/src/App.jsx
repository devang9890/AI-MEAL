import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuth, useUser } from '@clerk/clerk-react'
import { MemberDraftProvider } from './context/MemberDraftContext'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Register from './pages/Register'
import Recipes from './pages/Recipes'
import Ingredients from './pages/Ingredients'
import Household from './pages/Household'
import MealPlan from './pages/MealPlan'
import GroceryList from './pages/GroceryList'
import HealthSelection from './pages/HealthSelection'

function App() {
  const { isSignedIn, getToken } = useAuth()
  const { user, isLoaded } = useUser()

  useEffect(() => {
    const syncUser = async () => {
      if (isSignedIn && isLoaded && user) {
        try {
          const token = await getToken()
          const email = user.primaryEmailAddress?.emailAddress || ''
          const name = user.fullName || `${user.firstName || ''} ${user.lastName || ''}`.trim() || ''

          // Call the backend /api/me POST endpoint to sync user details to Neon
          await fetch('http://localhost:8000/api/me', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${token}`
            },
            body: JSON.stringify({ email, name })
          })
        } catch (error) {
          console.error('Failed to sync user with backend:', error)
        }
      }
    }
    syncUser()
  }, [isSignedIn, isLoaded, user, getToken])

  return (
    <BrowserRouter>
      <MemberDraftProvider>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/recipes" element={<Recipes />} />
          <Route path="/ingredients" element={<Ingredients />} />
          <Route path="/household" element={<Household />} />
          <Route path="/meal-plan" element={<MealPlan />} />
          <Route path="/grocery-list" element={<GroceryList />} />
          <Route path="/allergies" element={<HealthSelection type="allergies" />} />
          <Route path="/diseases" element={<HealthSelection type="diseases" />} />
          {/* Redirect already-signed-in users away from auth pages */}
          <Route
            path="/login"
            element={isSignedIn ? <Navigate to="/" replace /> : <Login />}
          />
          <Route
            path="/register"
            element={isSignedIn ? <Navigate to="/" replace /> : <Register />}
          />
        </Routes>
      </MemberDraftProvider>
    </BrowserRouter>
  )
}

export default App