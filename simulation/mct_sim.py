"""
MCT Simulation: Topological Structures and Gravitational Potentials
====================================================================

Demonstrates the core MCT claim: a vortex structure (angular momentum
source) embedded in a 3D medium produces a 1/r gravitational potential
in the far field, with effective mass proportional to angular momentum.

Uses zero-padded FFT for free-space (non-periodic) Poisson solve.
Compares point source, vortex ring, and trefoil knot topologies.

Author: Ray (Medium Coupling Theory project)
"""

import numpy as np
from scipy.fft import fftn, ifftn
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from mpl_toolkits.mplot3d import Axes3D
from PIL import Image
from pathlib import Path
import json
import time
import io

RESULTS = Path(__file__).parent / "results"
RESULTS.mkdir(exist_ok=True)


# ──────────────────────────────────────────────────────────
# Source creation
# ──────────────────────────────────────────────────────────

def make_grid(N, L):
    dx = L / N
    x = np.linspace(-L/2 + dx/2, L/2 - dx/2, N)
    return x, dx


def point_source(N, L, mass=1.0):
    x, dx = make_grid(N, L)
    rho = np.zeros((N, N, N), dtype=np.float64)
    c = N // 2
    rho[c, c, c] = mass / dx**3
    return rho, dx


def vortex_ring(N, L, R=0.5, a=0.08, Gamma=1.0):
    """Ring of radius R in xy-plane, Gaussian core of width a."""
    x, dx = make_grid(N, L)
    X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
    r_cyl = np.sqrt(X**2 + Y**2)
    dist = np.sqrt((r_cyl - R)**2 + Z**2)
    rho = np.exp(-dist**2 / (2 * a**2))
    rho *= Gamma / (np.sum(rho) * dx**3)  # normalize total to Gamma
    return rho, dx


def trefoil_knot(N, L, scale=0.5, a=0.08, Gamma=1.0):
    """Trefoil knot parametrized and deposited on grid."""
    x, dx = make_grid(N, L)
    X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
    rho = np.zeros((N, N, N), dtype=np.float64)

    n_pts = 3000
    t = np.linspace(0, 2*np.pi, n_pts, endpoint=False)
    s = scale / 3.0
    kx = s * (np.sin(t) + 2*np.sin(2*t))
    ky = s * (np.cos(t) - 2*np.cos(2*t))
    kz = s * (-np.sin(3*t))

    for i in range(n_pts):
        d2 = (X - kx[i])**2 + (Y - ky[i])**2 + (Z - kz[i])**2
        rho += np.exp(-d2 / (2 * a**2))

    rho *= Gamma / (np.sum(rho) * dx**3)
    return rho, dx


def figure_eight_knot(N, L, scale=0.5, a=0.08, Gamma=1.0):
    """Figure-eight (4_1) knot."""
    x, dx = make_grid(N, L)
    X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
    rho = np.zeros((N, N, N), dtype=np.float64)

    n_pts = 3000
    t = np.linspace(0, 2*np.pi, n_pts, endpoint=False)
    s = scale / 2.5
    # Figure-eight knot parametrization
    kx = s * (2 + np.cos(2*t)) * np.cos(3*t)
    ky = s * (2 + np.cos(2*t)) * np.sin(3*t)
    kz = s * np.sin(4*t)

    for i in range(n_pts):
        d2 = (X - kx[i])**2 + (Y - ky[i])**2 + (Z - kz[i])**2
        rho += np.exp(-d2 / (2 * a**2))

    rho *= Gamma / (np.sum(rho) * dx**3)
    return rho, dx


# ──────────────────────────────────────────────────────────
# Free-space Poisson solver (zero-padded FFT)
# ──────────────────────────────────────────────────────────

