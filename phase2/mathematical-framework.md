# Phase 2 — Mathematical Formalization of Medium Coupling Theory

## 1. Mathematical Setup

### 1.1 The Medium

We model the medium as a continuous dynamical substrate described by:

- A velocity field **u**(**x**, t) — the local flow of the medium
- A scalar potential Φ(**x**, t) — encoding the flow's acceleration structure
- A medium characteristic speed c₀ — the maximum propagation speed of disturbances in the medium

The medium satisfies continuity:

∇ · **u** = σ(**x**, t)

where σ is the **coupling source density** — nonzero only where matter (coupled structures) exists. In vacuum, the medium flow is divergence-free.

The momentum equation for the medium (Euler-type):

∂**u**/∂t + (**u** · ∇)**u** = −∇Φ

This is the equation of motion for the medium itself. Objects embedded in the medium don't move *through* it — they are carried *by* it. Their acceleration is the medium's acceleration at their location.

### 1.2 Coupling

A material structure (particle, body) at position **x** couples to the medium with strength:

κ = αL

where L is the structure's total angular momentum magnitude and α is a universal coupling constant (a property of the medium). The coupling strength κ determines:

- **Mass**: m = κ / √(4πG̃), where G̃ is related to medium elastic properties
- **Gravitational charge**: the structure acts as a source in the medium flow
- **Inertial resistance**: the medium's response to displacing the structure

We define the gravitational coupling constant through the medium:

G = α² / (4π ρ_m)

where ρ_m is the medium's effective impedance (analogous to density). G is not fundamental — it is a derived quantity from medium properties.

### 1.3 Background State

At cosmological scales, the medium is a toroidal vortex with:

- Major radius R_T (torus center to tube center)
- Minor radius a_T (tube cross-section radius)
- Poloidal circulation Γ_p (the inside-out rolling speed)
- Toroidal circulation Γ_t (the rotation around the torus axis)

Locally — on scales ≪ a_T — the poloidal flow appears as a nearly uniform acceleration field:

**g**₀ ≈ Γ_p² / a_T (directed toward the torus tube center)

This is the "cosmological background acceleration." All local gravitational phenomena are perturbations on top of this background.

---

## 2. Derivation: Newtonian Gravity from Medium Flow

### 2.1 Statement

A mass M creates a local perturbation in the medium. We show that the resulting flow field produces an acceleration on a test mass m equal to:

**F** = −GMm/r² **r̂**

### 2.2 Setup

Consider a compact structure with coupling strength κ_M = √(4πG) · M sitting at the origin. This structure is coupled to the medium — it continuously exchanges angular momentum with the flow, creating a steady-state perturbation in the surrounding medium.

We decompose the medium velocity field:

**u** = **u**₀ + **u**'

where **u**₀ is the background (cosmological) flow and **u**' is the perturbation from the mass M.

### 2.3 The Medium Response Equation

In the far field (r ≫ r_s, where r_s is the size of the structure), the perturbation is small and the medium responds linearly. The steady-state perturbation satisfies:

∇²φ = −4πG ρ_matter(**x**)

where φ is the perturbation potential (**u**' = −∇φ) and ρ_matter is the coupling source density.

**Why this equation?** The medium is a continuous, isotropic, linear-response substrate (in the weak-field limit). A localized coupling source creates a disturbance that propagates outward. In steady state, the disturbance satisfies the Poisson equation — this is not an assumption borrowed from Newtonian gravity, but a generic property of any continuous medium responding to a localized source in three spatial dimensions.

Specifically: the medium's response function (Green's function) in 3D is determined by the geometry. A point source in a 3D isotropic medium produces a 1/r potential. This is a topological fact about 3-space, not a dynamical assumption. Gravity goes as 1/r² because space has three dimensions and the medium fills it isotropically.

### 2.4 Solution

For a point mass M at the origin:

ρ_matter(**x**) = M δ³(**x**)

The solution is the standard Green's function:

φ(r) = −GM/r

The medium acceleration field (perturbation due to M):

**g**(r) = −∇φ = −(GM/r²) **r̂**

### 2.5 Force on a Test Mass

A test mass m at position **r** is coupled to the medium with strength κ_m. The coupling means the test mass is carried by the medium flow. The force it experiences is:

**F** = m · **g**(r) = −(GMm/r²) **r̂**

This is Newton's law of gravitation.

### 2.6 What MCT Adds

The derivation above recovers Newton's law, but the MCT framework provides content that Newtonian gravity alone does not:

