import { useEffect, useState } from "react"
import axios from "axios"

function App() {
  const [backendStatus, setBackendStatus] = useState("Checking backend...")

  useEffect(() => {
    axios
      .get("http://localhost:8000/api/health")
      .then((response) => {
        setBackendStatus(response.data.status)
      })
      .catch(() => {
        setBackendStatus("Backend unavailable")
      })
  }, [])

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center">
      <div className="rounded-2xl bg-white p-10 text-center shadow-lg">
        <h1 className="text-4xl font-bold text-slate-900">
          AI Meal Planner
        </h1>

        <p className="mt-3 text-slate-600">
          Personalized nutrition and budget optimization
        </p>

        <div className="mt-6 rounded-lg bg-slate-100 p-4">
          <p className="text-sm text-slate-500">
            Backend Status
          </p>

          <p className="mt-1 font-semibold text-green-600">
            {backendStatus}
          </p>
        </div>
      </div>
    </div>
  )
}

export default App