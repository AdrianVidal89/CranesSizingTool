import { useState, type FormEvent } from 'react'

import {
  calculateHoistRequirement,
  type HoistRequirementInput,
  type HoistRequirementResult,
} from './api'
import InfoTip from './InfoTip'
import { PARAM_INFO } from './paramInfo'

const DEFAULT_INPUT: HoistRequirementInput = {
  mass_load_kg: 5000,
  mass_tool_kg: 200,
  velocity_ms: 0.2,
  accel_time_s: 1.5,
  drum_diameter_m: 0.4,
  reeving_factor: 2,
  gear_ratio: 25,
  efficiency: 0.92,
  motor_inertia_kgm2: 0.05,
  brake_inertia_kgm2: 0.01,
}

const FIELDS: Array<{
  key: keyof HoistRequirementInput
  label: string
  unit: string
  step?: string
  infoKey: string
}> = [
  { key: 'mass_load_kg', label: 'Load mass (SWL)', unit: 'kg', infoKey: 'mass_load_kg' },
  { key: 'mass_tool_kg', label: 'Tool / hook block mass', unit: 'kg', infoKey: 'mass_tool_kg' },
  {
    key: 'velocity_ms',
    label: 'Hoisting speed',
    unit: 'm/s',
    step: '0.01',
    infoKey: 'hoist_velocity_ms',
  },
  {
    key: 'accel_time_s',
    label: 'Acceleration ramp time',
    unit: 's',
    step: '0.1',
    infoKey: 'accel_time_s',
  },
  {
    key: 'drum_diameter_m',
    label: 'Drum diameter',
    unit: 'm',
    step: '0.001',
    infoKey: 'drum_diameter_m',
  },
  { key: 'reeving_factor', label: 'Reeving factor (rope falls)', unit: '', infoKey: 'reeving_factor' },
  { key: 'gear_ratio', label: 'Gearbox ratio', unit: '', infoKey: 'gear_ratio' },
  {
    key: 'efficiency',
    label: 'Mechanical efficiency',
    unit: '0-1',
    step: '0.01',
    infoKey: 'hoist_efficiency',
  },
  {
    key: 'motor_inertia_kgm2',
    label: 'Motor rotor inertia',
    unit: 'kg·m²',
    step: '0.001',
    infoKey: 'motor_inertia_kgm2',
  },
  {
    key: 'brake_inertia_kgm2',
    label: 'Brake inertia',
    unit: 'kg·m²',
    step: '0.001',
    infoKey: 'brake_inertia_kgm2',
  },
]

/** Requirement-stage calculator for a hoist movement (Module 2 —
 *  MECH.HOIST): required torque and speed to lift the hook load, with the
 *  lowering case reported for brake/regeneration awareness. */
function HoistCalculator({ movementName }: { movementName: string }) {
  const [input, setInput] = useState<HoistRequirementInput>(DEFAULT_INPUT)
  const [result, setResult] = useState<HoistRequirementResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  function handleChange(key: keyof HoistRequirementInput, value: string) {
    setInput((prev) => ({ ...prev, [key]: Number(value) }))
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const data = await calculateHoistRequirement(input)
      setResult(data)
    } catch (err) {
      setResult(null)
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <section className="hero">
        <p className="eyebrow">Module 2 · MECH.HOIST</p>
        <h1>{movementName} — hoist requirement</h1>
        <p className="subtitle">
          Agnostic of any specific motor: this computes the torque and speed the hoist
          mechanism needs to lift the hook load, not which motor to use.
        </p>
      </section>

      <form onSubmit={handleSubmit} className="form">
        {FIELDS.map((field) => (
          <label key={field.key} className="field">
            <span>
              {field.label} {field.unit && <em>({field.unit})</em>}{' '}
              <InfoTip info={PARAM_INFO[field.infoKey]} />
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
              <span className="unit">N·m — required torque (lifting)</span>
            </div>
            <div>
              <span className="value">{result.required_speed_rpm}</span>
              <span className="unit">rpm — required motor speed</span>
            </div>
            <div>
              <span className="value">{result.static_lifting_torque_nm}</span>
              <span className="unit">N·m — static torque, lifting</span>
            </div>
            <div>
              <span className="value">{result.static_lowering_torque_nm}</span>
              <span className="unit">N·m — static torque, lowering</span>
            </div>
          </div>

          <p className="warning">
            When lowering, gravity drives the mechanism and the motor works
            regeneratively: the drive and its braking resistor must absorb the lowering
            power, and the mechanical brake must hold at least the lowering static
            torque with the margin your applicable standard requires.
          </p>

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
                <tr key={`${c.formula_id}-${c.label}`}>
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

          <p className="subtitle">
            Duty-cycle analysis and motor/drive candidate validation for hoist movements
            follow the same two-stage flow as travel and will be enabled next; the
            requirement above is the stage-1 input for both.
          </p>
        </section>
      )}
    </>
  )
}

export default HoistCalculator