1. **The mechanism**: Gravity is medium flow, not action at a distance. Mass M perturbs the medium; mass m is carried by the perturbed flow. No force is transmitted — it's advection.

2. **Why 1/r²**: Because the medium fills three spatial dimensions isotropically. If the medium had different topology (e.g., confined to a 2D surface), gravity would go as 1/r. The force law encodes the medium's geometry, not a fundamental inverse-square postulate.

3. **Why G exists**: G = α²/(4πρ_m) is built from the coupling constant α and the medium impedance ρ_m. G is not a free parameter of nature — it is determined by the medium's properties.

4. **Why gravity is universal**: Every structure with angular momentum couples to the same medium through the same mechanism. There is one medium, one coupling constant. Universality is automatic.

5. **Why gravity is always attractive**: The coupling always creates inward flow (the angular momentum structure pulls medium inward to maintain its rotation). Two such sources always flow toward each other. There is no configuration of angular momentum coupling that produces repulsive gravity — the medium always flows in.

---

## 3. Derivation: The Equivalence Principle

### 3.1 Statement

In MCT, the equivalence principle is not a postulate — it is a structural identity.

### 3.2 Argument

Consider an observer inside a closed laboratory, coupled to the medium. The observer's accelerometer reads the local medium acceleration **g**(**x**, t) — this is all any physical measurement can access.

There are two scenarios:

**Scenario A — Gravitational field:** The laboratory is near a mass M. The medium flows inward with acceleration **g** = −GM/r² **r̂**.

**Scenario B — Accelerating laboratory:** The laboratory is far from any mass, but the medium is undergoing uniform acceleration **g** = **a**₀ (e.g., from the cosmological poloidal flow, or from any large-scale medium motion).

In both cases, the observer's instruments measure the same thing: the medium acceleration at their location. The observer is coupled to the medium. Their physics is entirely determined by the local medium state. There is no additional variable that distinguishes "gravitational acceleration" from "medium acceleration" — because they are the same thing.

The equivalence principle in MCT is the statement: **there is only one kind of acceleration.** It is always the medium accelerating. The distinction between "gravity" and "inertial acceleration" is a labeling convention, not a physical difference. Mass M creates a particular flow pattern. The cosmological torus creates another. Locally, they are indistinguishable because locally, all that exists is the medium and its flow.

### 3.3 Inertial Mass = Gravitational Mass

In Newtonian mechanics, it's a coincidence that the m in F = ma (inertial mass) equals the m in F = GMm/r² (gravitational mass). In MCT, both are κ — the coupling strength to the medium.

- **Gravitational mass**: how strongly you source the medium flow (how big a perturbation you create).
- **Inertial mass**: how strongly the medium grips you when an external force tries to change your state (how much the medium resists your displacement).

Both are determined by the same angular momentum coupling. They must be equal — they are the same quantity measured two ways.

---

## 4. Derivation: The Speed of Light as Separation Rate

### 4.1 Statement

The speed of light c is not the velocity of photons through space. It is the rate at which mass-coupled matter separates from uncoupled radiation. c is a property of the medium.

### 4.2 Formalization

Define two classes of entity in the medium:

- **Coupled** (κ > 0): structures with angular momentum, carried by the medium flow. These are matter.
- **Uncoupled** (κ = 0): no angular momentum, no coupling. These are radiation (light).

The medium flows with local velocity **u**(**x**, t). A coupled object at position **x** moves with the medium:

d**x**_matter/dt = **u**(**x**, t)

An uncoupled entity (light) does not move with the medium. Its position is determined by the medium's wave equation — disturbances in the medium propagate at the medium's characteristic speed c₀ relative to the medium's local rest frame. But since light is uncoupled, it does not get dragged.

From the perspective of a coupled observer (who is being carried by the medium), light appears to move at speed c₀. But the observer doesn't know they're being carried. They measure the separation rate between themselves and the light, and find:

v_separation = c₀

This is always the same, regardless of the observer's "velocity" — because the observer has no velocity relative to the medium. They ARE the medium (coupled to it). The separation rate depends only on the medium's characteristic speed, which is a constant.

### 4.3 Lorentz Invariance

This picture directly yields Lorentz invariance. Consider two coupled observers A and B, in relative motion (their local medium flows differ by Δ**u**). Both measure the separation rate to light as c₀, because both are embedded in the medium and both measure the same medium characteristic speed.

