# Simulation Findings: Honest Assessment

## Critical Finding: The Coupling Term Has Zero Dynamical Effect

### What we found

The MCT coupling force $\alpha \nabla \phi$ is a gradient (irrotational) field. In incompressible Navier-Stokes, the Leray projection enforces divergence-free velocity by removing all gradient components. The coupling force is therefore projected out at every time step.

This was verified by running 4 topologies at 3 coupling strengths (alpha = 0, 0.05, 0.15) for 2000 steps each. Enstrophy and kinetic energy are identical to 10+ decimal places across all coupling values.

**The fluid does not respond to the MCT coupling. All previous "coupled" simulations evolved identically to pure Navier-Stokes.**

### What this means for previous results

| Previous claim | Actual status |
|---|---|
| "Different topologies produce different gravitational masses" | The mass spectrum is real as a *diagnostic* (different vorticity distributions produce different Poisson solutions). But the fluid dynamics is unaffected. The "masses" are geometric properties of the initial condition, not dynamical emergent quantities. |
| "Coupling modulation changes mass" | Trivially true because we measured alpha * (Poisson solve), and alpha was the parameter we varied. The fluid was unchanged. |
| "1/r potential and 1/r^2 force" | Properties of Poisson's equation, not of the dynamics. Correct math, not physics. |
| "Two-body attraction" | The static measurement (energy from Poisson) is mathematically valid. The dynamic simulation correctly showed ~zero effect because the coupling truly does nothing. |

### Why this happened

The coupling is formulated as:

$$\frac{\partial \mathbf{u}}{\partial t} + (\mathbf{u} \cdot \nabla)\mathbf{u} = -\nabla p + \nu \nabla^2 \mathbf{u} + \alpha \nabla \phi$$

The term $\alpha \nabla \phi$ is absorbed into the pressure gradient $\nabla p$ by the projection step. Defining $p' = p - \alpha \phi$ gives:

$$\frac{\partial \mathbf{u}}{\partial t} + (\mathbf{u} \cdot \nabla)\mathbf{u} = -\nabla p' + \nu \nabla^2 \mathbf{u}$$

which is exactly the standard incompressible Navier-Stokes equation. The coupling is invisible.

### This does not kill MCT

It means the coupling mechanism needs reformulation. Options:

1. **Compressible medium.** A compressible fluid has density variations. The coupling force $\rho \nabla \phi$ (with variable $\rho$) is NOT a pure gradient when $\rho$ varies spatially. The baroclinic term $\nabla \rho \times \nabla \phi / \rho^2$ generates vorticity. This would give the coupling a real dynamical effect.

2. **Couple to vorticity directly.** Instead of a body force, the coupling could modify the vortex stretching term or the viscosity. For example, coupling-dependent viscosity $\nu(\omega)$ would change the dissipation rate topology-dependently.

3. **Couple through the medium's equation of state.** In a real physical medium, gravitational potential affects density through compressibility. This is how gravity actually works in astrophysical fluids.

4. **Couple through metric modification.** Rather than adding a force to flat-space NS, modify the effective metric that the fluid propagates in. This is closer to GR and would not be removable by the projection.

The most physically motivated fix is option 1: **use compressible Navier-Stokes**. A real medium has finite sound speed. MCT's medium should too.

## Finding 2: Compressible Formulation is Numerically Unstable

Spectral methods for compressible NS blow up due to Gibbs phenomenon at density gradients. Even with 2/3 dealiasing and density diffusion, simulations at c_s=5 explode by step 560. A proper compressible simulation needs shock-capturing schemes (WENO, TVD) which are fundamentally different from spectral methods.

## Finding 3: Variable Viscosity Coupling Works But Goes the Wrong Way

Reformulating the coupling as variable viscosity (nu_eff = nu_0 * (1 - beta * |omega|/omega_ref)) produces a real dynamical effect:

| Topology | beta=0 (control) | beta=0.3 | beta=0.6 | beta=0.9 |
|---|---|---|---|---|
| Ring (survival ratio) | 0.1397 | 0.1446 | 0.1502 | 0.2500 |
| Trefoil (survival ratio) | 0.1124 | 0.1160 | 0.1201 | 0.1241 |

The coupling stabilizes structures (more enstrophy survives). This is real and nonlinear.

**Problem:** The ring benefits MORE from coupling than the trefoil (at beta=0.9: ring 1.79x vs trefoil 1.10x). MCT predicts the opposite: more complex topology should couple more strongly. The ring is simpler (lower crossing number, zero writhe), yet it responds more to the coupling.

**Explanation:** The ring has a more compact, symmetric vorticity core. Reduced viscosity in a compact core has a larger relative effect than in a diffuse, asymmetric distribution like the trefoil. This is geometry, not topology.

**Implication for MCT:** The naive "more vorticity = less viscosity" coupling does not produce the right topology dependence. If MCT is correct, the coupling mechanism must be more subtle than spatially variable viscosity proportional to vorticity magnitude.

## Finding 4: Helicity Distinguishes Topologies (Known Result, Validated)

