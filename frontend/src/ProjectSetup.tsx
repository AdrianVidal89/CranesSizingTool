import { useState, type FormEvent } from 'react'

import { createProject, type AuthUser, type MovementKind } from './api'
import InfoTip from './InfoTip'
import { PARAM_INFO } from './paramInfo'

export interface MovementSetup {
  localId: string
  kind: MovementKind
  name: string
  /** Backend movement id when the project was persisted (logged in). */
  persistedId: string | null
}

export interface ProjectSetupState {
  name: string
  movements: MovementSetup[]
  /** Backend project id when persisted (logged in), null when local-only. */
  persistedId: string | null
}

const MAX_PER_KIND = 3

const DEFAULT_HOIST_NAMES = ['Main hoist', 'Auxiliary hoist', 'Auxiliary hoist 2']
const DEFAULT_TRAVEL_NAMES = [
  'Long travel (bridge)',
  'Cross travel (trolley)',
  'Cross travel 2',
]

function defaultName(kind: MovementKind, index: number): string {
  const names = kind === 'hoist' ? DEFAULT_HOIST_NAMES : DEFAULT_TRAVEL_NAMES
  return names[index] ?? `${kind === 'hoist' ? 'Hoist' : 'Travel'} ${index + 1}`
}

function resizeNames(current: string[], kind: MovementKind, count: number): string[] {
  return Array.from({ length: count }, (_, i) => current[i] ?? defaultName(kind, i))
}

interface ProjectSetupProps {
  user: AuthUser | null
  onCreated: (setup: ProjectSetupState) => void
}

/** Step 1 of the app: describe the crane project — a name plus how many
 *  hoist and travel movements it has (up to 3 of each) and what each one
 *  is called. Calculations then run per movement. */
function ProjectSetup({ user, onCreated }: ProjectSetupProps) {
  const [projectName, setProjectName] = useState('')
  const [hoistCount, setHoistCount] = useState(1)
  const [travelCount, setTravelCount] = useState(1)
  const [hoistNames, setHoistNames] = useState<string[]>(resizeNames([], 'hoist', 1))
  const [travelNames, setTravelNames] = useState<string[]>(resizeNames([], 'travel', 1))
  const [saveToAccount, setSaveToAccount] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const totalMovements = hoistCount + travelCount

  function changeCount(kind: MovementKind, value: number) {
    if (kind === 'hoist') {
      setHoistCount(value)
      setHoistNames((prev) => resizeNames(prev, 'hoist', value))
    } else {
      setTravelCount(value)
      setTravelNames((prev) => resizeNames(prev, 'travel', value))
    }
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (totalMovements === 0) {
      setError('Define at least one movement (a hoist or a travel).')
      return
    }
    setSubmitting(true)
    setError(null)

    const movements: MovementSetup[] = [
      ...hoistNames.map((name, i) => ({
        localId: `hoist-${i}`,
        kind: 'hoist' as const,
        name: name.trim() || defaultName('hoist', i),
        persistedId: null as string | null,
      })),
      ...travelNames.map((name, i) => ({
        localId: `travel-${i}`,
        kind: 'travel' as const,
        name: name.trim() || defaultName('travel', i),
        persistedId: null as string | null,
      })),
    ]

    try {
      let persistedId: string | null = null
      if (user && saveToAccount) {
        const project = await createProject({
          name: projectName.trim(),
          movements: movements.map((m) => ({ kind: m.kind, name: m.name })),
        })
        persistedId = project.id
        // The API returns movements in creation order — same order as sent.
        project.movements.forEach((created, i) => {
          if (movements[i]) movements[i].persistedId = created.id
        })
      }
      onCreated({ name: projectName.trim(), movements, persistedId })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setSubmitting(false)
    }
  }

  const counts = [0, 1, 2, 3].filter((n) => n <= MAX_PER_KIND)

  return (
    <section className="setup">
      <section className="hero">
        <p className="eyebrow">Step 1 · Project setup</p>
        <h1>Describe your crane project</h1>
        <p className="subtitle">
          Give the project a name and tell us which movements the crane has — up to three
          hoists and three travel movements, each with its own name. You will size and
          validate each movement separately in the next step.
        </p>
      </section>

      <form onSubmit={handleSubmit} className="form setup-form">
        <label className="field field-wide">
          <span>Project name</span>
          <input
            type="text"
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
            placeholder="e.g. Crane 86"
            maxLength={200}
            required
          />
        </label>

        <label className="field">
          <span>
            Hoist movements <InfoTip info={PARAM_INFO.setup_hoist} />
          </span>
          <select
            value={hoistCount}
            onChange={(e) => changeCount('hoist', Number(e.target.value))}
          >
            {counts.map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
        </label>

        <label className="field">
          <span>
            Travel movements <InfoTip info={PARAM_INFO.setup_travel} />
          </span>
          <select
            value={travelCount}
            onChange={(e) => changeCount('travel', Number(e.target.value))}
          >
            {counts.map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
        </label>

        {hoistNames.map((name, i) => (
          <label key={`hoist-${i}`} className="field">
            <span>Hoist {i + 1} name</span>
            <input
              type="text"
              value={name}
              maxLength={200}
              onChange={(e) =>
                setHoistNames((prev) => prev.map((n, j) => (j === i ? e.target.value : n)))
              }
              required
            />
          </label>
        ))}

        {travelNames.map((name, i) => (
          <label key={`travel-${i}`} className="field">
            <span>Travel {i + 1} name</span>
            <input
              type="text"
              value={name}
              maxLength={200}
              onChange={(e) =>
                setTravelNames((prev) => prev.map((n, j) => (j === i ? e.target.value : n)))
              }
              required
            />
          </label>
        ))}

        {user ? (
          <label className="field">
            <span>
              <input
                type="checkbox"
                checked={saveToAccount}
                onChange={(e) => setSaveToAccount(e.target.checked)}
              />{' '}
              Save this project to my account
            </span>
          </label>
        ) : (
          <p className="field-note">
            Working locally — log in (top right) if you want the project saved to your
            account.
          </p>
        )}

        <button type="submit" disabled={submitting || totalMovements === 0}>
          {submitting ? 'Creating…' : 'Create project'}
        </button>
      </form>

      {totalMovements === 0 && (
        <p className="warning">Define at least one movement (a hoist or a travel).</p>
      )}
      {error && <p className="error">{error}</p>}
    </section>
  )
}

export default ProjectSetup