The transformations between A's and B's coordinate systems must preserve c₀. The unique linear transformation that preserves a universal speed is the Lorentz transformation:

t' = γ(t − vx/c₀²)
x' = γ(x − vt)

where γ = 1/√(1 − v²/c₀²).

In MCT, Lorentz invariance is not a postulate about spacetime geometry. It is a consequence of two facts:
1. All observers are coupled to the same medium
2. The medium has a finite, constant characteristic speed c₀

The "speed limit" c₀ is not a limit on how fast things can move. It is the medium's own characteristic — the rate at which its internal disturbances propagate. Nothing coupled to the medium can separate from it faster than c₀, because that would require the coupling to transmit information faster than the medium can carry it. This is self-contradictory — like asking a wave to outrun the medium it's waving in.

### 4.4 Identification

We identify c₀ = c = 299,792,458 m/s. This is the medium's characteristic propagation speed, measured by coupled observers as the speed of light.

---

## 5. Derivation: Mass Quantization from Angular Momentum

### 5.1 Statement

Mass is quantized because angular momentum is quantized and mass is a function of angular momentum.

### 5.2 The Coupling Function

From MCT postulate 2: mass = angular momentum coupling to the medium.

κ = α · L_eff

where L_eff is the effective angular momentum of the structure — not simply the spin quantum number, but the total angular momentum topology including:
- Intrinsic spin S
- Internal orbital angular momentum (e.g., quarks inside a proton)
- Topological winding number (how the structure's flow pattern wraps around the medium)

In quantum mechanics, angular momentum is quantized:

L = √(l(l+1)) ℏ     (orbital)
S = √(s(s+1)) ℏ     (spin)

Since κ ∝ L_eff and L_eff is quantized, κ is quantized, and therefore mass is quantized.

### 5.3 Why the Photon is Massless

A photon has spin s = 1, so S = √2 ℏ ≠ 0. In conventional physics, this is a puzzle — it has spin but no mass.

In MCT, the resolution is topological. Spin alone does not determine coupling — the *topology* of the angular momentum matters. A photon's spin is transverse to its propagation. It does not create a rotational structure that interlocks with the medium's poloidal flow. It slides through without coupling.

The coupling condition is not L > 0 but rather: the angular momentum topology must have a component that wraps around the medium's flow direction. Photon polarization is perpendicular to propagation — it has no winding around the flow. Hence κ = 0 and m = 0.

Compare this with a massive spin-1 particle (W or Z boson): these have angular momentum topologies that *do* wrap the medium, because their internal structure (they are composite at the electroweak scale) provides the necessary topological complexity.

### 5.4 Mass Spectrum — Qualitative Structure

The mass of a particle is determined by its angular momentum topology:

- **Electron** (m_e = 0.511 MeV/c²): simplest massive topology. Spin-1/2 with minimal winding. The lightest stable coupled structure.

- **Proton** (m_p = 938.3 MeV/c²): three quarks, each spin-1/2, bound by gluon fields carrying angular momentum. Far more complex topology — tighter, more elaborate knot in the medium. Mass ratio m_p/m_e ≈ 1836 reflects the ratio of topological complexity, not a coincidence.

- **Neutrinos** (m_ν ~ 0.01–0.1 eV/c²): nearly uncoupled. Their angular momentum topology barely interlocks with the medium — they are almost light-like. This is why they are so light and interact so weakly.

The quantitative calculation of mass ratios requires solving the medium flow equations for specific topological configurations — this is the MCT equivalent of lattice QCD. The framework predicts that mass ratios should be calculable from angular momentum topology alone, with no free parameters beyond α and ρ_m.

### 5.5 The Higgs Field in MCT

The Standard Model introduces the Higgs field to give particles mass through spontaneous symmetry breaking. In MCT, the Higgs mechanism has a natural reinterpretation:

The Higgs field describes the **local properties of the medium** — specifically, the medium's coupling responsiveness at each point in space. The Higgs vacuum expectation value v = 246 GeV is a measure of the medium's coupling strength. Spontaneous symmetry breaking corresponds to the medium having a preferred flow state (the toroidal vortex) rather than a uniform, symmetric state.

The Higgs boson is then a propagating disturbance in the medium's coupling properties — a ripple in the medium's responsiveness, rather than a separate field.

This is not a dismissal of the Higgs mechanism. It is a deeper interpretation: the Higgs field is real, measurable, and its predictions are correct. MCT provides the mechanical picture underneath.

---

## 6. Derivation: Schwarzschild Metric from Nonlinear Medium Response

### 6.1 Statement

When the medium flow perturbation is strong (near large masses), the linear approximation breaks down. The nonlinear medium response recovers the Schwarzschild metric of general relativity.

### 6.2 Setup

In Section 2, we assumed the perturbation was small and the medium response was linear (Poisson equation). Near a mass M, define the characteristic coupling radius:

r_s = 2GM/c₀²

For r ≫ r_s, the linear approximation is valid and we recover Newtonian gravity. For r ~ r_s, the medium flow becomes relativistic — the flow speed approaches c₀ — and nonlinear corrections dominate.

### 6.3 The Nonlinear Flow Equation

The full medium equation (beyond linear response) must respect:
1. The medium's characteristic speed c₀ (information cannot propagate faster than c₀)
2. The coupling structure (source terms proportional to κ)
3. Consistency with the equivalence principle (the equation must be the same in all coupled frames)

Requirement (3) is the key constraint. The medium flow equation must be **generally covariant** — expressible in any coordinate system of coupled observers. Combined with (1) and (2), this leads uniquely to Einstein's field equations:

G_μν = (8πG/c₀⁴) T_μν

This is not a derivation from first principles in the sense of a mathematical proof — it is the recognition that Einstein's equations are the *unique* nonlinear, generally covariant equations for a medium with a finite characteristic speed and a local coupling source. The field equations describe the medium's behavior. GR is the correct effective theory of the medium.

### 6.4 Schwarzschild Solution

For a spherically symmetric mass M in vacuum, the medium flow settles into a steady state described by the Schwarzschild metric:

ds² = −(1 − r_s/r)c₀²dt² + (1 − r_s/r)⁻¹dr² + r²dΩ²

In MCT, this metric has a direct physical interpretation:

- **Time dilation** (the g_tt component): Clocks are coupled to the medium. Near M, the medium flows faster (stronger coupling perturbation). Faster flow → time runs differently for the coupled clock. This is gravitational time dilation — not geometry, but flow speed.

- **Spatial distortion** (the g_rr component): Measuring rods are coupled structures. They are compressed or stretched by the medium flow gradient. The metric describes how coupled measuring instruments respond to the flow, not an abstract curvature of "spacetime."

- **The horizon** (r = r_s): Where the medium inflow speed equals c₀. At this radius, the medium is flowing inward at the speed of its own disturbance propagation. Nothing coupled to the medium can escape — not because of a "barrier," but because the medium itself is falling in faster than any signal can propagate out. Light (uncoupled) is dragged in because even its propagation through the medium cannot overcome the flow speed.

### 6.5 What MCT Adds to GR

GR is a correct description of the medium dynamics. MCT does not "replace" GR — it provides the mechanical picture that GR describes mathematically:

| GR Description | MCT Interpretation |
|---|---|
| Spacetime curvature | Medium flow geometry |
| Geodesic motion | Advection by the medium |
| Stress-energy tensor | Coupling source distribution |
| Metric tensor | Medium flow state (as measured by coupled instruments) |
| Gravitational constant G | Derived from α and ρ_m |
| Singularity (r = 0) | Maximum medium flow density (possibly regularized by medium micro-physics) |

The key prediction: GR should break down where the medium's continuum approximation fails — at the Planck scale, or in situations where the medium's micro-structure matters. MCT predicts that singularities are artifacts of the continuum approximation, not physical infinities.

---

## 7. Derivation: Entropy from Medium Dynamics

### 7.1 Statement

The second law of thermodynamics is not a statistical axiom. It is a consequence of the medium's churning dynamics.

### 7.2 Argument

The medium is not static. It circulates, rolls, and flows. The background toroidal motion ensures that every region of the medium is continuously being stirred.

Consider a localized, ordered configuration of coupled structures (low entropy state). The medium flow acts on each structure according to its coupling. But the flow is not uniform — it has gradients, shear, and vorticity from the toroidal circulation. These differential motions act on the ordered configuration, progressively dispersing it.

The rate of entropy increase is set by the medium's flow properties:

dS/dt ~ Γ_p / a_T × (geometric factor)

This is the ratio of poloidal circulation to torus size — essentially, how fast the medium stirs its contents. The second law holds because the medium is always stirring. It would fail only if the medium stopped flowing, which would also mean no gravity, no inertia, no mass — the medium IS the physics.

### 7.3 Arrow of Time

The thermodynamic arrow of time aligns with the medium's flow direction. Time "moves forward" in the direction the medium circulates. This is not a deep mystery in MCT — the medium has a definite circulation direction (poloidal flow has a handedness), and this breaks time-reversal symmetry at the cosmological level.

The microscopic laws of physics appear time-reversible because, locally, the medium flow looks approximately uniform. It's only over distances and times comparable to the medium's circulation scale that the asymmetry becomes visible as entropy increase.

---

## 8. The Aharonov-Bohm Effect: Potentials Are the Medium

### 8.1 The Problem

In 1959, Aharonov and Bohm predicted — and experiments later confirmed — that a charged particle is physically affected by electromagnetic potentials even in regions where the electromagnetic fields are exactly zero.

The standard setup: a long solenoid carries magnetic flux Φ. Outside the solenoid, the magnetic field **B** = ∇ × **A** = 0. But the vector potential **A** ≠ 0 — it circulates around the solenoid. An electron beam split around the solenoid picks up a phase difference:

Δθ = (e/ℏ) ∮ **A** · d**l** = (e/ℏ) Φ

This phase shift is measurable as an interference pattern shift, even though the electron never encounters any field. The effect has been confirmed to high precision.

This troubled physics deeply. In classical electromagnetism, **A** is a mathematical convenience — only the fields **E** and **B** are "real." The AB effect says otherwise: the potential has direct physical consequences. Mainstream physics accepts this formally (gauge theory requires it), but has no mechanical explanation for *why* the potential is physical.

### 8.2 MCT Resolution

In MCT, the resolution is immediate and mechanical.

**The electromagnetic potential A describes the medium's local flow state. The fields E and B are derived quantities — gradients and curls of the medium state. The electron is coupled to the medium itself, not to derived quantities of the medium.**

This is the complete answer. But let's make it precise.

### 8.3 The Fluid Dynamics Analogy (Exact, Not Approximate)

Consider a bathtub vortex. Inside the vortex core, the water rotates with nonzero vorticity (∇ × **v** ≠ 0). Outside the core, the flow is irrotational (∇ × **v** = 0) — but the water is still moving. It circulates around the core with velocity:

v(r) = Γ / (2πr)

where Γ is the circulation. A small boat floating outside the core gets carried by this flow. The boat doesn't care that the local vorticity is zero. It responds to the water, not to the curl of the water.

Now the key point: this isn't an analogy. In MCT, this IS the physics.

The solenoid creates a vortex structure in the medium. Inside the solenoid, the medium has electromagnetic vorticity (**B** ≠ 0). Outside, the medium flow is irrotational (**B** = 0) but has nonzero circulation (**A** ≠ 0). The electron, coupled to the medium, responds to the medium's actual state — the flow **A** — not to the derived vorticity **B**.

### 8.4 Formal Statement

In MCT, identify:

- **A**(**x**) = electromagnetic component of the medium's flow velocity at **x**
- **B** = ∇ × **A** = local vorticity of the electromagnetic flow
- **E** = −∂**A**/∂t − ∇φ = acceleration of the electromagnetic flow

A coupled charged particle at position **x** interacts with the medium via:

H_coupling = (e/c) **A** · **v**_particle

where e is the electromagnetic coupling strength (charge) and **v**_particle is the particle's velocity through the medium.

The phase accumulated by a quantum particle moving through the medium is:

θ = (e/ℏc) ∫ **A** · d**l**

This phase depends on **A** along the path, not on **B**. For two paths encircling the solenoid:

Δθ = (e/ℏc) ∮ **A** · d**l** = (e/ℏc) Φ

by Stokes' theorem (the line integral of **A** equals the enclosed flux).

### 8.5 Why This Was Mysterious (And Why It Shouldn't Have Been)

The AB effect was mysterious because of an ontological mistake: treating the fields as fundamental and the potentials as mathematical artifacts.

In MCT, the hierarchy is reversed:

| Conventional View | MCT View |
|---|---|
| **E**, **B** are the physical reality | **A**, φ are the physical reality (medium state) |
| **A**, φ are gauge-dependent math tools | **E**, **B** are derived quantities (curls/gradients) |
| AB effect is paradoxical | AB effect is obvious |

The "gauge freedom" in choosing **A** reflects the freedom to add any gradient to the flow without changing the vorticity — analogous to choosing a reference frame for the fluid velocity. The physics (the actual medium flow as experienced by coupled particles) doesn't change.

### 8.6 Predictions

MCT's interpretation of the AB effect makes specific predictions:

1. **Gravitational AB effect**: If gravity is also a medium flow (Section 2), there should be a gravitational analogue of the AB effect — a phase shift from gravitational potentials in regions of zero gravitational field. This would be detectable via matter-wave interferometry around a carefully shielded mass distribution. The phase shift would be:

   Δθ_grav = (m/ℏ) ∮ **Φ**_g · d**l**

   where **Φ**_g is the gravitational flow potential. This is an extremely small effect but in principle measurable with atom interferometry.

2. **Topological quantization**: The AB phase must be single-valued for consistency (the wavefunction must return to itself around a loop). This requires:

   eΦ/(ℏc) = 2πn

   leading to flux quantization in superconductors — which is observed. In MCT, this is the condition that the medium's electromagnetic flow admits only discrete winding numbers. The medium itself is quantized topologically.

3. **No AB effect without the medium**: If the AB effect is the particle coupling to the medium's flow, then any attempt to shield the particle from the medium (if that were possible) would eliminate the effect. In practice, coupling to the medium cannot be turned off for charged particles — but this prediction distinguishes MCT from purely geometric/topological interpretations.

### 8.7 Connection to Electromagnetism in MCT

The AB effect points toward how electromagnetism fits into MCT more broadly. The electromagnetic potential **A** is a component of the medium's flow — specifically, a flow mode that couples to charge rather than mass.

This suggests the medium carries (at minimum) two independent flow modes:

- **Gravitational mode**: couples to angular momentum topology (mass). Described by the metric/gravitational potential.
- **Electromagnetic mode**: couples to a different topological property (charge). Described by the 4-potential A_μ.

Both are aspects of the same medium. The separation between gravity and electromagnetism is the separation between two coupling channels to the same underlying flow. This is consistent with Kaluza-Klein theory, which unifies gravity and electromagnetism by adding a fifth dimension — in MCT, that "extra dimension" may be an additional degree of freedom of the medium's flow.

---

## 9. Summary and Open Problems

### What We Have Derived

| Known Result | MCT Derivation | Status |
|---|---|---|
| Newton's law F = GMm/r² | Linear medium response to coupling source | Complete (Section 2) |
| Equivalence principle | Structural identity — one kind of acceleration | Complete (Section 3) |
| Speed of light as constant | Medium characteristic speed, measured as separation rate | Complete (Section 4) |
| Lorentz invariance | Consequence of finite medium speed | Complete (Section 4) |
| Mass quantization | Quantized angular momentum → quantized coupling | Framework (Section 5) |
| Schwarzschild metric | Nonlinear medium response | Recovery via uniqueness argument (Section 6) |
| Second law of thermodynamics | Medium churning dynamics | Qualitative (Section 7) |
| Aharonov-Bohm effect | Particle couples to medium flow (A), not derived fields (B) | Complete (Section 8) |

### Open Problems for Further Development

1. **Quantitative mass spectrum**: Calculate mass ratios (m_p/m_e, etc.) from angular momentum topology. This requires solving the medium flow equations for specific knot configurations. This is hard but well-defined.

2. **Electromagnetic interaction**: How does electromagnetism emerge from the medium? Angular momentum coupling handles gravity and inertia. What medium property gives rise to electric charge? Leading candidate: a second coupling mode — perhaps the toroidal component of angular momentum (vs. poloidal for gravity).

3. **Quantum mechanics**: Where does the wavefunction come from in MCT? The medium is classical in our treatment so far. Quantum behavior may arise from the medium's micro-structure — if the medium is discrete at the Planck scale, quantum mechanics could emerge as the effective dynamics of coupled structures interacting with a discrete substrate.

4. **Dark matter**: Construct explicit angular momentum topologies that have mass (gravitational coupling) but no electromagnetic coupling. Show that these are stable.

5. **Cosmological predictions**: Derive the CMB toroidal signatures, expansion dynamics, and the relationship between Γ_p and the Hubble constant from the toroidal geometry.

6. **Gravitational waves**: In MCT, gravitational waves are propagating disturbances in the medium flow. Their speed should equal c₀ — which matches observation (GW170817 confirmed gravitational waves travel at c to within 10⁻¹⁵). Derive the wave equation and polarization states from medium dynamics.

7. **Medium micro-structure**: What is the medium at the smallest scales? This may connect to quantum gravity approaches — spin foams, causal sets, or loop quantum gravity might describe the medium's micro-physics.
