# Duty Cycle Model

> **Role of this document.** Engineering specification of the mechanism duty cycle. It is the basis for three mission deliverables: **thermal analysis** (RMS torque/current), **start/stop analysis**, and **energy consumption estimation**. It replaces the magic constant `0.1` from the original code with an explicit, parameterized, versioned model. It lives in `domain/calc/cycle/`.

---

## 1. Why an explicit model

The original code modeled the cycle with a single factor `0.1` (10% of the travel time assigned to an initial phase) buried inside the RMS formula. That is opaque and does not allow:

- declaring the real **cyclic duration factor** (%ED) of the mechanism,
- counting **starts per hour** (key for motor heating),
- distinguishing motoring phases from regenerative ones (for energy and braking),
- or justifying the cycle against a standard.

The model below makes the cycle a **first-class data object**: it is defined once, and from it are derived the times, energies, and RMS values that feed the rest of the calculation engine.

---

## 2. Normative framework

| Standard | What it contributes to the model |
|---|---|
| **ISO 4301-1** / **FEM 1.001** | Mechanism groups (M1–M8), load spectrum, total utilization time, cyclic duration factor. |
| **FEM 9.511** | Classification of drive mechanisms; basis for %ED and starts/hour. |
| **IEC 60034-1** | Duty types S1–S10 (continuous, intermittent periodic, with starts…), motor thermal class. |
| **CMAA 70/74** | Equivalent classification for overhead cranes (future support). |

These parameters enter as a **sizing policy** (a dataset abstracted in `domain/standards/`), never hardcoded.

---

## 3. Key concepts

- **Cyclic duration factor, %ED** (Einschaltdauer): fraction of the cycle time during which the motor is running.
  $$\%ED = \frac{t_{on}}{t_{on} + t_{off}}\times 100$$
  Typical standardized values: 15, 25, 40, 60, 100%. Determines the admissible heating.

- **Starts per hour, `z_h`**: number of accelerations per hour. Every start implies a current peak (`I_acc`), so heating grows with `z_h`. FEM/ISO groups define limits (e.g. 150, 300, 600 starts/h).

- **Mechanism group** (M1–M8): combines load spectrum and total usage duration ⇒ service factor applied to the sizing.

- **Standstill cooling factor, `k_f`**: self-ventilated motors cool worse at low/zero speed; rest time counts only partially in the thermal balance. Input parameter (conservative by default).

---

## 4. Motion profile (trapezoidal / triangular)

An elementary movement (a travel or a hoisting of distance `d`) is modeled with a **trapezoidal velocity profile**: acceleration → constant speed → deceleration, followed by a rest period `t_off`.

```
 v │        ______________
   │       /              \
   │      /                \
   │     /                  \
   │    /                    \
   └───┴──────┴──────────────┴──────┴────► t
       t_a       t_c          t_d    t_off
     (accel)  (constant)    (decel)  (rest)
```

### 4.1 Acceleration phase
$$a = \frac{v}{t_a},\qquad t_a = t_{ramp},\qquad d_a = \tfrac{1}{2}\,v\,t_a$$

### 4.2 Deceleration phase (symmetric by default; independent `t_d` if defined)
$$d_d = \tfrac{1}{2}\,v\,t_d$$

### 4.3 Constant-speed phase
$$d_c = d - d_a - d_d,\qquad t_c = \frac{d_c}{v}$$

### 4.4 Degeneration to a triangular profile
If `d < d_a + d_d`, the movement **never reaches** the nominal speed `v`. Then:
$$v_{peak} = \sqrt{a\cdot d},\qquad t_a = t_d = \sqrt{\frac{d}{a}},\qquad t_c = 0$$
The model must detect this case and switch automatically (mandatory validation: `t_c ≥ 0`).

### 4.5 Cycle time and rest
$$t_{on} = t_a + t_c + t_d,\qquad t_{cycle} = t_{on} + t_{off}$$
`t_off` is derived from one of two equivalent inputs (the user chooses):
- from the **target %ED**: `t_off = t_on·(100/%ED − 1)`, or
- from the **starts/hour**: `t_cycle = 3600 / z_h ⇒ t_off = t_cycle − t_on`.

> **This replaces the original `0.1`.** Instead of a fixed fraction, the duration of each phase comes from the physics of the movement (`v`, `a`, `d`) and the declared duty regime (%ED or starts/hour).

---

## 5. Torque per phase (input to the thermal RMS)

Each phase is associated with the motor torque already calculated in the mechanics modules:

| Phase | Associated torque | Notes |
|---|---|---|
| Acceleration (`t_a`) | `T_acc = T_ss + T_dyn` | peak torque and current |
| Constant (`t_c`) | `T_ss` | steady state |
| Deceleration (`t_d`) | `T_dec` | may be **regenerative** (negative sign) |
| Rest (`t_off`) | `0` | contributes to cooling (see `k_f`) |

