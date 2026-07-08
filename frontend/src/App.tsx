import { useState, type FormEvent } from 'react'
import {
  calculateTravelRequirement,
  type TravelRequirementInput,
  type TravelRequirementResult,
} from './api'

const DEFAULT_INPUT: TravelRequirementInput = {
  mass_dead_kg: 800,
  mass_load_kg: 5000,
  mass_tool_kg: 200,
  velocity_ms: 0.5,
  accel_time_s: 2,
  wheel_diameter_m: 0.315,
  gear_ratio: 20,
  efficiency: 0.9,
  motors_count: 2,
  rolling_coeff: 0.016,
}

const FIELDS: Array<{
  key: keyof TravelRequirementInput
  label: string
  unit: string
  step?: string
}> = [
  { key: 'mass_dead_kg', label: 'Dead mass', unit: 'kg' },
  { key: 'mass_load_kg', label: 'Load mass (SWL)', unit: 'kg' },
  { key: 'mass_tool_kg', label: 'Tool / spreader mass', unit: 'kg' },
  { key: 'velocity_ms', label: 'Travel velocity', unit: 'm/s', step: '0.01' },
  { key: 'accel_time_s', label: 'Acceleration ramp time', unit: 's', step: '0.1' },
  { key: 'wheel_diameter_m', label: 'Wheel diameter', unit: 'm', step: '0.001' },
  { key: 'gear_ratio', label: 'Gearbox ratio', unit: '' },
  { key: 'efficiency', label: 'Mechanical efficiency', unit: '0-1', step: '0.01' },
  { key: 'motors_count', label: 'Number of motors', unit: '' },
  { key: 'rolling_coeff', label: 'Rolling resistance coefficient', unit: '', step: '0.001' },
]

function App() {
  const [input, setInput] = useState<TravelRequirementInput>(DEFAULT_INPUT)
  const [result, setResult] = useState<TravelRequirementResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  function handleChange(key: keyof TravelRequirementInput, value: string) {
    setInput((prev) => ({ ...prev, [key]: Number(value) }))
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const data = await calculateTravelRequirement(input)
      setResult(data)
    } catch (err) {
      setResult(null)
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="page">
      <h1>Cranes Sizing Platform</h1>
      <p className="subtitle">
        Travel requirement (Module 1 — MECH.TRAVEL). Manufacturer-agnostic: this
        computes what the mechanism needs, not which motor to use.
      </p>

      <form onSubmit={handleSubmit} className="form">
        {FIELDS.map((field) => (
          <label key={field.key} className="field">
            <span>
              {field.label} {field.unit && <em>({field.unit})</em>}
            </span>
            <input
              type="number"
              step={field.step ?? '1'}
              value={input[field.key]}
              onChange={(e) => handleChange(field.key, e.target.value)}
              required
            />
          </label>
        ))}
        <button type="submit" disabled={loading}>
          {loading ? 'Calculating…' : 'Calculate requirement'}
        </button>
      </form>

      {error && <p className="error">{error}</p>}

      {result && (
        <section className="result">
          <h2>Result</h2>
          <div className="headline">
            <div>
              <span className="value">{result.required_torque_nm}</span>
              <span className="unit">N·m — required torque</span>
            </div>
            <div>
              <span className="value">{result.required_speed_rpm}</span>
              <span className="unit">rpm — required motor speed</span>
            </div>
          </div>

          <table>
            <thead>
              <tr>
                <th>Quantity</th>
                <th>Value</th>
                <th>Formula ID</th>
                <th>Standard(s)</th>
                <th>Assumptions</th>
              </tr>
            </thead>
            <tbody>
              {result.components.map((c) => (
                <tr key={c.formula_id}>
                  <td>{c.label}</td>
                  <td>
                    {c.value} {c.unit}
                  </td>
                  <td>
                    <code>{c.formula_id}</code>
                  </td>
                  <td>{c.standard_refs.join(', ')}</td>
                  <td>{c.assumptions.join('; ')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </main>
  )
}

export default App
