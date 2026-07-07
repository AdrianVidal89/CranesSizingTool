# Formula Inventory — Crane Calculation Engine

**Source:** `CraneSizing/Math_Version.py` (2021 version, the most mature in the history)
**Purpose:** clean, traceable specification of every equation in the core, to reimplement it in the new backend without carrying over the technical debt of the original code (global state, magic constants, catalog dependency).
**Status of each formula:** marked as ✅ *Correct*, ⚠️ *Correct but improvable*, or ❌ *Has an error — fix*, with the corresponding physical/normative reference.

> **How to read this document.** Each formula carries: (1) the equation as it will be reimplemented, (2) variables with SI units, (3) explicit constants, (4) physical basis / standard reference, and (5) notes from the original version and the corrections detected. Constants and factors that were "hardcoded" in the code are brought into the open here so the engine is auditable and versionable.

---

## 0. Conventions, symbols, and units

All quantities are handled internally in **SI**. Conversions (km→m, min→s, kW→W, °→rad) are done at the input layer, never inside the formulas.

| Symbol | Quantity | SI unit |
|---|---|---|
| `m_load` | Mass of the load (SWL) | kg |
| `m_tool` | Mass of the tool / spreader | kg |
| `m_dead` | Dead mass of the mechanism (gantry/trolley) | kg |
| `m` | Total mass to move | kg |
| `v` | Linear speed of the movement | m/s |
| `a` | Linear acceleration | m/s² |
| `t_r` | Ramp (acceleration) time | s |
| `D_w` | Wheel diameter (travel) / drum diameter (hoist) | m |
| `i` | Gearbox reduction ratio | – |
| `η` | Mechanical efficiency (gearbox + transmission) | – |
| `z` | Number of motors/drives per movement | – |
| `s` | Reeving factor (number of rope falls) | – |
| `μ` | Rolling resistance coefficient | – |
| `θ` | Track inclination angle | rad |
| `N_c` | Required speed at the motor shaft | rpm |
| `T_ss` | Steady-state torque | N·m |
| `T_dyn` | Dynamic (acceleration) torque | N·m |
| `T_acc` | Total torque during acceleration = `T_ss + T_dyn` | N·m |
| `T_rms` | Root-mean-square torque of the cycle | N·m |
| `J` | Moment of inertia | kg·m² |
| `ω` | Angular speed | rad/s |
| `g` | Gravitational acceleration = **9.80665** | m/s² |

**Global physical constant:** `g = 9.80665 m/s²`. *(The code uses `9.81`; fixing the CODATA value is recommended for reproducibility. The difference is <0.04%, but since this is a versioned calculation the constant should be declared once, not scattered across 20 formulas.)*

---

## MODULE 1 — Travel mechanics (Gantry / Trolley)

Applies to horizontal movements on wheels and rail (gantry and trolley). Both share the same model; only the input parameters change.

### 1.1 — Rolling resistance force ✅

$$F_r = \mu \cdot m \cdot g$$

- **Variables:** `m` = (m_dead + m_load + m_tool) [kg]; `μ` [–].
- **Physical basis:** simplified rolling resistance, a force opposing the movement proportional to the normal load. Standard model `F = μ·N` with `N = m·g` on a horizontal track.
- **Reference:** rolling resistance (steel wheel/rail ≈ 0.01–0.016). For cranes, FEM 9.511 / ISO 4301 use a *travel resistance coefficient* that combines rolling + bearing friction.
- **Notes on the original:** ✅ correct. ⚠️ **Recommended improvement:** the code fixes `μ = 0.016` *inside* the `Trolley` function (overwriting the input parameter). It must always be a **validated input parameter**, never hardcoded. Also, the basic model ignores bearing friction and wheel flanges; the full FEM model is:
  $$F_r = \frac{2}{D_w}\left(\mu_L \cdot \frac{d_L}{2} + f\right)\cdot c \cdot m \cdot g$$
  where `d_L` = bearing journal diameter, `f` = rolling lever arm [m], `c` = flange friction factor (≈1.1–1.5). Recommendation: keep the simple model as *level 1* and the full FEM model as an optional *level 2*, both versioned.

