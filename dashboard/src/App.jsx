import { Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import AlertsPage from './pages/AlertsPage'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/alertas" element={<AlertsPage />} />
    </Routes>
  )
}
