import { Route, Routes } from 'react-router-dom'
import { LandingPage } from '@/features/landing/LandingPage'
import { AuthPlaceholder } from '@/features/auth/AuthPlaceholder'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<AuthPlaceholder mode="login" />} />
      <Route path="/signup" element={<AuthPlaceholder mode="signup" />} />
    </Routes>
  )
}