### 1.2 — Required speed at the motor shaft ✅

$$N_c = \frac{v}{\pi \cdot D_w}\cdot i \cdot 60$$

*(in rpm; the code uses `v` in m/min and `π ≈ 3.1416`, so its factor 60 is implicit in the units)*

- **Physical basis:** the wheel speed `n_wheel = v/(π·D_w)` multiplied by the reduction ratio gives the motor speed.
- **Notes:** ✅ correct. ⚠️ Replace `3.1416` with `math.pi`.

### 1.3 — Steady-state torque (horizontal track) ✅

$$T_{ss} = \frac{F_r \cdot D_w}{2 \cdot z \cdot i \cdot \eta}$$

- **Variables:** `η` is the gearbox efficiency (the code calls it `r`, typically 0.9).
- **Physical basis:** torque at the wheel = `F_r · (D_w/2)`, referred to the motor shaft by dividing by `i`, shared among `z` motors, and **divided** by `η` because in traction (motoring) the motor must overcome the losses → it needs *more* torque.
- **Notes:** ✅ correct for the motoring case. ⚠️ **Inconsistency:** in `Trolley` the code writes a fixed `0.9` instead of the efficiency variable `rt` that `Gantry` does use. Unify into a single `η` parameter.

### 1.4 — Dynamic (acceleration) torque ✅

$$T_{dyn} = \frac{m \cdot a \cdot D_w}{2 \cdot z \cdot i \cdot \eta}, \qquad a = \frac{v}{t_r}$$

- **Physical basis:** Newton's second law for the translated mass, referred to the motor shaft. `a = v/t_r` is the acceleration during the ramp.
- **Notes:** ✅ correct. The original additionally builds a **torque vs. ramp time vector** (`np.arange(0.01, t_r+2, 0.01)`) for plotting; that is presentation, not calculation — separate it from the core. ⚠️ **Physics improvement:** this dynamic torque only considers the inertia of the translated mass; it **omits the rotor inertia of the motor + gearbox + wheels**. For low-inertia travel this is acceptable, but for rigorous sizing add `T_dyn_rotor = (J_motor + J_gearbox)·α`, with `α = ω_motor/t_r`. See Module 2, which does include it.

### 1.5 — Total torque during acceleration ✅

$$T_{acc} = T_{ss} + T_{dyn}$$

- **Physical basis:** the motor must simultaneously overcome the resistance (T_ss) and accelerate the mass (T_dyn). This is the sizing torque. ✅ correct.

---

## MODULE 2 — Hoisting mechanics (Hoist)

### 2.1 — Static hoisting torque ⚠️

$$T_{ss,h} = \frac{m_h \cdot g \cdot (D_w/2)}{s \cdot i \cdot \eta}$$

- **Variables:** `m_h` = (m_load + m_tool) [kg]; `s` = reeving factor; `D_w` = drum diameter.
- **Physical basis:** force at the hook `m_h·g`, shared among `s` falls → rope tension `m_h·g/s`; torque at the drum = tension · radius; referred to the motor by dividing by `i·η`.
- **Notes:** ✅ structure correct and confirmed by practice (tension = W/n falls; torque = tension·radius; referred to the motor with `/i` and, when **lifting**, `/η`). ⚠️ **Critical sign/efficiency improvement:** when **lifting**, `η` goes in the denominator (it works against you); when **lowering**, `η` goes in the numerator (friction helps hold the load):
  $$T_{ss,h}^{\text{lowering}} = \frac{m_h \cdot g \cdot (D_w/2) \cdot \eta}{s \cdot i}$$
  The original code **only models lifting**. For "start/stop analysis" and braking, both directions must be modeled.

