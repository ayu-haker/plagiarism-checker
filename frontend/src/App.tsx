import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import ScanResults from './pages/ScanResults'
import Humanizer from './pages/Humanizer'

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen">
        <nav className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center h-16 space-x-8">
              <h1 className="text-xl font-bold text-primary-600">
                PlagiarismChecker
              </h1>
              <div className="flex space-x-4">
                <NavLink
                  to="/"
                  className={({ isActive }) =>
                    `px-3 py-2 rounded-md text-sm font-medium ${
                      isActive
                        ? 'bg-primary-50 text-primary-700'
                        : 'text-gray-600 hover:text-primary-600'
                    }`
                  }
                >
                  Dashboard
                </NavLink>
                <NavLink
                  to="/humanizer"
                  className={({ isActive }) =>
                    `px-3 py-2 rounded-md text-sm font-medium ${
                      isActive
                        ? 'bg-primary-50 text-primary-700'
                        : 'text-gray-600 hover:text-primary-600'
                    }`
                  }
                >
                  Humanizer
                </NavLink>
              </div>
            </div>
          </div>
        </nav>
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/scan/:scanId" element={<ScanResults />} />
            <Route path="/humanizer" element={<Humanizer />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

export default App
