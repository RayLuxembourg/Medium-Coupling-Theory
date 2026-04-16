"""
MCT Simulation Phase 3: Two-Body Gravitational Interaction
===========================================================

Place two vortex structures at separation d in the medium. Compute
the interaction energy from the Poisson potential. Extract the force
F = -dE/dd and verify it follows 1/d^2 (Newton's law).

This is the second computational test of MCT: not only does a single
structure produce 1/r, but two structures attract with 1/r^2.
"""

import numpy as np
from scipy.fft import fftn, ifftn
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
import json
import time

RESULTS = Path(__file__).parent / "results"
RESULTS.mkdir(exist_ok=True)


def make_grid(N, L):
    dx = L / N
    x = np.linspace(-L/2 + dx/2, L/2 - dx/2, N)
    return x, dx


def vortex_ring_at(N, L, center, R=0.4, a=0.06, Gamma=1.0):
    """Vortex ring centered at (cx, cy, cz), lying in xy-plane."""
    x, dx = make_grid(N, L)
    X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
    Xc = X - center[0]
    Yc = Y - center[1]
    Zc = Z - center[2]
    r_cyl = np.sqrt(Xc**2 + Yc**2)
    dist = np.sqrt((r_cyl - R)**2 + Zc**2)
    rho = np.exp(-dist**2 / (2 * a**2))
    rho *= Gamma / (np.sum(rho) * dx**3)
    return rho, dx


def poisson_free_space(rho, dx):
    """Free-space Poisson solve via zero-padded FFT."""
    N = rho.shape[0]
    M = 2 * N

    rho_pad = np.zeros((M, M, M), dtype=np.float64)
    rho_pad[:N, :N, :N] = rho

    ix = np.arange(M)
    ix = np.where(ix <= N, ix, ix - M)
    IX, IY, IZ = np.meshgrid(ix, ix, ix, indexing='ij')
    R = np.sqrt((IX * dx)**2 + (IY * dx)**2 + (IZ * dx)**2)
    R[0, 0, 0] = 1.0

    G = dx**3 / R
    G[0, 0, 0] = 0.0

    phi_pad = np.real(ifftn(fftn(rho_pad) * fftn(G)))
    return phi_pad[:N, :N, :N]


def interaction_energy(rho1, rho2, dx):
    """
    Compute the gravitational interaction energy between two sources.

    E_int = integral of rho2(x) * phi1(x) dx^3
    where phi1 is the potential from rho1.
    """
    phi1 = poisson_free_space(rho1, dx)
    E = np.sum(rho2 * phi1) * dx**3
    return E


