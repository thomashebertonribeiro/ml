import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Navbar } from './components/shared/Navbar'
import { ProtectedRoute } from './components/shared/ProtectedRoute'
import { ErrorBoundary } from './components/shared/ErrorBoundary'
import { LoginPage } from './pages/LoginPage'
import { RegisterPage } from './pages/RegisterPage'
import { DashboardPage } from './pages/DashboardPage'
import { BrowsePage } from './pages/BrowsePage'
import { SearchPage } from './pages/SearchPage'
import { ChangesPage } from './pages/ChangesPage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ErrorBoundary>
          <Navbar />
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/" element={
              <ProtectedRoute><DashboardPage /></ProtectedRoute>
            } />
            <Route path="/browse" element={
              <ProtectedRoute><BrowsePage /></ProtectedRoute>
            } />
            <Route path="/search" element={
              <ProtectedRoute><SearchPage /></ProtectedRoute>
            } />
            <Route path="/changes" element={
              <ProtectedRoute><ChangesPage /></ProtectedRoute>
            } />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </ErrorBoundary>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
