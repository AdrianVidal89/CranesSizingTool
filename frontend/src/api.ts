export interface FormulaOutput {
  label: string
  value: number
  unit: string
  formula_id: string
  assumptions: string[]
  standard_refs: string[]
}

export interface TravelRequirementResult {
  required_torque_nm: number
  required_speed_rpm: number
  steady_torque_nm: number
  dynamic_torque_nm: number
  components: FormulaOutput[]
}

export interface TravelRequirementInput {
  mass_dead_kg: number
  mass_load_kg: number
  mass_tool_kg: number
  velocity_ms: number
  accel_time_s: number
  wheel_diameter_m: number
  gear_ratio: number
  efficiency: number
  motors_count: number
  rolling_coeff: number
}

export interface DutyCycleInput extends TravelRequirementInput {
  distance_m: number
  decel_time_s: number | null
  duty_factor_pct: number | null
  starts_per_hour: number | null
  cooling_factor: number
  mechanism_group: string | null
}

interface FormulaFields {
  formula_id: string
  assumptions: string[]
  standard_refs: string[]
}

export interface MotionProfile extends FormulaFields {
  accel_time_s: number
  const_time_s: number
  decel_time_s: number
  accel_distance_m: number
  const_distance_m: number
  decel_distance_m: number
  peak_velocity_ms: number
  is_triangular: boolean
}

export interface DutyRegime extends FormulaFields {
  on_time_s: number
  off_time_s: number
  cycle_time_s: number
  duty_factor_pct: number
  starts_per_hour: number
}

export interface DecelTorque extends FormulaFields {
  value_nm: number
  is_regenerative: boolean
}

export interface ThermalRms extends FormulaFields {
  value: number
}

export interface PhaseEnergy {
  label: string
  energy_j: number
  is_regenerative: boolean
}

export interface EnergyCycle extends FormulaFields {
  energy_per_cycle_j: number
  energy_per_hour_j: number
  phases: PhaseEnergy[]
  has_regenerative_phase: boolean
}

export interface MechanismGroupCheck {
  status: 'ok' | 'exceeded' | 'not_available'
  mechanism_group: string | null
  starts_per_hour_limit: number | null
  note: string
}

export interface DutyCycleResult {
  required_torque_nm: number
  required_speed_rpm: number
  steady_torque_nm: number
  dynamic_torque_nm: number
  profile: MotionProfile
  regime: DutyRegime
  decel_torque: DecelTorque
  rms_torque: ThermalRms
  energy: EnergyCycle
  mechanism_group_check: MechanismGroupCheck
}

export interface MotorCandidateInput {
  rated_power_kw: number
  rated_speed_rpm: number
  rated_voltage_v: number
  power_factor: number
  efficiency: number
  nameplate_frequency_hz: number
  breakdown_torque_pu: number | null
  breakdown_torque_nm: number | null
  max_mechanical_torque_pu: number | null
  max_mechanical_torque_nm: number | null
  no_load_current_a: number | null
  rotor_inertia_kgm2: number
}

export interface DriveCandidateInput {
  rated_current_a: number
  overload_factor: number
  overload_duration_s: number
  rated_voltage_v: number
}

export interface ValidateCandidateInput extends DutyCycleInput {
  motor: MotorCandidateInput
  motor_target_frequency_hz: number
  drive: DriveCandidateInput | null
}

export interface ConditionResult {
  label: string
  verdict: 'pass' | 'fail'
  required_value: number
  available_value: number
  margin: number
  formula_id: string
  assumptions: string[]
  standard_refs: string[]
}

export interface ResolvedMotor {
  rated_torque_nm: number
  rated_speed_rpm: number
  rated_current_a: number
  breakdown_torque_nm: number
  max_mechanical_torque_nm: number
}

export interface ValidateCandidateResult {
  requirement: DutyCycleResult
  resolved_motor: ResolvedMotor
  motor_conditions: ConditionResult[]
  motor_passed: boolean
  drive_conditions: ConditionResult[] | null
  drive_passed: boolean | null
  rms_current_a: number | null
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

async function postJson<TResult>(path: string, body: unknown): Promise<TResult> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })

  if (!response.ok) {
    const detail = await response.text()
    throw new Error(`Calculation failed (${response.status}): ${detail}`)
  }

  return response.json() as Promise<TResult>
}

export function calculateTravelRequirement(
  input: TravelRequirementInput,
): Promise<TravelRequirementResult> {
  return postJson<TravelRequirementResult>('/api/calc/travel', input)
}

export function calculateDutyCycle(input: DutyCycleInput): Promise<DutyCycleResult> {
  return postJson<DutyCycleResult>('/api/calc/duty-cycle', input)
}

export function validateCandidate(
  input: ValidateCandidateInput,
): Promise<ValidateCandidateResult> {
  return postJson<ValidateCandidateResult>('/api/calc/validate-candidate', input)
}
