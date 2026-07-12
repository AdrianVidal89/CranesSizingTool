import type { ReactNode } from 'react'

import type { ParamInfo } from './InfoTip'

/* Parameter explanations shown by the "i" InfoTip next to each form field,
 * written for users who are not drive-sizing specialists. Illustrations are
 * small inline SVGs (currentColor strokes so they follow the theme; no
 * external assets — privacy rule: nothing is fetched from third parties). */

const FIG = {
  width: 230,
  height: 120,
  stroke: 'currentColor',
  strokeWidth: 1.4,
  fontSize: 9.5,
}

function Fig({ children }: { children: ReactNode }) {
  return (
    <svg
      viewBox={`0 0 ${FIG.width} ${FIG.height}`}
      width="100%"
      role="img"
      fill="none"
      stroke={FIG.stroke}
      strokeWidth={FIG.strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      style={{ maxWidth: FIG.width }}
    >
      {children}
    </svg>
  )
}

function Label({ x, y, children, anchor = 'start' }: {
  x: number
  y: number
  children: ReactNode
  anchor?: 'start' | 'middle' | 'end'
}) {
  return (
    <text
      x={x}
      y={y}
      fontSize={FIG.fontSize}
      fill="currentColor"
      stroke="none"
      textAnchor={anchor}
      fontFamily="inherit"
    >
      {children}
    </text>
  )
}

/** Overhead crane sketch: bridge, trolley, hook and load — which mass is which. */
const massesFigure = (
  <Fig>
    {/* runway + bridge */}
    <path d="M14 22h202" />
    <path d="M14 16v12M216 16v12" />
    {/* trolley */}
    <rect x={92} y={24} width={44} height={16} rx={2} />
    <circle cx={102} cy={26} r={3} />
    <circle cx={126} cy={26} r={3} />
    {/* hoist rope + hook */}
    <path d="M114 40v28m-4 0h8m-4 0v6c0 5 7 5 7 1" />
    {/* spreader / tool */}
    <rect x={98} y={80} width={32} height={7} rx={1.5} />
    {/* load */}
    <rect x={94} y={92} width={40} height={20} rx={2} />
    <Label x={16} y={12}>bridge + trolley = dead mass</Label>
    <Label x={140} y={86}>tool / spreader</Label>
    <Label x={140} y={106}>load (SWL)</Label>
  </Fig>
)

/** Speed-vs-time trapezoid marking the acceleration ramp t_r and speed v. */
const rampFigure = (
  <Fig>
    <path d="M18 104h196M18 104V16" />
    <path d="M18 104 62 34h84l44 70" strokeWidth={1.8} />
    <path d="M18 34h44" strokeDasharray="3 3" />
    <path d="M62 104V34" strokeDasharray="3 3" />
    <Label x={10} y={32} anchor="start">v</Label>
    <Label x={38} y={116} anchor="middle">t_r</Label>
    <Label x={104} y={30} anchor="middle">constant speed</Label>
    <Label x={210} y={116} anchor="end">t</Label>
  </Fig>
)

/** Travel wheel on a rail with its diameter marked. */
const wheelFigure = (
  <Fig>
    <path d="M20 96h190" strokeWidth={2} />
    <circle cx={115} cy={62} r={34} />
    <circle cx={115} cy={62} r={4} />
    <path d="M115 28v68" strokeDasharray="3 3" />
    <path d="M115 28l-5 8m5-8 5 8M115 96l-5-8m5 8 5-8" />
    <Label x={126} y={40}>D = wheel diameter</Label>
    <Label x={24} y={90}>rail</Label>
  </Fig>
)

/** Motor + gearbox: the ratio between fast and slow shafts. */
const gearFigure = (
  <Fig>
    <rect x={16} y={44} width={52} height={34} rx={4} />
    <Label x={42} y={64} anchor="middle">motor</Label>
    <path d="M68 61h18" strokeWidth={2} />
    <circle cx={112} cy={61} r={22} />
    <circle cx={148} cy={61} r={11} />
    <path d="M159 61h20" strokeWidth={2} />
    <Label x={112} y={99} anchor="middle">gearbox</Label>
    <Label x={186} y={50}>slow shaft</Label>
    <Label x={186} y={62}>(wheel/drum)</Label>
    <Label x={112} y={22} anchor="middle">i = n_motor / n_out</Label>
  </Fig>
)

/** Hoist drum with reeved rope falls down to the hook. */
const drumFigure = (
  <Fig>
    <rect x={70} y={14} width={90} height={26} rx={13} />
    <path d="M70 27v-6M160 27v-6" />
    <path d="M115 14V4" strokeDasharray="3 3" />
    <Label x={122} y={10}>drum, diameter D</Label>
    {/* two falls to sheave/hook block */}
    <path d="M92 40v52M138 40v52" />
    <circle cx={115} cy={96} r={9} />
    <path d="M92 92c0 8 10 13 23 13s23-5 23-13" />
    <path d="M115 105v5c0 5 8 5 8 1" />
    <Label x={148} y={72}>s = number of</Label>
    <Label x={148} y={84}>rope falls</Label>
    <Label x={60} y={72} anchor="end">rope</Label>
  </Fig>
)

/** Duty cycle: torque blocks with running and rest periods (%ED). */
const dutyFigure = (
  <Fig>
    <path d="M14 100h202M14 100V20" />
    <path d="M14 100V46h56v54M100 100V46h56v54" strokeWidth={1.8} />
    <path d="M14 110h56M100 110h56" />
    <Label x={42} y={40} anchor="middle">running</Label>
    <Label x={85} y={70} anchor="middle">rest</Label>
    <Label x={128} y={40} anchor="middle">running</Label>
    <Label x={210} y={98} anchor="end">t</Label>
    <Label x={14} y={118}>%ED = running time / cycle time</Label>
  </Fig>
)

/** Rotating inertia: motor shaft with a disc. */
const inertiaFigure = (
  <Fig>
    <path d="M26 62h60" strokeWidth={2} />
    <ellipse cx={104} cy={62} rx={12} ry={34} />
    <path d="M104 28c22 0 40 15 40 34" strokeDasharray="3 3" />
    <path d="M144 62l-6-7m6 7-8 2" />
    <path d="M116 62h68" strokeWidth={2} />
    <Label x={30} y={50}>shaft</Label>
    <Label x={150} y={40}>rotation</Label>
    <Label x={104} y={112} anchor="middle">J = resistance to speeding up rotation</Label>
  </Fig>
)

export const PARAM_INFO: Record<string, ParamInfo> = {
  // ---------- Project setup ----------
  setup_hoist: {
    title: 'Hoist movement',
    body:
      'The vertical lifting movement: a motor turns a rope drum that raises and lowers the hook. A crane can have a main hoist and up to two auxiliary hoists, each sized separately.',
    illustration: drumFigure,
  },
  setup_travel: {
    title: 'Travel movement',
    body:
      'A horizontal movement on wheels and rails: the long travel of the bridge/gantry, or the cross travel of the trolley along the bridge. Each travel movement is sized separately.',
    illustration: massesFigure,
  },

  // ---------- Shared masses ----------
  mass_dead_kg: {
    title: 'Dead mass',
    body:
      'The moving structure’s own mass (bridge, gantry or trolley frame) without load or lifting tool. It always moves with the mechanism, so the motor must accelerate it too.',
    illustration: massesFigure,
  },
  mass_load_kg: {
    title: 'Load mass (SWL)',
    body:
      'The Safe Working Load: the heaviest payload the crane is rated to carry on the hook. Found on the crane’s rating plate.',
    illustration: massesFigure,
  },
  mass_tool_kg: {
    title: 'Tool / spreader mass',
    body:
      'The mass of the lifting attachment between hook and load: spreader, grab, magnet, C-hook or hook block. It hangs on the rope even when the crane runs empty.',
    illustration: massesFigure,
  },

  // ---------- Travel mechanics ----------
  travel_velocity_ms: {
    title: 'Travel velocity',
    body:
      'The nominal (steady) horizontal speed of the movement, in metres per second. 1 m/s = 60 m/min. Typical crane travel speeds are 0.3–2 m/s.',
    illustration: rampFigure,
  },
  accel_time_s: {
    title: 'Acceleration ramp time',
    body:
      'How long the drive takes to go from standstill to nominal speed. A shorter ramp needs more torque; a longer ramp is gentler on the structure and the load swing.',
    illustration: rampFigure,
  },
  wheel_diameter_m: {
    title: 'Wheel diameter',
    body:
      'The rolling diameter of the travel wheels on the rail, in metres. Together with the gear ratio it links motor speed to travel speed.',
    illustration: wheelFigure,
  },
  gear_ratio: {
    title: 'Gearbox ratio',
    body:
      'How many turns the motor makes for one turn of the output shaft (wheel or drum). Found on the gearbox nameplate, e.g. i = 20 means the motor spins 20× faster.',
    illustration: gearFigure,
  },
  efficiency: {
    title: 'Mechanical efficiency',
    body:
      'The fraction of motor power that reaches the wheel or drum after gearbox and transmission losses, between 0 and 1. Typical geared transmissions: 0.85–0.95.',
  },
  motors_count: {
    title: 'Number of motors',
    body:
      'How many identical motors drive this movement together (e.g. one at each corner of a gantry). The required torque is shared equally between them.',
  },
  rolling_coeff: {
    title: 'Rolling resistance coefficient',
    body:
      'A dimensionless factor for how much the wheels resist rolling on the rail. Steel wheel on steel rail: about 0.01–0.016 (includes bearing friction in the simple model).',
    illustration: wheelFigure,
  },

  // ---------- Hoist mechanics ----------
  hoist_velocity_ms: {
    title: 'Hoisting speed',
    body:
      'The vertical speed of the hook (not of the rope), in metres per second. 0.2 m/s = 12 m/min. Typical hoisting speeds are 0.05–0.5 m/s.',
    illustration: rampFigure,
  },
  drum_diameter_m: {
    title: 'Drum diameter',
    body:
      'The diameter of the rope drum the hoist rope winds onto, in metres. Together with reeving and gear ratio it links motor speed to hook speed.',
    illustration: drumFigure,
  },
  reeving_factor: {
    title: 'Reeving factor',
    body:
      'The number of rope falls (rope lines) carrying the hook block. With s falls the rope tension is the load weight divided by s, and the rope moves s× faster than the hook.',
    illustration: drumFigure,
  },
  hoist_efficiency: {
    title: 'Mechanical efficiency',
    body:
      'The fraction of motor power that reaches the load after gearbox, drum and reeving losses, between 0 and 1. When lifting, the motor must overcome these losses; when lowering, they help hold the load.',
  },
  motor_inertia_kgm2: {
    title: 'Motor rotor inertia',
    body:
      'The moment of inertia of the motor’s own rotor (from the motor datasheet, in kg·m²). During the ramp, part of the torque is spent just accelerating the rotor itself.',
    illustration: inertiaFigure,
  },
  brake_inertia_kgm2: {
    title: 'Brake inertia',
    body:
      'The moment of inertia of the brake disc or drum mounted on the motor shaft (from the brake datasheet, in kg·m²). Set 0 if unknown or negligible.',
    illustration: inertiaFigure,
  },

  // ---------- Duty cycle ----------
  distance_m: {
    title: 'Distance',
    body:
      'The distance the movement covers in one work cycle (e.g. the typical travel length between pick and place). It sets how long each phase of the motion profile lasts.',
  },
  decel_time_s: {
    title: 'Deceleration ramp time',
    body:
      'How long the drive takes to brake from nominal speed to standstill. Leave blank to use the same value as the acceleration ramp.',
    illustration: rampFigure,
  },
  duty_regime_mode: {
    title: 'Duty regime input',
    body:
      'Choose how to describe how intensively the mechanism works: either the duty factor %ED (share of time running) or the number of starts per hour. The other value is derived.',
    illustration: dutyFigure,
  },
  duty_factor_pct: {
    title: 'Duty factor %ED',
    body:
      'The percentage of cycle time the motor is actually running (the rest is standstill). E.g. 25 %ED means running a quarter of the time. Crane duty classes commonly use 25–60 %ED.',
    illustration: dutyFigure,
  },
  starts_per_hour: {
    title: 'Starts per hour',
    body:
      'How many times per hour the movement starts. Frequent starting heats the motor: each mechanism group (ISO 4301 / FEM) allows a maximum number of starts per hour.',
    illustration: dutyFigure,
  },
  cooling_factor: {
    title: 'Standstill cooling factor',
    body:
      'How well the motor cools while stopped, between 0 and 1. Self-ventilated motors cool poorly at standstill (≈0.3–0.5); force-ventilated motors keep cooling (≈1).',
  },
  mechanism_group: {
    title: 'Mechanism group',
    body:
      'The ISO 4301-1 / FEM classification of the mechanism’s service (M1…M8), from light to heavy duty. If given, the computed starts per hour are checked against the group’s limit.',
  },

  // ---------- Motor candidate ----------
  rated_power_kw: {
    title: 'Rated power',
    body:
      'The continuous mechanical output power on the motor nameplate, in kW. This is a nameplate value from the motor you are proposing — the system validates it, it never picks a motor for you.',
  },
  rated_speed_rpm: {
    title: 'Rated speed',
    body:
      'The shaft speed on the motor nameplate at rated load, in rpm (e.g. 950 rpm for a 6-pole 50 Hz motor). Compared against the speed the mechanism requires.',
  },
  rated_voltage_v: {
    title: 'Rated voltage',
    body: 'The line-to-line supply voltage on the motor nameplate, in volts (e.g. 400 V).',
  },
  power_factor: {
    title: 'Power factor cos φ',
    body:
      'The nameplate cosine of the angle between voltage and current at rated load, between 0 and 1. Used to derive rated current and to estimate the magnetizing current.',
  },
  motor_efficiency: {
    title: 'Motor efficiency',
    body:
      'The nameplate efficiency of the motor at rated load, between 0 and 1 (e.g. 0.87 = 87 %). Not the same as the mechanical efficiency of the transmission.',
  },
  nameplate_frequency_hz: {
    title: 'Nameplate frequency',
    body:
      'The supply frequency the nameplate data refers to (50 or 60 Hz). If your mains differs, the values are rescaled as a documented engineering estimate.',
  },
  target_frequency_hz: {
    title: 'Target mains frequency',
    body:
      'The frequency of the network where the crane will actually operate. If it differs from the nameplate frequency, speed and power are scaled proportionally (torque preserved).',
  },
  torque_input_mode: {
    title: 'Torque input mode',
    body:
      'Motor catalogs state breakdown/maximum torque either as a multiple of rated torque (e.g. 2.5×) or as an absolute value in N·m. Pick the form your datasheet uses.',
  },
  breakdown_torque: {
    title: 'Breakdown torque',
    body:
      'The maximum torque the motor can develop before stalling (pull-out torque). The requirement must stay below it with a safety margin — reaching it means losing control of the load.',
  },
  max_mechanical_torque: {
    title: 'Max mechanical torque',
    body:
      'The highest torque the motor shaft and mechanical parts are rated to transmit, from the datasheet. The total acceleration torque must not exceed it.',
  },
  no_load_current_a: {
    title: 'No-load current I₀',
    body:
      'The current the motor draws spinning with nothing attached — essentially the magnetizing current (typically 20–50 % of rated current). If blank, it is estimated from cos φ.',
  },

  // ---------- Drive candidate ----------
  drive_rated_current_a: {
    title: 'Drive rated current',
    body:
      'The continuous output current of the variable-frequency drive, in amperes, from its nameplate. Must cover the motor’s steady-state current.',
  },
  overload_factor: {
    title: 'Overload factor',
    body:
      'How much current above rated the drive can deliver for a short time, as a multiple (e.g. 1.6 = 160 %). Heavy-duty drives typically allow 1.5–1.6× — check the drive datasheet.',
  },
  overload_duration_s: {
    title: 'Overload duration',
    body:
      'How long the drive can sustain its overload current, in seconds (commonly 60 s). Must be at least as long as the acceleration ramp needs it.',
  },
  drive_rated_voltage_v: {
    title: 'Drive rated voltage',
    body: 'The output voltage class of the drive, in volts. It must match the motor’s rated voltage.',
  },
}