**Regenerative deceleration:** in horizontal travel and in lowering, the braking phase usually returns energy. The deceleration torque is
`T_dec = T_dyn − T_ss` (travel) — it may come out negative, which indicates regenerative braking and **sizes the braking resistor** (a pending item from the original `To_do.txt`). The sign must be preserved (no `abs`).

---

## 6. Model outputs

### 6.1 RMS torque (thermal)
$$T_{rms} = \sqrt{\dfrac{T_{acc}^2\,t_a + T_{ss}^2\,t_c + T_{dec}^2\,t_d}{t_a + t_c + t_d + k_f\,t_{off}}}$$

- The `t_off` in the denominator (weighted by `k_f ∈ [0,1]`) models cooling during rest. `k_f = 1` ⇒ full cooling (motor with independent forced ventilation); `k_f < 1` ⇒ self-ventilated. An **explicit improvement** over the original, which ignored rest.
- Motor validation criterion: `T_r ≥ margin · T_rms` (margin from the sizing policy).

### 6.2 RMS current (drive thermal)
$$I_{rms} = \sqrt{\dfrac{I_{acc}^2\,t_a + I_{ss}^2\,t_c + I_{dec}^2\,t_d}{t_a + t_c + t_d + k_f\,t_{off}}}$$
Feeds the criterion `I_r,drive ≥ margin · I_rms`.

### 6.3 Start/stop analysis
- **Effective starts/hour** vs. the mechanism group limit (FEM/ISO): validate `z_h ≤ z_h,max`.
- **Energy dissipated per start** (for thermal verification of the motor and the braking resistor).
- Brake switching frequency (FEM 1.001 reference: brake torque ≥ 1.6× static load torque).

### 6.4 Energy consumption estimation
Energy per phase = average power × time. Net energy per cycle adds motoring phases and **subtracts** regenerative ones:
$$E_{cycle} = \sum_{phase} P_{phase}\cdot t_{phase},\qquad P_{phase} = \frac{T_{phase}\cdot \omega_{phase}}{\eta_{system}}\ \text{(motoring)} \quad\text{or}\quad T_{phase}\cdot\omega_{phase}\cdot\eta\ \text{(regenerative)}$$
$$E_{hour} = E_{cycle}\cdot z_h$$
Efficiency enters the numerator or denominator depending on the direction of the power flow (same criterion as in hoisting). This allows reporting estimated consumption and recoverable energy.

---

## 7. Input parameters (typed)

```python
@dataclass(frozen=True)
class DutyCycleInput:
    distance_m: float          # movement travel distance
    velocity_ms: float         # nominal speed
    accel_time_s: float        # acceleration ramp time
    decel_time_s: float        # deceleration ramp time (defaults to accel_time_s)
    # Duty regime: exactly ONE of the two is defined
    duty_factor_pct: float | None = None   # target %ED
    starts_per_hour: float | None = None   # starts/hour
    cooling_factor: float = 0.5            # k_f, standstill cooling (conservative default)
    mechanism_group: str | None = None     # e.g. "M5" (ISO 4301-1) — sizing policy
```

**Output** (`DutyCycleResult`): times per phase, `t_on`, `t_off`, resulting `%ED`, `z_h`, profile flags (trapezoidal/triangular), and the aggregates consumed by the thermal/energy modules. Like every core formula, it carries `formula_id`, `assumptions`, and `standard_refs`.

---

## 8. Identifier and version

- `CYCLE.PROFILE.v1` — calculation of times and distances per phase (trapezoidal/triangular).
- `CYCLE.ED.v1` — derivation of `t_off`, %ED, and starts/hour.
- `CYCLE.Trms.v1` / `CYCLE.Irms.v1` — thermal RMS with cooling factor.
- `CYCLE.ENERGY.v1` — energy per cycle/hour with regeneration.

Physics changes ⇒ new version; published versions are never modified (reproducibility).

---

## 9. Validations and edge cases

- `t_c ≥ 0` — otherwise, switch to the triangular profile (short movement that never reaches `v`).
- Exactly one of `duty_factor_pct` / `starts_per_hour` must be present.
- `0 < %ED ≤ 100`; `k_f ∈ [0, 1]`; times and speed `> 0`.
- If `T_dec < 0` ⇒ flag regenerative operation and expose recoverable energy + braking resistor requirement.
- Resulting `z_h` compared against the limit of the declared mechanism group.
- All rounding explicit and documented in the formula sheet.

---

## 10. How it fits into the calculation engine

```
Mechanics (T_ss, T_dyn, T_acc, N_c)
        │
        ▼
Duty cycle  ──►  phase profile + %ED + z_h
        │                     │
        ├──► T_rms, I_rms  ──► Thermal analysis  ──► motor/drive validation
        ├──► starts/h      ──► Start/stop analysis + brake
        └──► E_cycle,E_hour──► Energy consumption estimation
```

The cycle is the hinge between the mechanics (what torque is needed) and the service analyses (whether the equipment holds up thermally, how many starts it withstands, and how much energy it consumes/recovers). That is why it is built right after the mechanics and before the final thermal sizing.
