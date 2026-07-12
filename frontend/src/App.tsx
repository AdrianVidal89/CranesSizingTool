import { useEffect, useState, type FormEvent } from 'react'

import {
  fetchCurrentUser,
  loginUser,
  logoutUser,
  registerUser,
  type AuthUser,
} from './api'
import HoistCalculator from './HoistCalculator'
import ProjectSetup, { type ProjectSetupState } from './ProjectSetup'
import TravelCalculator from './TravelCalculator'

function BrandMark() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M4 6h16M6 6v13M18 6v13M11 9h2v3h-2z"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M12 12v5m-2.2-1.6c0 1.6 4.4 1.6 4.4 0"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function App() {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login')
  const [authEmail, setAuthEmail] = useState('')
  const [authPassword, setAuthPassword] = useState('')
  const [authError, setAuthError] = useState<string | null>(null)
  const [authLoading, setAuthLoading] = useState(false)

  const [project, setProject] = useState<ProjectSetupState | null>(null)
  const [activeMovement, setActiveMovement] = useState(0)

  useEffect(() => {
    fetchCurrentUser()
      .then(setUser)
      .catch(() => setUser(null))
  }, [])

  async function handleAuthSubmit(event: FormEvent) {
    event.preventDefault()
    setAuthLoading(true)
    setAuthError(null)
    try {
      if (authMode === 'register') {
        await registerUser(authEmail, authPassword)
      }
      const loggedIn = await loginUser(authEmail, authPassword)
      setUser(loggedIn)
      setAuthPassword('')
    } catch (err) {
      setAuthError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setAuthLoading(false)
    }
  }

  async function handleLogout() {
    try {
      await logoutUser()
    } finally {
      setUser(null)
    }
  }

  function handleNewProject() {
    const confirmed = window.confirm(
      'Start a new project? Unsaved calculations in the current movements will be discarded.',
    )
    if (confirmed) {
      setProject(null)
      setActiveMovement(0)
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="brand">
          <span className="brand-mark">
            <BrandMark />
          </span>
          <div className="brand-text">
            <span className="brand-title">Cranes Sizing Platform</span>
            <span className="brand-tagline">Manufacturer-neutral drive sizing</span>
          </div>
        </div>
        <div className="header-auth">
          {user ? (
            <div className="user-chip">
              <span>
                Signed in as <strong>{user.email}</strong>
              </span>
              <button type="button" onClick={handleLogout}>
                Log out
              </button>
            </div>
          ) : (
            <form onSubmit={handleAuthSubmit} className="form auth-form">
              <label className="field">
                <span>Email</span>
                <input
                  type="email"
                  value={authEmail}
                  onChange={(e) => setAuthEmail(e.target.value)}
                  required
                />
              </label>
              <label className="field">
                <span>Password</span>
                <input
                  type="password"
                  minLength={8}
                  value={authPassword}
                  onChange={(e) => setAuthPassword(e.target.value)}
                  required
                />
              </label>
              <label className="field">
                <span>&nbsp;</span>
                <select
                  value={authMode}
                  onChange={(e) => setAuthMode(e.target.value as 'login' | 'register')}
                >
                  <option value="login">Log in</option>
                  <option value="register">Register</option>
                </select>
              </label>
              <button type="submit" disabled={authLoading}>
                {authLoading ? 'Please wait…' : authMode === 'login' ? 'Log in' : 'Register'}
              </button>
            </form>
          )}
        </div>
      </header>

      <main className="page">
        {authError && <p className="error">{authError}</p>}

        {project === null ? (
          <ProjectSetup
            user={user}
            onCreated={(setup) => {
              setProject(setup)
              setActiveMovement(0)
            }}
          />
        ) : (
          <>
            <div className="project-bar">
              <div className="project-bar-info">
                <span className="eyebrow">Project</span>
                <h1>{project.name}</h1>
              </div>
              <button type="button" className="project-bar-action" onClick={handleNewProject}>
                New project
              </button>
            </div>

            <nav className="movement-tabs" aria-label="Crane movements">
              {project.movements.map((movement, index) => (
                <button
                  key={movement.localId}
                  type="button"
                  className={`movement-tab ${index === activeMovement ? 'active' : ''}`}
                  aria-current={index === activeMovement ? 'page' : undefined}
                  onClick={() => setActiveMovement(index)}
                >
                  <span className="movement-tab-kind">
                    {movement.kind === 'hoist' ? 'Hoist' : 'Travel'}
                  </span>
                  {movement.name}
                </button>
              ))}
            </nav>

            {/* All calculators stay mounted (hidden) so switching tabs never
                loses entered data or results. */}
            {project.movements.map((movement, index) => (
              <div key={movement.localId} hidden={index !== activeMovement}>
                {movement.kind === 'travel' ? (
                  <TravelCalculator
                    user={user}
                    movementName={movement.name}
                    projectId={project.persistedId}
                    projectName={project.name}
                  />
                ) : (
                  <HoistCalculator movementName={movement.name} />
                )}
              </div>
            ))}
          </>
        )}
      </main>

      <footer className="app-footer">
        Manufacturer-neutral · Runs entirely on your own infrastructure · No tracking, no
        telemetry.
      </footer>
    </div>
  )
}

export default App