### 2.2 — Required motor speed ✅

$$N_c = \frac{v \cdot s}{\pi \cdot D_w}\cdot i \cdot 60 \quad\text{[rpm]}$$

- **Physical basis:** hook speed `v`; linear rope speed at the drum = `v·s`; drum angular speed `ω = v·s/(D_w/2)`; referred to the motor with `·i`.
- **Notes:** ✅ correct (the code expresses it via `ω`).

### 2.3 — Dynamic torque of the motor+brake assembly ✅

$$T_{dyn,rot} = (J_{motor} + J_{brake})\cdot \frac{\omega_{motor}}{t_r}$$

- **Physical basis:** torque to accelerate the assembly's own rotor inertias. `α = ω/t_r`. ✅ correct.

### 2.4 — Dynamic torque of the hoisted load ❌ **FIX**

**Original (incorrect):**
$$J_{load}^{orig} = \frac{1}{4}\cdot\frac{1}{2}\cdot m_h \cdot \left(\frac{D_w}{2}\right)^2 \Big/ i^2$$

- **Problem:** the hanging load is a **translating mass**, not a spinning cylinder. Its equivalent inertia reduced to the drum is `m·r_effective²`, **not** `(1/2)·m·r²` (solid cylinder formula), and it does **not** carry the extra `1/4` factor. The reeving factor `s²` is also missing.
- **Physically correct formula** (inertia of a translated mass, reduced to the motor shaft):
  $$J_{load} = \frac{m_h \cdot (D_w/2)^2}{s^2 \cdot i^2}$$
  equivalent to `J_load = m_h · r_ef²` with `r_ef = (D_w/2)/(s·i)`.
- **Reference:** reflected load inertia = load inertia / (ratio²); a translating mass reflects as `m·r²`. Confirmed in motor sizing literature (reflected load inertia) and in crane winch dynamics models (`J·d²θ/dt² = T − m·R/(n·k)·(...)`).
- **Impact:** the error makes the dynamic torque of the load come out **underestimated** by a factor of ~`(2/s²)` versus the physical value (e.g. with `s`=2 the original gives 1/8·m·r² versus the correct 1/4·m·r² → underestimation by a factor of 2). **Fixing this is important for sizing safety.**

### 2.5 — Total hoisting torque during acceleration ✅ (after fixing 2.4)

$$T_{acc,h} = T_{ss,h} + T_{dyn,rot} + T_{dyn,load}$$

- **Physical basis:** sum of the static torque (holding) + accelerating the rotor inertias + accelerating the load. ✅ structure correct.

---

## MODULE 3 — Forces on an incline / slope ⚠️

For tracks inclined at an angle `θ`:

$$F = m\cdot g\cdot\sin\theta \;-\; \mu\cdot m\cdot g\cdot\cos\theta$$
$$T_{ss} = \frac{F \cdot v}{\omega \cdot z \cdot i},\qquad \omega = \frac{(N_c/60)\cdot 2\pi}{i}$$

- **Physical basis:** gravitational component along the slope (`m·g·sinθ`) minus/plus the rolling resistance on the normal component (`μ·m·g·cosθ`). Torque is obtained through the power balance `P = F·v = T·ω`.
- **Notes:** ⚠️ The original takes `abs(F)` when `F<0`, which **loses the sign** and with it the information of whether the movement is *motoring* (climbing the slope) or *regenerative* (descending, gravity helps). For sizing the drive and the braking resistor (which appears explicitly in the original `To_do.txt` as pending) **the sign must be preserved**: `F<0` ⇒ regenerative operation ⇒ sizes the braking resistor, not the motor torque.
- ⚠️ The torque "range" (`θ±θ`) that the original computes to produce an interval is a non-rigorous artifice; better to explicitly calculate the declared worst-case favorable and unfavorable slope cases as inputs.

---

## MODULE 4 — Duty cycle and RMS values

