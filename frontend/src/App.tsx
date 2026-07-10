import { useEffect, useState, type FormEvent } from 'react'
import SavePanel from './SavePanel'
import {
  calculateDutyCycle,
  calculateTravelRequirement,
  fetchCurrentUser,
  loginUser,
  logoutUser,
  registerUser,
  validateCandidate,
  type AuthUser,
  type DutyCycleResult,
  type MotorCandidateInput,
  type TravelRequirementInput,
  type TravelRequirementResult,
  type ValidateCandidateInput,
  type ValidateCandidateResult,
} from './api'

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

type DutyRegimeMode = 'duty_factor_pct' | 'starts_per_hour'

interface CycleFormState {
  distance_m: number
  decel_time_s: string
  regimeMode: DutyRegimeMode
  regimeValue: number
  cooling_factor: number
  mechanism_group: string
}

const DEFAULT_CYCLE: CycleFormState = {
  distance_m: 10,
  decel_time_s: '',
  regimeMode: 'duty_factor_pct',
  regimeValue: 25,
  cooling_factor: 0.5,
  mechanism_group: '',
}

type TorqueInputMode = 'pu' | 'nm'

interface MotorFormState {
  rated_power_kw: number
  rated_speed_rpm: number
  rated_voltage_v: number
  power_factor: number
  efficiency: number
  nameplate_frequency_hz: number
  motor_target_frequency_hz: number
  torqueInputMode: TorqueInputMode
  breakdown_torque_value: number
  max_mechanical_torque_value: number
  no_load_current_a: string
  rotor_inertia_kgm2: number
}

const DEFAULT_MOTOR: MotorFormState = {
  rated_power_kw: 2.2,
  rated_speed_rpm: 750,
  rated_voltage_v: 400,
  power_factor: 0.85,
  efficiency: 0.87,
  nameplate_frequency_hz: 50,
  motor_target_frequency_hz: 50,
  torqueInputMode: 'pu',
  breakdown_torque_value: 2.5,
  max_mechanical_torque_value: 3.0,
  no_load_current_a: '',
  rotor_inertia_kgm2: 0,
}

interface DriveFormState {
  enabled: boolean
  rated_current_a: number
  overload_factor: number
  overload_duration_s: number
  rated_voltage_v: number
}

const DEFAULT_DRIVE: DriveFormState = {
  enabled: true,
  rated_current_a: 6.0,
  overload_factor: 1.6,
  overload_duration_s: 60,
  rated_voltage_v: 400,
}

