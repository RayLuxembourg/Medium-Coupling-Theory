# From Quantum Mechanics to Quantum Field Theory in MCT

Section 9 of the [main framework](mathematical-framework.md#9-quantum-mechanics-from-medium-micro-structure) derived quantum mechanics from the medium's micro-structure via Nelson's stochastic mechanics. This gives the Schrödinger equation: non-relativistic, single-particle quantum mechanics.

Modern physics is quantum field theory (QFT): relativistic, multi-particle, with particle creation and annihilation. MCT must get there.

---

## 1. The Gap

### 1.1 What Nelson gives us

Nelson's stochastic mechanics, completed by the medium in MCT, gives:
- The Schrödinger equation
- The Born rule
- The uncertainty principle
- A dissolution of the measurement problem

These are the foundations of non-relativistic quantum mechanics (NRQM). This is 1926-era physics.

### 1.2 What we need

QFT (developed 1927-1970s) adds:
- Relativistic invariance (Dirac equation, Klein-Gordon equation)
- Fields as fundamental objects (not particles)
- Particle creation and annihilation (pair production, decay)
- Feynman diagrams and perturbation theory
- Renormalization (handling divergences)
- The path integral formulation

The [MCT action](mct-action.md) already contains the QFT Lagrangian. The question is how to connect the "bottom-up" stochastic picture (Nelson) to the "top-down" field theory picture (action principle).

---

## 2. Stochastic Fields

### 2.1 From stochastic particles to stochastic fields

Nelson's construction works for a single particle: it undergoes Brownian motion in the medium with diffusion $D = \hbar/(2m)$, and the resulting statistics satisfy the Schrödinger equation.

The field theory generalization: instead of a single particle's position $\mathbf{x}(t)$ fluctuating stochastically, the entire medium flow field $\hat{\mathbf{u}}(\mathbf{x}, t)$ fluctuates stochastically. The medium's micro-structure introduces random perturbations at every point, at every moment.

The statistical description of these fluctuations is the quantum field. The field operator $\hat{\phi}(\mathbf{x}, t)$ in standard QFT corresponds to the medium flow perturbation at $(\mathbf{x}, t)$, described statistically because the micro-structural noise is unresolvable.

### 2.2 The Euclidean path integral

Nelson's stochastic mechanics has a deep connection to the path integral. In Euclidean (imaginary-time) formulation, the Schrödinger equation becomes a diffusion equation, and the path integral becomes a sum over Brownian paths weighted by the action:

$$
Z = \int \mathcal{D}[\phi]\; e^{-S_E[\phi]/\hbar}
$$

where $S_E$ is the Euclidean action. Each path in the integral corresponds to a specific realization of the medium's stochastic fluctuation. The path integral sums over all realizations.

In MCT, this sum is physical: the medium's micro-structure actually generates these fluctuations, and the path integral is the average over the medium's thermal noise. There is no mystery about "summing over all paths." The medium does it mechanically.

### 2.3 Feynman diagrams

Perturbation theory expands the path integral around the classical solution (saddle point). Each term in the expansion corresponds to a Feynman diagram: a picture of medium flow disturbances propagating, interacting, and combining.

In MCT:
- **Propagators** (internal lines) are the medium's response function: how a disturbance at point $x$ affects the flow at point $y$.
- **Vertices** (interaction points) are locations where multiple medium flow modes interact, determined by the nonlinear terms in the medium equations.
- **External lines** are the incoming/outgoing particles (topological structures) whose scattering we compute.

The Feynman rules are identical to standard QFT because the MCT action is the same as the Standard Model action (after dimensional reduction, see [mct-action.md](mct-action.md#32-medium-action-gravity--gauge-fields)). MCT does not change the computational technology. It provides the physical picture underneath.

---

## 3. Particle Creation and Annihilation

### 3.1 The puzzle

In NRQM, particles are conserved. In QFT, they are created and destroyed: an electron-positron pair appears from a photon, a neutron decays into a proton plus leptons. Where do new particles come from?

### 3.2 MCT answer

The medium is the source.

When a medium flow disturbance carries enough energy (above the rest mass threshold $2mc^2$ for pair creation), it can organize itself into a topological structure (a knot). This is pair creation: the medium's flow energy converts into a new particle-antiparticle pair (a knot and its mirror image).

Conversely, when a particle and its antiparticle meet (a knot and its mirror image overlap), their topologies cancel, releasing the stored energy back into the medium flow. This is annihilation.

There is nothing mysterious about either process. The medium converts between unstructured flow energy and topological structures, the same way a fluid can form and dissolve vortices. The total energy (flow energy + topological energy) is conserved.

### 3.3 The vacuum

In QFT, the vacuum is not empty. It is a seething foam of virtual particle-antiparticle pairs constantly fluctuating. In MCT, the vacuum is the medium's ground state: the lowest-energy flow configuration. The "virtual pairs" are short-lived micro-structural fluctuations that briefly resemble topological structures before dissolving. They are not real particles; they are noise in the medium that happens to be mathematically describable as particle-antiparticle loops.

The Casimir effect (a measurable force between conducting plates from vacuum fluctuations) is the medium's micro-structural noise being modified by the boundary conditions imposed by the plates. The plates constrain which medium fluctuation modes can exist between them, creating a pressure difference. This is real and measurable, but it is a property of the medium's noise spectrum, not evidence for literal virtual particles.

---

## 4. Renormalization

### 4.1 The problem in standard QFT

Loop diagrams in QFT contain integrals over all momenta, up to infinity. These integrals diverge. Renormalization absorbs the infinities into redefined parameters (masses, couplings), producing finite predictions. This works but has always been philosophically unsatisfying: the "bare" parameters are infinite, and only the differences (which are finite) are physical.

### 4.2 MCT resolution

In MCT, the medium has a natural ultraviolet cutoff: the Planck scale $l_P$. Fluctuations at wavelengths shorter than $l_P$ do not exist because the medium's micro-structure does not support them. All loop integrals are automatically finite, cut off at momentum $p \sim \hbar/l_P \sim m_P c$.

The "bare" parameters in MCT are the actual medium parameters ($\alpha$, $\rho_m$, the compact manifold geometry). They are finite and physical. Renormalization is the process of relating these short-distance (Planck-scale) parameters to the long-distance (laboratory-scale) effective parameters, which involves integrating out the medium fluctuations between $l_P$ and the observation scale. This is a finite computation at every step.

The renormalization group is preserved: couplings still run with energy scale, because the effective description changes as we coarse-grain the medium over different length scales. But there are no infinities to subtract. The medium's granularity makes the theory UV-finite from the start.

---

## 5. Relativistic Quantum Mechanics

### 5.1 From Schrödinger to Dirac

The Schrödinger equation is the non-relativistic limit of the Dirac equation. In MCT:

The Nelson stochastic process in the full relativistic medium (where the characteristic speed is $c_0$, not infinity) yields the Dirac equation rather than the Schrödinger equation. The diffusion is modified to respect Lorentz invariance:

$$
i\hbar\frac{\partial\psi}{\partial t} = \left(c\boldsymbol{\alpha}\cdot\mathbf{p} + \beta mc^2\right)\psi
$$

where $\boldsymbol{\alpha}$ and $\beta$ are the Dirac matrices, encoding the medium's spinor structure.

The key insight: the Dirac equation requires 4-component spinors (not scalars), which describe both particles and antiparticles, both spin-up and spin-down. In MCT, these four components correspond to:

1. Particle, aligned with medium flow
2. Particle, opposed to medium flow
3. Antiparticle (mirror topology), aligned
4. Antiparticle (mirror topology), opposed

The medium's flow direction provides the physical basis for the spinor's four degrees of freedom.

### 5.2 The Klein-Gordon equation

For spinless particles (bosons), the relativistic wave equation is Klein-Gordon:

$$
\left(\Box + \frac{m^2c^2}{\hbar^2}\right)\phi = 0
$$

In MCT, this describes the propagation of unoriented medium flow disturbances (see [fermions-and-spin-statistics.md](fermions-and-spin-statistics.md#21-knots-vs-links-in-the-medium)). The mass term $m^2c^2/\hbar^2$ is the inverse square of the structure's Compton wavelength, determined by its topological coupling.

---

## 6. Summary

| QFT Concept | MCT Interpretation |
|---|---|
| Quantum field | Statistical description of medium flow fluctuations |
| Path integral | Sum over medium micro-structural realizations |
| Feynman diagram | Medium flow disturbances propagating and interacting |
| Particle creation | Medium flow energy organizing into topological structure |
| Annihilation | Knot-antiknot cancellation, energy returns to flow |
| Virtual particles | Short-lived micro-structural noise |
| Vacuum | Medium ground state (lowest-energy flow) |
| Renormalization | Relating Planck-scale medium parameters to lab-scale observables |
| UV divergences | Absent (medium micro-structure provides natural cutoff) |

MCT does not change QFT's mathematical apparatus. It provides the physical substrate that makes QFT's formal manipulations correspond to real mechanical processes in the medium.