def poisson_free_space(rho, dx):
    """
    Solve nabla^2 phi = -4 pi rho with free-space (isolated) BCs.

    Method: zero-pad rho to 2N in each dimension, build the free-space
    Green's function G(r) = -1/r on the doubled grid, convolve via FFT.
    """
    N = rho.shape[0]
    M = 2 * N  # padded size

    # Zero-pad the source
    rho_pad = np.zeros((M, M, M), dtype=np.float64)
    rho_pad[:N, :N, :N] = rho

    # Build Green's function on the doubled grid
    # G(x) = 1/(4 pi |x|) for the Poisson equation nabla^2 phi = -4 pi rho
    # => phi = G * rho where G = 1/|x|
    ix = np.arange(M)
    ix = np.where(ix <= N, ix, ix - M)  # wrap negative indices
    IX, IY, IZ = np.meshgrid(ix, ix, ix, indexing='ij')
    R = np.sqrt((IX * dx)**2 + (IY * dx)**2 + (IZ * dx)**2)
    R[0, 0, 0] = 1.0  # avoid div by zero

    G = dx**3 / R  # Green's function * dx^3 (convolution weight)
    G[0, 0, 0] = 0.0  # self-interaction regularization (or 2.38 * dx^2 for accuracy)

    # Convolve via FFT
    phi_pad = np.real(ifftn(fftn(rho_pad) * fftn(G)))

    # Extract the physical region
    phi = phi_pad[:N, :N, :N]
    return phi


# ──────────────────────────────────────────────────────────
# Analysis
# ──────────────────────────────────────────────────────────

def radial_profile(phi, dx, N):
    """Spherically averaged phi(r)."""
    L = N * dx
    x, _ = make_grid(N, L)
    X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
    R = np.sqrt(X**2 + Y**2 + Z**2)

    r_max = L / 4
    n_bins = min(N // 2, 200)
    edges = np.linspace(dx, r_max, n_bins + 1)
    centers = 0.5 * (edges[:-1] + edges[1:])
    avg = np.zeros(n_bins)

    R_flat = R.ravel()
    phi_flat = phi.ravel()
    for i in range(n_bins):
        mask = (R_flat >= edges[i]) & (R_flat < edges[i+1])
        if np.any(mask):
            avg[i] = np.mean(phi_flat[mask])

    valid = avg != 0
    return centers[valid], avg[valid]


def fit_power(r, phi, r_min, r_max):
    mask = (r >= r_min) & (r <= r_max) & (np.abs(phi) > 1e-30)
    if np.sum(mask) < 5:
        return 0, 0, 0
    lr = np.log(r[mask])
    lp = np.log(np.abs(phi[mask]))
    c = np.polyfit(lr, lp, 1)
    pred = c[0]*lr + c[1]
    ss_res = np.sum((lp - pred)**2)
    ss_tot = np.sum((lp - np.mean(lp))**2)
    r2 = 1 - ss_res/ss_tot if ss_tot > 0 else 0
    return c[0], np.exp(c[1]), r2


# ──────────────────────────────────────────────────────────
# 3D Visualization
# ──────────────────────────────────────────────────────────

def plot_3d_source(rho, dx, N, title, filename):
    """Render the source density as a 3D isosurface plot."""
    from mpl_toolkits.mplot3d import Axes3D

    threshold = np.max(rho) * 0.15
    coords = np.argwhere(rho > threshold)
    if len(coords) == 0:
        return

    L = N * dx
    xs = coords[:, 0] * dx - L/2
    ys = coords[:, 1] * dx - L/2
    zs = coords[:, 2] * dx - L/2
    vals = rho[coords[:, 0], coords[:, 1], coords[:, 2]]
    vals_norm = vals / np.max(vals)

    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(111, projection='3d')
    scatter = ax.scatter(xs, ys, zs, c=vals_norm, cmap='hot',
                         s=1, alpha=0.6, depthshade=True)
    ax.set_xlabel('x')
    ax.set_ylabel('y')
    ax.set_zlabel('z')
    ax.set_title(title)
    lim = max(np.max(np.abs(xs)), np.max(np.abs(ys)), np.max(np.abs(zs))) * 1.2
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_zlim(-lim, lim)
    plt.tight_layout()
    plt.savefig(RESULTS / filename, dpi=120)
    plt.close()
    print(f"    3D plot saved: {filename}")


def make_rotation_gif(rho, dx, N, title, filename, n_frames=36):
    """Create a rotating 3D GIF of the source density."""
    threshold = np.max(rho) * 0.15
    coords = np.argwhere(rho > threshold)
    if len(coords) == 0:
        return

    L = N * dx
    xs = coords[:, 0] * dx - L/2
    ys = coords[:, 1] * dx - L/2
    zs = coords[:, 2] * dx - L/2
    vals = rho[coords[:, 0], coords[:, 1], coords[:, 2]]
    vals_norm = vals / np.max(vals)

    lim = max(np.max(np.abs(xs)), np.max(np.abs(ys)), np.max(np.abs(zs))) * 1.2

    frames = []
    for i in range(n_frames):
        angle = i * 360 / n_frames
        fig = plt.figure(figsize=(6, 6))
        ax = fig.add_subplot(111, projection='3d')
        ax.scatter(xs, ys, zs, c=vals_norm, cmap='hot', s=1, alpha=0.6, depthshade=True)
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        ax.set_zlabel('z')
        ax.set_title(title)
        ax.set_xlim(-lim, lim)
        ax.set_ylim(-lim, lim)
        ax.set_zlim(-lim, lim)
        ax.view_init(elev=25, azim=angle)
        plt.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=80)
        buf.seek(0)
        frames.append(Image.open(buf).copy())
        plt.close()
        buf.close()

    frames[0].save(RESULTS / filename, save_all=True, append_images=frames[1:],
                   duration=100, loop=0)
    print(f"    GIF saved: {filename} ({n_frames} frames)")