### 4.1 — Cycle times ✅

$$t_1 = \frac{d_{max}}{v}\cdot 0.1,\quad t_2 = \frac{d_{max}}{v}\cdot 0.1 + t_r,\quad t_3 = \frac{d_{max}}{v}$$

- **Variables:** `d_max` = maximum travel distance [m].
- **Notes:** ⚠️ The factor `0.1` (10% of the travel time assigned to the initial phase) is a **magic constant** that models a simplified trapezoidal cycle profile. It must be declared as a parameter of the *cycle profile* (with its justification) and, better still, replaced by a configurable cycle profile (ISO 4301-1 / FEM utilization groups, with real `%ED` — cyclic duration factor — and starts/hour). The duty cycle is the basis of the thermal analysis, so it deserves an explicit model, not a buried 0.1. See `DUTY_CYCLE_MODEL.md`.

### 4.2 — RMS torque of the cycle ✅

$$T_{rms} = \sqrt{\dfrac{T_{ss}^2\,t_1 + T_{acc}^2\,t_2 + T_{ss}^2\,t_3}{t_1 + t_2 + t_3}}$$

- **Physical basis:** thermal effective value of the torque over the cycle (equivalent to the average Joule losses). Standard *thermal-equivalent RMS torque* formula for motor thermal sizing. ✅ correct.
- ⚠️ **Improvement:** explicitly include pauses (rest phase with `T≈0` during `t_off`) to reflect the duty factor `%ED`; the real cycle is almost never 100% ED. This connects directly with the "Thermal analysis" mission item.

### 4.3 — RMS current ✅

$$I_{rms} = \sqrt{\dfrac{I_{ss}^2\,t_1 + I_{acc}^2\,t_2 + I_{ss}^2\,t_3}{t_1 + t_2 + t_3}}$$

- Analogous to 4.2 for sizing the drive's rated current. ✅ correct.

---

## MODULE 5 — Motor sizing and validation

### 5.1 — 50 Hz → 60 Hz conversion ✅

When the grid frequency is 60 Hz, scale the ratings of a motor characterized at 50 Hz:

$$N_r^{60} = N_r^{50}\cdot\frac{60}{50},\quad P_r^{60} = P_r^{50}\cdot\frac{60}{50},\quad T_r = \frac{P_r\cdot 1000}{2\pi N_r/60}$$

- **Notes:** ✅ common engineering approximation (at proportional voltage, torque is preserved and power/speed scale with frequency). ⚠️ Must be documented as an *assumption* in the report (not all motors scale ideally). Better: require nameplate data at the target frequency and offer the conversion only as an estimate.

### 5.2 — Rated current ✅

$$I_r = \frac{P_r\cdot 1000}{\sqrt{3}\cdot V_r\cdot \eta_{motor}\cdot \cos\varphi}$$

- **Physical basis:** three-phase power `P = √3·V·I·cosφ·η`. ✅ correct. The code uses a fixed `η_motor = 0.925` → **extract as a parameter** (nameplate efficiency).

### 5.3 — Breakdown (stall) torque and maximum mechanical torque ✅

$$T_{st} = T_{br}\cdot T_r \;\;(\text{if } T_{br}<7),\qquad T_{mech,max} = T_{lr}\cdot T_r\;\;(\text{if } T_{lr}<7)$$

- **Variables:** `T_br`, `T_lr` = multiples of rated torque (nameplate factors); if the entered value is ≥7 it is interpreted as an absolute value in N·m.
- **Notes:** ✅ functional, but the "threshold 7" for distinguishing a *multiple* from an *absolute value* is fragile. Better: separate, typed fields (`T_br_pu` [–] vs `T_br_abs` [N·m]).

### 5.4 — Field weakening curve ⚠️

$$T_{st}(N) = T_{st}\cdot\left(\frac{N_r}{N}\right)^2 \quad (N \geq N_r)$$

