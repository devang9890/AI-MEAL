import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuth, useUser } from '@clerk/clerk-react'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Register from './pages/Register'

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
      <Routes>
        <Route path="/" element={<Landing />} />
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
    </BrowserRouter>
  )
}

export default App