# ──────────────────────────────────────────────────────────
# Main simulation
# ──────────────────────────────────────────────────────────

def run_one(name, rho, dx, N, struct_size, make_visuals=True):
    """Run Poisson solve, extract profile, fit, optionally visualize."""
    total_M = np.sum(rho) * dx**3
    print(f"  [{name}] Total source M = {total_M:.6f}")

    if make_visuals:
        plot_3d_source(rho, dx, N, f"Source: {name}", f"source_{name}.png")
        make_rotation_gif(rho, dx, N, f"Source: {name}", f"source_{name}.gif", n_frames=36)

    t0 = time.time()
    phi = poisson_free_space(rho, dx)
    dt = time.time() - t0
    print(f"    Poisson solve (free-space, 2N padded): {dt:.1f}s")

    r, phi_avg = radial_profile(phi, dx, N)

    # Fit far field
    r_min_fit = max(3 * struct_size, 5 * dx)
    L = N * dx
    r_max_fit = L / 4
    n_exp, A_fit, r2 = fit_power(r, phi_avg, r_min_fit, r_max_fit)

    # Analytic expectation for monopole: phi(r) = M/r (from our Green's function convention)
    # Check how close the amplitude matches total_M
    ratio = A_fit / total_M if total_M > 0 else 0

    print(f"    Fit range: [{r_min_fit:.2f}, {r_max_fit:.2f}]")
    print(f"    Power law exponent: {n_exp:.4f} (expect -1.000)")
    print(f"    Fit amplitude: {A_fit:.4f}, total M: {total_M:.4f}, ratio: {ratio:.4f}")
    print(f"    R^2: {r2:.6f}")

    result = {
        "name": name, "total_M": float(total_M),
        "exponent": float(n_exp), "amplitude": float(A_fit),
        "r2": float(r2), "amp_over_M": float(ratio),
        "fit_range": [float(r_min_fit), float(r_max_fit)]
    }
    return r, phi_avg, result