- **Physical basis:** above the base speed, at constant voltage the flux drops and the maximum torque of an induction motor decreases approximately with `1/N²`. Standard approximation in the constant-power region.
- **Notes:** ✅ acceptable and commonly used approximation. ⚠️ Document it as an approximation; the real behavior depends on the motor's reactance.

### 5.5 — Motor validation conditions ⚠️

| # | Condition | Original criterion |
|---|---|---|
| 1 | Mechanical torque | `T_mech,max > T_acc` |
| 2 | Breakdown torque with margin | `T_st/1.2 > T_acc` |
| 3 | Speed | `N_r > N_c` **and** `N_c > 0.75·N_r` |
| 4 | Thermal RMS torque | `T_r > 0.9·T_rms` |

- **Notes:** reasonable validation logic. ⚠️ The factors `1.2` (breakdown torque margin), `0.75` (lower speed band), and `0.9` (RMS margin) are **engineering criterion constants** that must: (a) be declared as parameters of the *sizing policy*, (b) be justified with a normative reference (FEM 1.001 / ISO 4301 for service factors and margins), and (c) be recorded in the report as "applied assumptions". Never buried in the code.

---

## MODULE 6 — Drive (VFD) sizing and validation

### 6.1 — Motor current as a function of torque ⚠️ **IMPROVE (physics)**

**Model (correct structure):**
$$I(T) = I_r\sqrt{\,i_o^2 + \left(\frac{T}{T_r}\right)^2\left(1 - i_o^2\right)}$$

where `i_o = I_0/I_r` is the normalized no-load (magnetizing) current. It verifies: `I(0)=I_r·i_o=I_0` ✅ and `I(T_r)=I_r` ✅. It is the **quadrature sum** of the magnetizing component (constant) and the load component (proportional to torque).

- **Confirmed physical basis:** the no-load current is essentially magnetizing; the total current is `I=√(I_0² + I_load²)` with `I_load ∝ T`. Standard model. ✅
- ❌ **Error to fix in the `i_o` estimator:** the code estimates `i_o = √(1 − cosφ)`, which is **not physical** (it mixes dimensions). The magnetizing current is the reactive component, so the correct estimator is:
  $$i_o \approx \sin\varphi = \sqrt{1 - \cos^2\varphi}$$
  **Better still:** allow `I_0` as a **nameplate input** (no-load current, typically 20–50% of `I_r`, lower in large motors) and use `sinφ` only as a default estimate when the data is not available.

### 6.2 — Steady-state and acceleration currents ✅

$$I_{ss} = I(T_{ss}),\qquad I_{acc} = I(T_{acc})$$

For a **2 motors/drive** configuration (`z=2`) the code doubles both. ✅ correct (parallel currents add).

### 6.3 — Drive current estimation ⚠️

$$I_{h} = \frac{I_{acc}}{1.6},\qquad I_{h,\,60s} = 1.5\cdot I_h$$

- **Interpretation:** `I_h` = continuous drive current; an overload capability of **160%** (factor 1.6) is assumed to cover `I_acc`, and a short-duration overload of **150%** for 60 s.
- **Notes:** ⚠️ The factors `1.6` and `1.5` are **typical overload capabilities of heavy-duty drives**, but they vary by manufacturer and class (and here lies the manufacturer neutrality risk!). They must be **parameters of the imported drive dataset**, not core constants. The core must only calculate the *required* current (`I_ss`, `I_acc`, `I_rms`); the comparison against the overload capability belongs to the *equipment selection* layer.

### 6.4 — Drive validation conditions ✅

| # | Condition | Criterion |
|---|---|---|
| 1 | Overload | `I_h,overload > I_acc` |
| 2 | Continuous | `I_h > I_ss` |
| 3 | Thermal | `I_r,drive > 0.9·I_rms` |

- ✅ Correct logic. The `0.9` factor is the same RMS margin criterion as in the motor → parameterize consistently.

