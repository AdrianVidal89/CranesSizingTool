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

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export async function calculateTravelRequirement(
  input: TravelRequirementInput,
): Promise<TravelRequirementResult> {
  const response = await fetch(`${API_BASE_URL}/api/calc/travel`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })

  if (!response.ok) {
    const detail = await response.text()
    throw new Error(`Calculation failed (${response.status}): ${detail}`)
  }

  return response.json() as Promise<TravelRequirementResult>
}
