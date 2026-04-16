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
