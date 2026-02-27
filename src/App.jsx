import { useState } from 'react'
import {
  LayoutDashboard,
  Search,
  TrendingUp,
  MapPin,
  Calendar,
  BookOpen,
  PieChart,
  User,
  GraduationCap
} from 'lucide-react'
import { motion } from 'framer-motion'
import './App.css'
import BranchExplorer, { branches } from './components/BranchExplorer'
import ClosingRanks from './components/ClosingRanks'

function App() {
  const [activeTab, setActiveTab] = useState('closing-ranks') // Set as default for now
  const [searchQuery, setSearchQuery] = useState('')

  const navItems = [
    { id: 'dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { id: 'closing-ranks', icon: TrendingUp, label: 'Closing Ranks' },
    { id: 'branches', icon: BookOpen, label: 'Branch Explorer' },
    { id: 'colleges', icon: MapPin, label: 'College Finder' },
    { id: 'timeline', icon: Calendar, label: 'Counselling Timeline' },
  ]

  const stats = [
    { label: 'Total Seats', value: '45,210', icon: GraduationCap, color: '#4f46e5' },
    { label: 'Govt. Seats', value: '25,840', icon: TrendingUp, color: '#0ea5e9' },
    { label: 'Top Branch', value: 'Radio Dx', icon: BookOpen, color: '#f43f5e' },
    { label: 'Eligible Candidates', value: '1.8L+', icon: User, color: '#10b981' },
  ]

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div className="logo-container">
          <GraduationCap className="logo-icon" />
          <span>NEET PG 2026</span>
        </div>

        <nav>
          <ul className="nav-links">
            {navItems.map((item) => (
              <li key={item.id}>
                <button
                  onClick={() => setActiveTab(item.id)}
                  className={`nav-item glass-panel ${activeTab === item.id ? 'active' : ''}`}
                  style={{ width: '100%', background: 'none' }}
                >
                  <item.icon size={20} />
                  {item.label}
                </button>
              </li>
            ))}
          </ul>
        </nav>
      </aside>

      {/* Main Content Area */}
      <main className="main-content">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <section className="hero-section">
            <h1 className="hero-title">NEET PG Counselling <br />Intelligence Dashboard</h1>
            <p style={{ color: 'var(--text-muted)', fontSize: '1.125rem' }}>
              Data-driven insights to help you secure the best possible medical PG seat.
            </p>

            <div className="search-bar glass-panel">
              <Search size={22} color="var(--text-muted)" />
              <input
                type="text"
                placeholder="Search for branches, colleges, or ranks..."
                className="search-input"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
          </section>

          <div className="stats-grid">
            {stats.map((stat, index) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.1 }}
                className="card glass-panel"
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span className="card-title">{stat.label}</span>
                  <stat.icon size={20} color={stat.color} />
                </div>
                <span className="card-value">{stat.value}</span>
              </motion.div>
            ))}
          </div>

          <section className="dashboard-content">
            <div className="glass-panel" style={{ padding: '2rem', minHeight: '300px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <h2 style={{ fontSize: '1.25rem' }}>
                  {activeTab === 'branches' ? 'Branch Explorer' : 'Trending Branches (2025)'}
                </h2>
                {activeTab === 'branches' && (
                  <span style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
                    Showing {branches.length} national specialties
                  </span>
                )}
              </div>

              {activeTab === 'closing-ranks' ? (
                <ClosingRanks />
              ) : activeTab === 'branches' || activeTab === 'dashboard' ? (
                <BranchExplorer searchQuery={searchQuery} />
              ) : (
                <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '3rem' }}>
                  Visualization for {activeTab} will be implemented soon...
                </div>
              )}
            </div>
          </section>
        </motion.div>
      </main>
    </div>
  )
}

export default App
