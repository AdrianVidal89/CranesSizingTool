import { useEffect, useState, type FormEvent } from 'react'
import {
  downloadReportPdf,
  generateReport,
  listCalculationRuns,
  listProjects,
  saveCalculationRun,
  type AuthUser,
  type CalculationRunSummary,
  type Project,
  type ValidateCandidateInput,
} from './api'

interface SavePanelProps {
  user: AuthUser | null
  calculationInput: ValidateCandidateInput | null
  /** Project created in the setup step (null when working locally). */
  defaultProjectId?: string | null
  defaultProjectName?: string
  defaultMovementName?: string
}

function SavePanel({
  user,
  calculationInput,
  defaultProjectId = null,
  defaultProjectName = '',
  defaultMovementName = 'Trolley travel',
}: SavePanelProps) {
  const [projects, setProjects] = useState<Project[]>([])
  const [runs, setRuns] = useState<CalculationRunSummary[]>([])
  const [projectChoice, setProjectChoice] = useState<string>(defaultProjectId ?? 'new')
  const [newProjectName, setNewProjectName] = useState(defaultProjectName)
  const [craneConfigurationName, setCraneConfigurationName] = useState('Crane configuration')
  const [movementName, setMovementName] = useState(defaultMovementName)
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [saveSuccess, setSaveSuccess] = useState(false)
  const [downloadingId, setDownloadingId] = useState<string | null>(null)
  const [listError, setListError] = useState<string | null>(null)

  async function refreshLists() {
    try {
      const [projectList, runList] = await Promise.all([listProjects(), listCalculationRuns()])
      setProjects(projectList)
      setRuns(runList)
      setListError(null)
    } catch (err) {
      setListError(err instanceof Error ? err.message : 'Unknown error')
    }
  }

  useEffect(() => {
    if (user) {
      refreshLists()
    } else {
      setProjects([])
      setRuns([])
    }
  }, [user])

  if (!user) {
    return null
  }

  async function handleSave(event: FormEvent) {
    event.preventDefault()
    if (!calculationInput) return
    setSaving(true)
    setSaveError(null)
    setSaveSuccess(false)
    try {
      await saveCalculationRun({
        ...calculationInput,
        project_id: projectChoice === 'new' ? null : projectChoice,
        new_project_name: projectChoice === 'new' ? newProjectName : null,
        crane_configuration_name: craneConfigurationName,
        movement_kind: 'travel',
        movement_name: movementName,
      })
      setSaveSuccess(true)
      await refreshLists()
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setSaving(false)
    }
  }

  async function handleDownload(runId: string) {
    setDownloadingId(runId)
    setListError(null)
    try {
      const report = await generateReport(runId)
      const blob = await downloadReportPdf(report.id)
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `crane-report-${runId}.pdf`
      document.body.appendChild(link)
      link.click()
      link.remove()
      URL.revokeObjectURL(url)
    } catch (err) {
      setListError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setDownloadingId(null)
    }
  }

  return (
    <section className="candidate">
      <h2>Save & reports</h2>
      <p className="subtitle">
        Save a validated calculation to a project, then download a traceable PDF report at
        any time.
      </p>

      {calculationInput ? (
        <form onSubmit={handleSave} className="form">
          <label className="field">
            <span>Project</span>
            <select value={projectChoice} onChange={(e) => setProjectChoice(e.target.value)}>
              <option value="new">+ New project</option>
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </label>

          {projectChoice === 'new' && (
            <label className="field">
              <span>New project name</span>
              <input
                type="text"
                value={newProjectName}
                onChange={(e) => setNewProjectName(e.target.value)}
                required
              />
            </label>
          )}

          <label className="field">
            <span>Crane configuration name</span>
            <input
              type="text"
              value={craneConfigurationName}
              onChange={(e) => setCraneConfigurationName(e.target.value)}
              required
            />
          </label>

          <label className="field">
            <span>Movement name</span>
            <input
              type="text"
              value={movementName}
              onChange={(e) => setMovementName(e.target.value)}
              required
            />
          </label>

          <button type="submit" disabled={saving}>
            {saving ? 'Saving…' : 'Save this calculation'}
          </button>
        </form>
      ) : (
        <p className="subtitle">Validate a candidate above to save this calculation.</p>
      )}

      {saveError && <p className="error">{saveError}</p>}
      {saveSuccess && <p className="subtitle">Saved.</p>}

      <h3>Saved calculations</h3>
      {listError && <p className="error">{listError}</p>}
      {runs.length === 0 ? (
        <p className="subtitle">No saved calculations yet.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Saved at</th>
              <th>Formulas used</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {runs.map((run) => (
              <tr key={run.id}>
                <td>{new Date(run.created_at).toLocaleString()}</td>
                <td>{run.formula_ids.length}</td>
                <td>
                  <button
                    type="button"
                    onClick={() => handleDownload(run.id)}
                    disabled={downloadingId === run.id}
                  >
                    {downloadingId === run.id ? 'Preparing…' : 'Download PDF'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}

export default SavePanel