Helicity H = integral(u . omega) correctly distinguishes topologies:
- Ring: H = 0 (unknot, no self-linking)
- Hopf link: H = -3.66 (linking number contribution)
- Trefoil: H = -9.08 (large, knotted)
- Figure-eight: H ~ 0 total but |H|_abs = 11.08 (amphicheiral, locally helical but globally cancels)

This is a known result (Moffatt 1969) but validates our Biot-Savart initialization.

## Finding 5: Helicity-Based Variable Viscosity Also Wrong Direction

Using nu_eff = nu_0 * (1 - beta * |h|/h_ref) instead of omega-based viscosity produces the same wrong direction: ring (|H|=0) stabilized MORE than trefoil (|H|=9.08). Correlation -0.52 to -0.59.

The problem is geometric, not about what drives the viscosity. Any local viscosity reduction favors compact structures. The ring has a tighter core regardless of what field we use for the viscosity model.

## Finding 6: Helicity-Inertia (Boussinesq) Shows First Correct Direction

Formulation: rho_eff(x) = 1 + alpha * |h(x)|/h_ref. Knotted regions have more inertia.

At alpha=0.5:
- Ring (|H|=0): stability ratio 2.67
- Trefoil (|H|=9.08): stability ratio 3.93
- Hopf link (|H|=3.66): stability ratio 4.45

**First time a knotted structure is more stabilized than an unknotted one.**

Caveats: figure-eight blows up (numerical instability). Overall correlation is weak. Alpha=2.0 causes blowups. The effect may be driven by the inertia-viscosity interaction (heavier regions dissipate slower because nu/rho_eff is smaller) rather than true topological protection. Need parameter study.

This is the most promising mechanism tested: modifying inertia rather than viscosity, using helicity rather than vorticity magnitude.

## Finding 7: Critical Comparison Kills the Helicity-Inertia Hypothesis

6 topologies x 3 coupling mechanisms (helicity, omega, random) at alpha=0.3:

| Topology | |H|_total | |H|_abs | Helicity ratio | Omega ratio | Random ratio |
|---|---|---|---|---|---|
| Ring | 0.00 | 0.12 | 1.69 | 1.82 | 1.24 |
| Hopf | 3.66 | 3.71 | 2.32 | 2.50 | 1.34 |
| Trefoil | 9.08 | 9.14 | 1.98 | 2.24 | 1.29 |
| Figure-8 | 0.20 | 11.08 | 2.01 | 2.09 | 1.28 |
| T(2,5) | 17.23 | 17.33 | 1.73 | 1.80 | 1.25 |
| T(2,7) | 24.86 | 24.99 | 1.91 | 1.98 | 1.26 |

Correlations with |H|_total: **all negative** (helicity -0.23, omega -0.29, random -0.28).

The v2 "positive" result (trefoil > ring at alpha=0.5) was real but misleading. With 4 topologies the correlation appeared positive. Adding T25 and T27 (highest helicity, among least stabilized) flipped it negative. Classic small-sample spurious correlation.

**Helicity-inertia and omega-inertia produce nearly identical rankings.** Both rank hopf link first, ring near last. The ranking tracks geometric compactness (how concentrated the vorticity is), not topological invariants.

**Conclusion: in incompressible pseudo-spectral simulations, no coupling mechanism we tested produces genuinely topology-dependent stabilization.** The physics distinguishes compact from diffuse structures, not knotted from unknotted.

## Summary of All Findings

After 7 rigorous experiments testing 5 coupling mechanisms on up to 6 topologies:

1. **Gradient force (alpha * grad(phi)):** algebraically invisible in incompressible flow.
2. **Variable viscosity (omega-based):** stabilizes compact structures more (wrong direction).
3. **Variable viscosity (helicity-based):** same wrong direction.
4. **Helicity-inertia (Boussinesq):** appeared correct with 4 topologies, reversed with 6.
5. **Critical comparison:** helicity, omega, and random coupling all produce similar rankings based on geometric compactness, not topology.

**No formulation of the coupling tested in incompressible spectral flow produces the MCT prediction that more complex topology = more mass/stability.**

Possible reasons:
- Spectral methods smooth all structure, destroying topological information
- Incompressible flow may fundamentally not support topology-dependent coupling
- The MCT coupling mechanism may require compressible flow, discrete vortex methods, or fundamentally different equations
- The MCT hypothesis connecting topology to mass may be wrong

## Open Questions

1. Is there any coupling formulation that survives the Leray projection AND produces topology-dependent stabilization in the correct direction?
2. Does MCT fundamentally require a compressible medium? If so, the entire spectral approach may need to be replaced with finite-volume methods.
3. Can topological invariants (writhe, linking number) be meaningfully incorporated into the coupling without being ad hoc?

## Lessons

- Always run controls
- A gradient force in incompressible flow does nothing
- Measuring a diagnostic (Poisson solve on the vorticity) is not the same as proving dynamical feedback
- Self-criticism catches fundamental errors that enthusiasm hides
- Variable viscosity coupling works dynamically but the topology dependence is wrong
- Simpler structures benefit more from local viscosity reduction (compact core effect)
- Ad hoc formulations are quick but may not test the right physics