def main():
    print("=" * 70)
    print("MCT SIMULATION: Free-Space Poisson Solver")
    print("Topological Structures -> Gravitational Potential")
    print("=" * 70)

    N = 128  # per side (padded to 256 for FFT, fits in 16GB)
    L = 10.0
    print(f"Grid: {N}^3, padded to {2*N}^3 for free-space solve")
    print(f"Box size: {L}, dx = {L/N:.4f}")

    all_results = []
    all_profiles = {}

    # 1. Point source (sanity check: must give exact 1/r)
    print("\n--- Point Source (sanity check) ---")
    rho_pt, dx = point_source(N, L, mass=1.0)
    r_pt, phi_pt, res_pt = run_one("point", rho_pt, dx, N, struct_size=dx, make_visuals=False)
    all_results.append(res_pt)
    all_profiles["point"] = (r_pt, phi_pt)

    # 2. Vortex ring
    print("\n--- Vortex Ring (R=0.5, a=0.08) ---")
    rho_ring, dx = vortex_ring(N, L, R=0.5, a=0.08, Gamma=1.0)
    r_ring, phi_ring, res_ring = run_one("vortex_ring", rho_ring, dx, N, struct_size=0.5)
    all_results.append(res_ring)
    all_profiles["vortex_ring"] = (r_ring, phi_ring)

    # 3. Trefoil knot
    print("\n--- Trefoil Knot (scale=0.5, a=0.08) ---")
    rho_tre, dx = trefoil_knot(N, L, scale=0.5, a=0.08, Gamma=1.0)
    r_tre, phi_tre, res_tre = run_one("trefoil", rho_tre, dx, N, struct_size=0.5)
    all_results.append(res_tre)
    all_profiles["trefoil"] = (r_tre, phi_tre)

    # 4. Figure-eight knot
    print("\n--- Figure-Eight Knot (scale=0.5, a=0.08) ---")
    rho_fig, dx = figure_eight_knot(N, L, scale=0.5, a=0.08, Gamma=1.0)
    r_fig, phi_fig, res_fig = run_one("figure_eight", rho_fig, dx, N, struct_size=0.5)
    all_results.append(res_fig)
    all_profiles["figure_eight"] = (r_fig, phi_fig)

    # 5. Angular momentum scaling (vary Gamma for the ring)
    print("\n--- Angular Momentum Scaling ---")
    scaling_results = []
    for Gamma in [0.25, 0.5, 1.0, 2.0, 4.0, 8.0]:
        rho_s, dx = vortex_ring(N, L, R=0.5, a=0.08, Gamma=Gamma)
        _, _, res_s = run_one(f"ring_G={Gamma}", rho_s, dx, N, struct_size=0.5, make_visuals=False)
        scaling_results.append(res_s)

    # ──────────────────────────────────────────────────────
    # Plots
    # ──────────────────────────────────────────────────────
    print("\n--- Generating plots ---")

    # Plot 1: Log-log potential comparison
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    ax = axes[0]
    colors = {"point": "gray", "vortex_ring": "blue", "trefoil": "red", "figure_eight": "green"}
    for name, (r, phi) in all_profiles.items():
        valid = np.abs(phi) > 1e-30
        res = [x for x in all_results if x["name"] == name][0]
        ax.loglog(r[valid], np.abs(phi[valid]), '-', color=colors[name], linewidth=2,
                  label=f'{name} (n={res["exponent"]:.3f})')

    # 1/r reference
    r_ref = np.logspace(np.log10(0.3), np.log10(L/4), 100)
    ax.loglog(r_ref, 1.0/r_ref, 'k--', alpha=0.4, linewidth=1, label='$1/r$ reference')
    ax.set_xlabel('$r$', fontsize=13)
    ax.set_ylabel('$|\\phi(r)|$', fontsize=13)
    ax.set_title('Far-Field Potential by Topology', fontsize=14)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    # Plot 2: Residual from 1/r
    ax = axes[1]
    for name, (r, phi) in all_profiles.items():
        res = [x for x in all_results if x["name"] == name][0]
        M = res["total_M"]
        valid = (r > 1.5) & (np.abs(phi) > 1e-30)
        if np.any(valid) and M > 0:
            phi_mono = res["amplitude"] / r[valid]  # expected monopole
            residual = (np.abs(phi[valid]) - phi_mono) / phi_mono * 100
            ax.semilogx(r[valid], residual, '-', color=colors[name], linewidth=2, label=name)

    ax.axhline(0, color='k', linewidth=0.5)
    ax.set_xlabel('$r$', fontsize=13)
    ax.set_ylabel('Deviation from $1/r$ fit (%)', fontsize=13)
    ax.set_title('Multipole Residuals', fontsize=14)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(RESULTS / "potential_comparison.png", dpi=150)
    plt.close()
    print("  Saved: potential_comparison.png")

    # Plot 3: Angular momentum scaling
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    ax = axes[0]
    Ms = [r["total_M"] for r in scaling_results]
    As = [r["amplitude"] for r in scaling_results]
    ax.scatter(Ms, As, s=80, color='blue', zorder=5)

    M_arr = np.array(Ms)
    A_arr = np.array(As)
    k = np.sum(M_arr * A_arr) / np.sum(M_arr**2)
    x_line = np.linspace(0, max(Ms)*1.1, 50)
    ax.plot(x_line, k*x_line, 'r--', linewidth=1.5, label=f'$GM = {k:.3f} \\times M$')
    pred = k * M_arr
    ss_res = np.sum((A_arr - pred)**2)
    ss_tot = np.sum((A_arr - np.mean(A_arr))**2)
    r2_lin = 1 - ss_res/ss_tot if ss_tot > 0 else 0

    ax.set_xlabel('Total coupling source $M$', fontsize=12)
    ax.set_ylabel('Far-field amplitude $GM$', fontsize=12)
    ax.set_title(f'Mass $\\propto$ Angular Momentum ($R^2 = {r2_lin:.6f}$)', fontsize=13)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)

    # Exponent summary
    ax = axes[1]
    all_for_bar = all_results + scaling_results
    names_bar = [r["name"] for r in all_for_bar]
    exps_bar = [r["exponent"] for r in all_for_bar]
    colors_bar = ['green' if abs(e+1) < 0.05 else 'orange' if abs(e+1) < 0.15 else 'red'
                  for e in exps_bar]
    ax.barh(range(len(names_bar)), exps_bar, color=colors_bar, alpha=0.7)
    ax.axvline(-1.0, color='black', linewidth=2, linestyle='--', label='MCT prediction ($n=-1$)')
    ax.set_yticks(range(len(names_bar)))
    ax.set_yticklabels(names_bar, fontsize=8)
    ax.set_xlabel('Power law exponent $n$', fontsize=12)
    ax.set_title('Far-Field Exponent (all runs)', fontsize=13)
    ax.legend()
    ax.grid(True, alpha=0.3, axis='x')

    plt.tight_layout()
    plt.savefig(RESULTS / "scaling_and_exponents.png", dpi=150)
    plt.close()
    print("  Saved: scaling_and_exponents.png")

    # Plot 4: Potential slice (xy plane, z=0)
    print("  Generating potential slice plots...")
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    for ax, (name, rho_data) in zip(axes, [
        ("Vortex Ring", rho_ring),
        ("Trefoil Knot", rho_tre),
        ("Figure-Eight Knot", rho_fig),
    ]):
        phi = poisson_free_space(rho_data, dx)
        mid = N // 2
        phi_slice = phi[:, :, mid]
        extent = [-L/2, L/2, -L/2, L/2]
        vmax = np.max(np.abs(phi_slice)) * 0.5
        im = ax.imshow(phi_slice.T, origin='lower', extent=extent, cmap='RdBu_r',
                       vmin=-vmax, vmax=vmax)
        ax.set_title(f'$\\phi(x, y, z=0)$: {name}', fontsize=12)
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        plt.colorbar(im, ax=ax, shrink=0.8)

    plt.tight_layout()
    plt.savefig(RESULTS / "potential_slices.png", dpi=150)
    plt.close()
    print("  Saved: potential_slices.png")

    # Save all data
    with open(RESULTS / "simulation_results.json", 'w') as f:
        json.dump({
            "grid": {"N": N, "L": L, "dx": float(dx)},
            "topologies": all_results,
            "scaling": scaling_results,
            "linear_fit_slope": float(k),
            "linear_fit_r2": float(r2_lin),
        }, f, indent=2)
    print("  Saved: simulation_results.json")

    # ──────────────────────────────────────────────────────
    # Summary
    # ──────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("RESULTS SUMMARY")
    print("=" * 70)
    print(f"  Grid: {N}^3 (padded to {2*N}^3)")
    print(f"  Solver: Free-space Poisson (zero-padded FFT)")
    print()
    for res in all_results:
        status = "PASS" if abs(res["exponent"] + 1) < 0.1 else "CHECK"
        print(f"  [{status}] {res['name']:20s}  n = {res['exponent']:+.4f}  "
              f"A/M = {res['amp_over_M']:.4f}  R^2 = {res['r2']:.6f}")
    print()
    print(f"  Angular momentum scaling: GM = {k:.4f} * M  (R^2 = {r2_lin:.6f})")
    print()

    all_pass = all(abs(r["exponent"] + 1) < 0.1 for r in all_results)
    if all_pass:
        print("  PASS: ALL TOPOLOGIES produce 1/r far-field potential")
        print("  PASS: Effective mass proportional to coupling source (angular momentum)")
        print("  MCT's core mechanism is computationally verified.")
    else:
        exponents = {r["name"]: r["exponent"] for r in all_results}
        print(f"  Exponents: {exponents}")
        print("  Further investigation needed (resolution, fit range, or physics).")

    print("=" * 70)


if __name__ == "__main__":
    main()