function App() {
  const [input, setInput] = useState<TravelRequirementInput>(DEFAULT_INPUT)
  const [result, setResult] = useState<TravelRequirementResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const [cycle, setCycle] = useState<CycleFormState>(DEFAULT_CYCLE)
  const [cycleResult, setCycleResult] = useState<DutyCycleResult | null>(null)
  const [cycleError, setCycleError] = useState<string | null>(null)
  const [cycleLoading, setCycleLoading] = useState(false)

  const [motor, setMotor] = useState<MotorFormState>(DEFAULT_MOTOR)
  const [drive, setDrive] = useState<DriveFormState>(DEFAULT_DRIVE)
  const [validation, setValidation] = useState<ValidateCandidateResult | null>(null)
  const [validationError, setValidationError] = useState<string | null>(null)
  const [validationLoading, setValidationLoading] = useState(false)
  const [lastValidatedInput, setLastValidatedInput] = useState<ValidateCandidateInput | null>(
    null,
  )

  const [user, setUser] = useState<AuthUser | null>(null)
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login')
  const [authEmail, setAuthEmail] = useState('')
  const [authPassword, setAuthPassword] = useState('')
  const [authError, setAuthError] = useState<string | null>(null)
  const [authLoading, setAuthLoading] = useState(false)

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

  async function handleCycleSubmit(event: FormEvent) {
    event.preventDefault()
    setCycleLoading(true)
    setCycleError(null)
    try {
      const data = await calculateDutyCycle({
        ...input,
        distance_m: cycle.distance_m,
        decel_time_s: cycle.decel_time_s === '' ? null : Number(cycle.decel_time_s),
        duty_factor_pct: cycle.regimeMode === 'duty_factor_pct' ? cycle.regimeValue : null,
        starts_per_hour: cycle.regimeMode === 'starts_per_hour' ? cycle.regimeValue : null,
        cooling_factor: cycle.cooling_factor,
        mechanism_group: cycle.mechanism_group === '' ? null : cycle.mechanism_group,
      })
      setCycleResult(data)
    } catch (err) {
      setCycleResult(null)
      setCycleError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setCycleLoading(false)
    }
  }

  const isRegenerative =
    cycleResult?.decel_torque.is_regenerative || cycleResult?.energy.has_regenerative_phase

  async function handleValidateSubmit(event: FormEvent) {
    event.preventDefault()
    setValidationLoading(true)
    setValidationError(null)
    try {
      const motorPayload: MotorCandidateInput = {
        rated_power_kw: motor.rated_power_kw,
        rated_speed_rpm: motor.rated_speed_rpm,
        rated_voltage_v: motor.rated_voltage_v,
        power_factor: motor.power_factor,
        efficiency: motor.efficiency,
        nameplate_frequency_hz: motor.nameplate_frequency_hz,
        breakdown_torque_pu:
          motor.torqueInputMode === 'pu' ? motor.breakdown_torque_value : null,
        breakdown_torque_nm:
          motor.torqueInputMode === 'nm' ? motor.breakdown_torque_value : null,
        max_mechanical_torque_pu:
          motor.torqueInputMode === 'pu' ? motor.max_mechanical_torque_value : null,
        max_mechanical_torque_nm:
          motor.torqueInputMode === 'nm' ? motor.max_mechanical_torque_value : null,
        no_load_current_a:
          motor.no_load_current_a === '' ? null : Number(motor.no_load_current_a),
        rotor_inertia_kgm2: motor.rotor_inertia_kgm2,
      }
      const candidatePayload: ValidateCandidateInput = {
        ...input,
        distance_m: cycle.distance_m,
        decel_time_s: cycle.decel_time_s === '' ? null : Number(cycle.decel_time_s),
        duty_factor_pct: cycle.regimeMode === 'duty_factor_pct' ? cycle.regimeValue : null,
        starts_per_hour: cycle.regimeMode === 'starts_per_hour' ? cycle.regimeValue : null,
        cooling_factor: cycle.cooling_factor,
        mechanism_group: cycle.mechanism_group === '' ? null : cycle.mechanism_group,
        motor: motorPayload,
        motor_target_frequency_hz: motor.motor_target_frequency_hz,
        drive: drive.enabled
          ? {
              rated_current_a: drive.rated_current_a,
              overload_factor: drive.overload_factor,
              overload_duration_s: drive.overload_duration_s,
              rated_voltage_v: drive.rated_voltage_v,
            }
          : null,
      }
      const data = await validateCandidate(candidatePayload)
      setValidation(data)
      setLastValidatedInput(candidatePayload)
    } catch (err) {
      setValidation(null)
      setValidationError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setValidationLoading(false)
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

        <section className="hero">
          <p className="eyebrow">Module 1 · MECH.TRAVEL</p>
          <h1>Travel requirement</h1>
          <p className="subtitle">
            Agnostic of any specific motor: this computes what the mechanism needs, not
            which motor to use.
          </p>
        </section>

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

          <section className="cycle">
            <h2>Duty cycle (Module 4 — CYCLE)</h2>
            <p className="subtitle">
              Now that the torque/speed requirement is known, describe the movement's
              distance and service regime to get the phase profile, thermal RMS
              torque, and estimated energy consumption.
            </p>

            <form onSubmit={handleCycleSubmit} className="form">
              <label className="field">
                <span>
                  Distance <em>(m)</em>
                </span>
                <input
                  type="number"
                  step="0.1"
                  value={cycle.distance_m}
                  onChange={(e) =>
                    setCycle((prev) => ({ ...prev, distance_m: Number(e.target.value) }))
                  }
                  required
                />
              </label>

              <label className="field">
                <span>
                  Deceleration ramp time <em>(s, optional — defaults to accel time)</em>
                </span>
                <input
                  type="number"
                  step="0.1"
                  value={cycle.decel_time_s}
                  placeholder={String(input.accel_time_s)}
                  onChange={(e) =>
                    setCycle((prev) => ({ ...prev, decel_time_s: e.target.value }))
                  }
                />
              </label>

              <label className="field">
                <span>Duty regime input</span>
                <select
                  value={cycle.regimeMode}
                  onChange={(e) =>
                    setCycle((prev) => ({
                      ...prev,
                      regimeMode: e.target.value as DutyRegimeMode,
                    }))
                  }
                >
                  <option value="duty_factor_pct">Target %ED</option>
                  <option value="starts_per_hour">Starts per hour</option>
                </select>
              </label>

              <label className="field">
                <span>
                  {cycle.regimeMode === 'duty_factor_pct'
                    ? 'Target %ED'
                    : 'Starts per hour'}{' '}
                  <em>{cycle.regimeMode === 'duty_factor_pct' ? '(0-100)' : '(1/h)'}</em>
                </span>
                <input
                  type="number"
                  step="0.1"
                  value={cycle.regimeValue}
                  onChange={(e) =>
                    setCycle((prev) => ({ ...prev, regimeValue: Number(e.target.value) }))
                  }
                  required
                />
              </label>

              <label className="field">
                <span>
                  Standstill cooling factor k_f <em>(0-1)</em>
                </span>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  max="1"
                  value={cycle.cooling_factor}
                  onChange={(e) =>
                    setCycle((prev) => ({
                      ...prev,
                      cooling_factor: Number(e.target.value),
                    }))
                  }
                  required
                />
              </label>

              <label className="field">
                <span>
                  Mechanism group <em>(optional, e.g. M5)</em>
                </span>
                <input
                  type="text"
                  value={cycle.mechanism_group}
                  onChange={(e) =>
                    setCycle((prev) => ({ ...prev, mechanism_group: e.target.value }))
                  }
                />
              </label>

              <button type="submit" disabled={cycleLoading}>
                {cycleLoading ? 'Calculating…' : 'Calculate duty cycle'}
              </button>
            </form>
          </section>

          {cycleError && <p className="error">{cycleError}</p>}

          {cycleResult && (
            <>
            <section className="result">
              <h3>Duty cycle result</h3>

              {isRegenerative && (
                <p className="warning">
                  Regenerative operation detected: this movement returns energy to
                  the drive during deceleration. Size a braking resistor
                  accordingly.
                </p>
              )}

              <div className="headline">
                <div>
                  <span className="value">
                    {cycleResult.profile.is_triangular ? 'Triangular' : 'Trapezoidal'}
                  </span>
                  <span className="unit">motion profile</span>
                </div>
                <div>
                  <span className="value">{cycleResult.regime.duty_factor_pct}</span>
                  <span className="unit">%ED</span>
                </div>
                <div>
                  <span className="value">{cycleResult.regime.starts_per_hour}</span>
                  <span className="unit">starts/hour</span>
                </div>
                <div>
                  <span className="value">{cycleResult.rms_torque.value}</span>
                  <span className="unit">N·m — RMS torque</span>
                </div>
                <div>
                  <span className="value">
                    {(cycleResult.energy.energy_per_cycle_j / 3600).toFixed(3)}
                  </span>
                  <span className="unit">Wh — energy per cycle</span>
                </div>
              </div>

              <table>
                <thead>
                  <tr>
                    <th>Phase</th>
                    <th>Time (s)</th>
                    <th>Distance (m)</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>Acceleration</td>
                    <td>{cycleResult.profile.accel_time_s}</td>
                    <td>{cycleResult.profile.accel_distance_m}</td>
                  </tr>
                  <tr>
                    <td>Constant speed</td>
                    <td>{cycleResult.profile.const_time_s}</td>
                    <td>{cycleResult.profile.const_distance_m}</td>
                  </tr>
                  <tr>
                    <td>Deceleration</td>
                    <td>{cycleResult.profile.decel_time_s}</td>
                    <td>{cycleResult.profile.decel_distance_m}</td>
                  </tr>
                  <tr>
                    <td>Rest (t_off)</td>
                    <td>{cycleResult.regime.off_time_s}</td>
                    <td>—</td>
                  </tr>
                </tbody>
              </table>

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
                  <tr>
                    <td>Motion profile</td>
                    <td>{cycleResult.profile.is_triangular ? 'triangular' : 'trapezoidal'}</td>
                    <td>
                      <code>{cycleResult.profile.formula_id}</code>
                    </td>
                    <td>{cycleResult.profile.standard_refs.join(', ')}</td>
                    <td>{cycleResult.profile.assumptions.join('; ')}</td>
                  </tr>
                  <tr>
                    <td>Duty regime</td>
                    <td>
                      {cycleResult.regime.duty_factor_pct}% ED, {cycleResult.regime.starts_per_hour}
                      /h
                    </td>
                    <td>
                      <code>{cycleResult.regime.formula_id}</code>
                    </td>
                    <td>{cycleResult.regime.standard_refs.join(', ')}</td>
                    <td>{cycleResult.regime.assumptions.join('; ')}</td>
                  </tr>
                  <tr>
                    <td>Deceleration torque</td>
                    <td>
                      {cycleResult.decel_torque.value_nm} N*m
                      {cycleResult.decel_torque.is_regenerative && ' (regenerative)'}
                    </td>
                    <td>
                      <code>{cycleResult.decel_torque.formula_id}</code>
                    </td>
                    <td>{cycleResult.decel_torque.standard_refs.join(', ')}</td>
                    <td>{cycleResult.decel_torque.assumptions.join('; ')}</td>
                  </tr>
                  <tr>
                    <td>RMS torque</td>
                    <td>{cycleResult.rms_torque.value} N*m</td>
                    <td>
                      <code>{cycleResult.rms_torque.formula_id}</code>
                    </td>
                    <td>{cycleResult.rms_torque.standard_refs.join(', ')}</td>
                    <td>{cycleResult.rms_torque.assumptions.join('; ')}</td>
                  </tr>
                  <tr>
                    <td>Energy per cycle / hour</td>
                    <td>
                      {cycleResult.energy.energy_per_cycle_j} J /{' '}
                      {cycleResult.energy.energy_per_hour_j} J
                    </td>
                    <td>
                      <code>{cycleResult.energy.formula_id}</code>
                    </td>
                    <td>{cycleResult.energy.standard_refs.join(', ')}</td>
                    <td>{cycleResult.energy.assumptions.join('; ')}</td>
                  </tr>
                </tbody>
              </table>

              {cycleResult.mechanism_group_check.mechanism_group && (
                <p className="subtitle">
                  Mechanism group {cycleResult.mechanism_group_check.mechanism_group}:{' '}
                  {cycleResult.mechanism_group_check.note}
                </p>
              )}
            </section>

            <section className="candidate">
              <h2>Candidate validation (Modules 5-6 — MOTOR / DRIVE)</h2>
              <p className="subtitle">
                Enter the nameplate data of a motor (and optionally a drive) you are
                considering. <strong>The system validates the candidate you propose —
                it never selects or recommends equipment from a catalog.</strong>
              </p>

              <form onSubmit={handleValidateSubmit} className="form">
                <label className="field">
                  <span>
                    Rated power <em>(kW)</em>
                  </span>
                  <input
                    type="number"
                    step="0.1"
                    value={motor.rated_power_kw}
                    onChange={(e) =>
                      setMotor((prev) => ({ ...prev, rated_power_kw: Number(e.target.value) }))
                    }
                    required
                  />
                </label>
                <label className="field">
                  <span>
                    Rated speed <em>(rpm)</em>
                  </span>
                  <input
                    type="number"
                    step="1"
                    value={motor.rated_speed_rpm}
                    onChange={(e) =>
                      setMotor((prev) => ({ ...prev, rated_speed_rpm: Number(e.target.value) }))
                    }
                    required
                  />
                </label>
                <label className="field">
                  <span>
                    Rated voltage <em>(V)</em>
                  </span>
                  <input
                    type="number"
                    step="1"
                    value={motor.rated_voltage_v}
                    onChange={(e) =>
                      setMotor((prev) => ({ ...prev, rated_voltage_v: Number(e.target.value) }))
                    }
                    required
                  />
                </label>
                <label className="field">
                  <span>
                    Power factor cos(phi) <em>(0-1)</em>
                  </span>
                  <input
                    type="number"
                    step="0.01"
                    value={motor.power_factor}
                    onChange={(e) =>
                      setMotor((prev) => ({ ...prev, power_factor: Number(e.target.value) }))
                    }
                    required
                  />
                </label>
                <label className="field">
                  <span>
                    Efficiency <em>(0-1)</em>
                  </span>
                  <input
                    type="number"
                    step="0.01"
                    value={motor.efficiency}
                    onChange={(e) =>
                      setMotor((prev) => ({ ...prev, efficiency: Number(e.target.value) }))
                    }
                    required
                  />
                </label>
                <label className="field">
                  <span>
                    Nameplate frequency <em>(Hz)</em>
                  </span>
                  <input
                    type="number"
                    step="1"
                    value={motor.nameplate_frequency_hz}
                    onChange={(e) =>
                      setMotor((prev) => ({
                        ...prev,
                        nameplate_frequency_hz: Number(e.target.value),
                      }))
                    }
                    required
                  />
                </label>
                <label className="field">
                  <span>
                    Target mains frequency <em>(Hz)</em>
                  </span>
                  <input
                    type="number"
                    step="1"
                    value={motor.motor_target_frequency_hz}
                    onChange={(e) =>
                      setMotor((prev) => ({
                        ...prev,
                        motor_target_frequency_hz: Number(e.target.value),
                      }))
                    }
                    required
                  />
                </label>

                <label className="field">
                  <span>Breakdown / max mechanical torque input</span>
                  <select
                    value={motor.torqueInputMode}
                    onChange={(e) =>
                      setMotor((prev) => ({
                        ...prev,
                        torqueInputMode: e.target.value as TorqueInputMode,
                      }))
                    }
                  >
                    <option value="pu">Multiple of rated torque (pu)</option>
                    <option value="nm">Absolute value (N*m)</option>
                  </select>
                </label>
                <label className="field">
                  <span>
                    Breakdown torque{' '}
                    <em>{motor.torqueInputMode === 'pu' ? '(x rated)' : '(N*m)'}</em>
                  </span>
                  <input
                    type="number"
                    step="0.1"
                    value={motor.breakdown_torque_value}
                    onChange={(e) =>
                      setMotor((prev) => ({
                        ...prev,
                        breakdown_torque_value: Number(e.target.value),
                      }))
                    }
                    required
                  />
                </label>
                <label className="field">
                  <span>
                    Max mechanical torque{' '}
                    <em>{motor.torqueInputMode === 'pu' ? '(x rated)' : '(N*m)'}</em>
                  </span>
                  <input
                    type="number"
                    step="0.1"
                    value={motor.max_mechanical_torque_value}
                    onChange={(e) =>
                      setMotor((prev) => ({
                        ...prev,
                        max_mechanical_torque_value: Number(e.target.value),
                      }))
                    }
                    required
                  />
                </label>
                <label className="field">
                  <span>
                    No-load current I_0{' '}
                    <em>(A, optional — estimated via sin(phi) if blank)</em>
                  </span>
                  <input
                    type="number"
                    step="0.1"
                    value={motor.no_load_current_a}
                    onChange={(e) =>
                      setMotor((prev) => ({ ...prev, no_load_current_a: e.target.value }))
                    }
                  />
                </label>

                <label className="field">
                  <span>
                    <input
                      type="checkbox"
                      checked={drive.enabled}
                      onChange={(e) =>
                        setDrive((prev) => ({ ...prev, enabled: e.target.checked }))
                      }
                    />{' '}
                    Include a drive candidate
                  </span>
                </label>

                {drive.enabled && (
                  <>
                    <label className="field">
                      <span>
                        Drive rated current <em>(A)</em>
                      </span>
                      <input
                        type="number"
                        step="0.1"
                        value={drive.rated_current_a}
                        onChange={(e) =>
                          setDrive((prev) => ({
                            ...prev,
                            rated_current_a: Number(e.target.value),
                          }))
                        }
                        required
                      />
                    </label>
                    <label className="field">
                      <span>
                        Overload factor <em>(x rated)</em>
                      </span>
                      <input
                        type="number"
                        step="0.1"
                        value={drive.overload_factor}
                        onChange={(e) =>
                          setDrive((prev) => ({
                            ...prev,
                            overload_factor: Number(e.target.value),
                          }))
                        }
                        required
                      />
                    </label>
                    <label className="field">
                      <span>
                        Overload duration <em>(s)</em>
                      </span>
                      <input
                        type="number"
                        step="1"
                        value={drive.overload_duration_s}
                        onChange={(e) =>
                          setDrive((prev) => ({
                            ...prev,
                            overload_duration_s: Number(e.target.value),
                          }))
                        }
                        required
                      />
                    </label>
                    <label className="field">
                      <span>
                        Drive rated voltage <em>(V)</em>
                      </span>
                      <input
                        type="number"
                        step="1"
                        value={drive.rated_voltage_v}
                        onChange={(e) =>
                          setDrive((prev) => ({
                            ...prev,
                            rated_voltage_v: Number(e.target.value),
                          }))
                        }
                        required
                      />
                    </label>
                  </>
                )}

                <button type="submit" disabled={validationLoading}>
                  {validationLoading ? 'Validating…' : 'Validate candidate'}
                </button>
              </form>

              {validationError && <p className="error">{validationError}</p>}

              {validation && (
                <section className="result">
                  <h3>Validation result</h3>

                  <p
                    className={
                      validation.motor_passed &&
                      (validation.drive_passed === null || validation.drive_passed)
                        ? 'verdict-banner pass'
                        : 'verdict-banner fail'
                    }
                  >
                    {validation.motor_passed &&
                    (validation.drive_passed === null || validation.drive_passed)
                      ? 'This candidate meets all validated conditions.'
                      : 'This candidate does NOT meet all validated conditions.'}
                  </p>

                  <h4>Motor conditions</h4>
                  <table>
                    <thead>
                      <tr>
                        <th>Condition</th>
                        <th>Required</th>
                        <th>Available</th>
                        <th>Margin</th>
                        <th>Verdict</th>
                        <th>Formula ID</th>
                      </tr>
                    </thead>
                    <tbody>
                      {validation.motor_conditions.map((c) => (
                        <tr key={c.formula_id}>
                          <td>{c.label}</td>
                          <td>{c.required_value}</td>
                          <td>{c.available_value}</td>
                          <td>{(c.margin * 100).toFixed(1)}%</td>
                          <td>
                            <span className={`verdict ${c.verdict}`}>{c.verdict}</span>
                          </td>
                          <td>
                            <code>{c.formula_id}</code>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>

                  {validation.drive_conditions && (
                    <>
                      <h4>Drive conditions</h4>
                      <table>
                        <thead>
                          <tr>
                            <th>Condition</th>
                            <th>Required</th>
                            <th>Available</th>
                            <th>Margin</th>
                            <th>Verdict</th>
                            <th>Formula ID</th>
                          </tr>
                        </thead>
                        <tbody>
                          {validation.drive_conditions.map((c) => (
                            <tr key={c.formula_id}>
                              <td>{c.label}</td>
                              <td>{c.required_value}</td>
                              <td>{c.available_value}</td>
                              <td>{(c.margin * 100).toFixed(1)}%</td>
                              <td>
                                <span className={`verdict ${c.verdict}`}>{c.verdict}</span>
                              </td>
                              <td>
                                <code>{c.formula_id}</code>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </>
                  )}
                </section>
              )}
            </section>
            </>
          )}
        </section>
      )}

        <SavePanel user={user} calculationInput={lastValidatedInput} />
      </main>

      <footer className="app-footer">
        Manufacturer-neutral · Runs entirely on your own infrastructure · No tracking, no
        telemetry.
      </footer>
    </div>
  )
}

export default App
