import { Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import AlertsPage from './pages/AlertsPage'
import VisionPage from './pages/VisionPage'
import AuditPage from './pages/AuditPage'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/alertas" element={<AlertsPage />} />
      <Route path="/visao" element={<VisionPage />} />
      <Route path="/auditoria" element={<AuditPage />} />
    </Routes>
  )
}