---

## Consolidated table of constants to externalize

These are the "magic constants" of the original code that must be moved out to versioned configuration (with their justification and, where applicable, normative reference):

| Constant | Original value | Meaning | Where it must live |
|---|---|---|---|
| `g` | 9.81 | Gravity | Global physical constant (use 9.80665) |
| `μ` (trolley) | 0.016 | Rolling resistance wheel/rail | Validated per-project input |
| `η` gearbox | 0.9 | Mechanical efficiency | Input (gearbox nameplate) |
| `η` motor | 0.925 | Motor efficiency | Input (motor nameplate) |
| `0.1` | phase-1 fraction | Cycle profile | Cycle model (%ED, ISO 4301) |
| `1.2` | breakdown torque margin | Sizing policy | Criteria config + standard |
| `0.75` | lower speed band | Sizing policy | Criteria config |
| `0.9` | RMS margin | Sizing policy | Criteria config |
| `1.6` | drive overload | Drive capability | Drive dataset (manufacturer-neutral) |
| `1.5` | 60 s overload | Drive capability | Drive dataset |
| `threshold 7` | pu vs. absolute | Input interpretation | Remove: separate typed fields |

---

## Map to standards (for the "Standards Support" requirement)

The architecture must abstract these references in a standards layer, not embed them:

- **FEM 1.001 / FEM 9.511** — mechanism groups, service factors, travel resistance, minimum brake torque (1.6× static load torque, confirmed in crane brake practice).
- **ISO 4301-1** — classification of cranes and mechanisms (utilization groups, duty factor %ED, starts/hour) → basis for Module 4.
- **IEC 60034** — characteristics of rotating electrical machines (torque, current, duty types S1–S10, thermal class) → basis for Modules 5–6.
- **IEC 61800** — adjustable speed drives (overload classes) → basis for Module 6.
- **CMAA 70/74** — North American equivalent for overhead cranes (future support).

---

## Summary of priority corrections

1. ❌ **Load inertia in the hoist (2.4)** — physically wrong formula (underestimates the dynamic torque). Fix to `J = m·(D_w/2)²/(s²·i²)`. **Safety impact: high.**
2. ❌ **No-load current estimator (6.1)** — `√(1−cosφ)` is not physical. Fix to `sinφ = √(1−cos²φ)` or, better, nameplate input `I_0`.
3. ⚠️ **Efficiency depending on travel direction in the hoist (2.1)** — the original only models lifting; add lowering (η in the numerator) for start/stop and braking.
4. ⚠️ **Sign of the incline force (Module 3)** — preserve the sign to distinguish motoring from regenerative operation (braking resistor sizing).
5. ⚠️ **Magic constants** — externalize all of them (table above) so the engine is deterministic, auditable, and versioned.
6. ⚠️ **Rotor inertia in travel (1.4)** — add motor+gearbox inertia for rigor.
7. ⚠️ **Cycle/thermal model (4.x)** — replace the `0.1` with a real cycle profile with %ED.

---

## Open questions (to decide before reimplementing)

- **Cycle profile:** simple parameterizable trapezoidal model, or full ISO 4301 profile with %ED and starts/hour? (affects the thermal and start/stop analyses, both in the mission).
- **Braking and regeneration:** the original `To_do.txt` already asked for "braking power for the resistors". Is braking resistor sizing included in v1?
- **Travel resistance level:** simple `μ·m·g` model (level 1) and full FEM model (level 2), switchable by calculation version?
- **Motor/drive data:** confirm that all parameters are generic (power, current, voltage, cosφ, efficiency, inertia, overload factors) and that no manufacturer catalog enters the core.

---

*This inventory is the basis for versioning the calculation engine. Each reimplemented formula must carry as metadata its identifier (e.g. `MECH.TRAVEL.Tss.v1`), its normative reference, and the calculation version, so that every generated report is technically auditable and reproducible.*
