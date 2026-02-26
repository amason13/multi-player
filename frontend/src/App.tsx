import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import './App.css'

// Pages (to be created)
// import LoginPage from './pages/LoginPage'
// import DashboardPage from './pages/DashboardPage'
// import LeaguesPage from './pages/LeaguesPage'

function App() {
  return (
    <Router>
      <Routes>
        {/* <Route path="/login" element={<LoginPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/leagues" element={<LeaguesPage />} />
        <Route path="/" element={<Navigate to="/dashboard" replace />} /> */}
        <Route path="/" element={<div>Welcome to Multi-Player</div>} />
      </Routes>
    </Router>
  )
}

export default App