def main():
    print("=" * 70)
    print("MCT SIMULATION: Two-Body Gravitational Force")
    print("=" * 70)

    N = 128
    L = 16.0  # larger box for two separated objects
    dx = L / N
    print(f"Grid: {N}^3, box size: {L}, dx = {dx:.4f}")

    # Place two vortex rings along the x-axis at varying separations
    R_ring = 0.4
    a_core = 0.06
    M1 = 1.0
    M2 = 1.0

    separations = np.array([1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0])
    energies = []

    print(f"\nRing parameters: R={R_ring}, a={a_core}, M1={M1}, M2={M2}")
    print(f"Separations: {separations}")
    print()

    for d in separations:
        t0 = time.time()
        center1 = (-d/2, 0, 0)
        center2 = (d/2, 0, 0)

        rho1, _ = vortex_ring_at(N, L, center1, R=R_ring, a=a_core, Gamma=M1)
        rho2, _ = vortex_ring_at(N, L, center2, R=R_ring, a=a_core, Gamma=M2)

        E = interaction_energy(rho1, rho2, dx)
        energies.append(E)
        dt = time.time() - t0
        print(f"  d = {d:.1f}  E_int = {E:.6f}  ({dt:.1f}s)")

    energies = np.array(energies)

    # Force: F = -dE/dd (numerical derivative)
    forces = -np.gradient(energies, separations)

    # Fit E(d) to power law in the far field (d >> 2*R_ring)
    far_mask = separations > 3 * R_ring
    d_far = separations[far_mask]
    E_far = np.abs(energies[far_mask])

    log_d = np.log(d_far)
    log_E = np.log(E_far)
    c_E = np.polyfit(log_d, log_E, 1)
    n_E = c_E[0]

    # Fit F(d) to power law
    F_far = np.abs(forces[far_mask])
    valid_F = F_far > 1e-30
    if np.sum(valid_F) > 3:
        log_F = np.log(F_far[valid_F])
        log_dF = np.log(d_far[valid_F])
        c_F = np.polyfit(log_dF, log_F, 1)
        n_F = c_F[0]
    else:
        n_F = 0

    # Analytic expectation: E = -M1*M2/d, so n_E = -1 and F = -M1*M2/d^2, n_F = -2
    print(f"\nEnergy power law: n = {n_E:.4f} (expect -1.0)")
    print(f"Force power law:  n = {n_F:.4f} (expect -2.0)")

    # ── Plots ──
    fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))

    # Energy vs separation
    ax = axes[0]
    ax.plot(separations, energies, 'bo-', linewidth=2, markersize=6, label='Simulation')
    d_theory = np.linspace(separations[0], separations[-1], 100)
    A_E = np.exp(c_E[1])
    ax.plot(d_theory, -A_E / d_theory**abs(n_E), 'r--', linewidth=1.5,
            label=f'Fit: $E \\propto d^{{{n_E:.3f}}}$')
    ax.set_xlabel('Separation $d$', fontsize=12)
    ax.set_ylabel('Interaction Energy $E$', fontsize=12)
    ax.set_title(f'Energy vs Separation ($n = {n_E:.3f}$)', fontsize=13)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    # Force vs separation
    ax = axes[1]
    ax.plot(separations, np.abs(forces), 'go-', linewidth=2, markersize=6, label='$|F| = |dE/dd|$')
    if n_F != 0:
        A_F = np.exp(c_F[1])
        ax.plot(d_theory, A_F / d_theory**abs(n_F), 'r--', linewidth=1.5,
                label=f'Fit: $F \\propto d^{{{n_F:.3f}}}$')
    # Reference 1/d^2
    ax.plot(d_theory, np.abs(forces).max() * (separations[far_mask][0]**2) / d_theory**2,
            'k:', alpha=0.4, label='$1/d^2$ reference')
    ax.set_xlabel('Separation $d$', fontsize=12)
    ax.set_ylabel('$|F|$', fontsize=12)
    ax.set_title(f'Force vs Separation ($n = {n_F:.3f}$)', fontsize=13)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    # Log-log force
    ax = axes[2]
    ax.loglog(separations, np.abs(forces), 'go-', linewidth=2, markersize=6, label='Simulation')
    ax.loglog(d_theory, A_F / d_theory**abs(n_F), 'r--', linewidth=1.5,
              label=f'Fit: slope = {n_F:.3f}')
    ax.loglog(d_theory, A_F * d_far[0]**2 / d_theory**2, 'k:', alpha=0.4,
              label='$1/d^2$ (slope = -2)')
    ax.set_xlabel('Separation $d$', fontsize=12)
    ax.set_ylabel('$|F|$', fontsize=12)
    ax.set_title('Log-Log Force (Newton\'s Law Test)', fontsize=13)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(RESULTS / "two_body_force.png", dpi=150)
    plt.close()
    print(f"\nPlot saved: two_body_force.png")

    # Also make a nice visualization of the two-body potential field
    print("Generating two-body potential slice...")
    center1 = (-2.0, 0, 0)
    center2 = (2.0, 0, 0)
    rho1, _ = vortex_ring_at(N, L, center1, R=R_ring, a=a_core, Gamma=M1)
    rho2, _ = vortex_ring_at(N, L, center2, R=R_ring, a=a_core, Gamma=M2)
    rho_total = rho1 + rho2
    phi_total = poisson_free_space(rho_total, dx)

    mid = N // 2
    phi_slice = phi_total[:, :, mid]
    extent = [-L/2, L/2, -L/2, L/2]

    fig, ax = plt.subplots(figsize=(10, 8))
    vmax = np.max(np.abs(phi_slice)) * 0.3
    im = ax.imshow(phi_slice.T, origin='lower', extent=extent, cmap='RdBu_r',
                   vmin=-vmax, vmax=vmax)
    ax.set_xlabel('x', fontsize=13)
    ax.set_ylabel('y', fontsize=13)
    ax.set_title('Two-Body Gravitational Potential $\\phi(x, y, z=0)$', fontsize=14)
    plt.colorbar(im, ax=ax, shrink=0.8, label='$\\phi$')

    # Mark the source positions
    ax.plot(center1[0], center1[1], 'wo', markersize=10, markeredgecolor='black')
    ax.plot(center2[0], center2[1], 'wo', markersize=10, markeredgecolor='black')
    ax.annotate('$M_1$', (center1[0], center1[1]+0.5), color='white', fontsize=14,
                ha='center', fontweight='bold')
    ax.annotate('$M_2$', (center2[0], center2[1]+0.5), color='white', fontsize=14,
                ha='center', fontweight='bold')

    plt.tight_layout()
    plt.savefig(RESULTS / "two_body_potential.png", dpi=150)
    plt.close()
    print("Plot saved: two_body_potential.png")

    # Save data
    data = {
        "grid": {"N": N, "L": L, "dx": float(dx)},
        "ring": {"R": R_ring, "a": a_core, "M1": M1, "M2": M2},
        "separations": separations.tolist(),
        "energies": energies.tolist(),
        "forces": forces.tolist(),
        "energy_exponent": float(n_E),
        "force_exponent": float(n_F),
    }
    with open(RESULTS / "two_body_results.json", 'w') as f:
        json.dump(data, f, indent=2)
    print("Data saved: two_body_results.json")

    # Summary
    print("\n" + "=" * 70)
    print("TWO-BODY RESULTS")
    print("=" * 70)
    E_pass = abs(n_E + 1) < 0.15
    F_pass = abs(n_F + 2) < 0.3
    print(f"  Energy exponent: {n_E:.4f} (expect -1.0) {'PASS' if E_pass else 'CHECK'}")
    print(f"  Force exponent:  {n_F:.4f} (expect -2.0) {'PASS' if F_pass else 'CHECK'}")
    print()
    if E_pass and F_pass:
        print("  PASS: Two vortex structures attract with F ~ 1/d^2")
        print("  Newton's law of gravitation emerges from medium coupling.")
    else:
        print("  Results need investigation.")
        print("  (Possible causes: insufficient separation, grid artifacts)")
    print("=" * 70)


if __name__ == "__main__":
    main()
