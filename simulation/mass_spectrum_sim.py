"""
MCT Mass Spectrum Simulation
==============================

Run the coupled Navier-Stokes + MCT system for MANY topologies and
extract the effective mass of each. This builds the MCT mass spectrum:
the relationship between knot topology and gravitational mass.

Topologies tested:
  - Vortex ring (unknot, trivial topology)
  - Trefoil knot (3_1, simplest nontrivial)
  - Figure-eight knot (4_1)
  - Torus knot T(2,5) (cinquefoil)
  - Torus knot T(2,7) (7-crossing torus knot)
  - Torus knot T(3,2) (trefoil, different parametrization)
  - Double ring (two linked rings, composite topology)

All initialized with the SAME circulation Gamma. The effective mass
differences come purely from topology.
"""

import numpy as np
from scipy.fft import fftn, ifftn, fftfreq
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
from pathlib import Path
import json
import io
import time

RESULTS = Path(__file__).parent / "results"
RESULTS.mkdir(exist_ok=True)

# Parameters
N = 96
L = 2 * np.pi
dx = L / N
dt = 0.002
nu = 0.008
alpha_coupling = 0.05
N_STEPS = 300
SAVE_EVERY = 50


def make_wavenumbers():
    k = fftfreq(N, d=L/(2*np.pi*N))
    KX, KY, KZ = np.meshgrid(k, k, k, indexing='ij')
    K2 = KX**2 + KY**2 + KZ**2
    K2_safe = K2.copy()
    K2_safe[0,0,0] = 1.0
    return KX, KY, KZ, K2, K2_safe


def biot_savart(curve_x, curve_y, curve_z, Gamma, core_a):
    """Compute velocity field from a filament curve via Biot-Savart (vectorized)."""
    x = np.linspace(0, L, N, endpoint=False)
    X, Y, Z = np.meshgrid(x, x, x, indexing='ij')

    n_pts = len(curve_x)
    dl_x = np.roll(curve_x, -1) - curve_x
    dl_y = np.roll(curve_y, -1) - curve_y
    dl_z = np.roll(curve_z, -1) - curve_z

    ux = np.zeros((N, N, N))
    uy = np.zeros((N, N, N))
    uz = np.zeros((N, N, N))

    # Process in batches to manage memory (batch_size x N^3)
    batch = 10
    for b in range(0, n_pts, batch):
        end = min(b + batch, n_pts)
        for i in range(b, end):
            rx = X - curve_x[i]
            ry = Y - curve_y[i]
            rz = Z - curve_z[i]
            rx -= L * np.round(rx / L)
            ry -= L * np.round(ry / L)
            rz -= L * np.round(rz / L)

            r2 = rx**2 + ry**2 + rz**2 + core_a**2
            r3_inv = 1.0 / (r2**1.5)

            ux += (dl_y[i]*rz - dl_z[i]*ry) * r3_inv
            uy += (dl_z[i]*rx - dl_x[i]*rz) * r3_inv
            uz += (dl_x[i]*ry - dl_y[i]*rx) * r3_inv

    c = Gamma / (4*np.pi)
    return ux*c, uy*c, uz*c


# ── Topology parametrizations ──

def make_ring(center, R, n_pts=100):
    t = np.linspace(0, 2*np.pi, n_pts, endpoint=False)
    return (center[0] + R*np.cos(t),
            center[1] + R*np.sin(t),
            np.full(n_pts, center[2]))


def make_trefoil(center, scale, n_pts=200):
    t = np.linspace(0, 2*np.pi, n_pts, endpoint=False)
    s = scale / 3.0
    return (center[0] + s*(np.sin(t) + 2*np.sin(2*t)),
            center[1] + s*(np.cos(t) - 2*np.cos(2*t)),
            center[2] + s*(-np.sin(3*t)))


def make_figure_eight(center, scale, n_pts=200):
    t = np.linspace(0, 2*np.pi, n_pts, endpoint=False)
    s = scale / 2.5
    return (center[0] + s*(2 + np.cos(2*t))*np.cos(3*t),
            center[1] + s*(2 + np.cos(2*t))*np.sin(3*t),
            center[2] + s*np.sin(4*t))


def make_torus_knot(center, scale, p, q, n_pts=200):
    """Torus knot T(p,q): winds p times around the hole, q times through it."""
    t = np.linspace(0, 2*np.pi, n_pts, endpoint=False)
    r_major = scale * 0.6
    r_minor = scale * 0.3
    return (center[0] + (r_major + r_minor*np.cos(q*t))*np.cos(p*t),
            center[1] + (r_major + r_minor*np.cos(q*t))*np.sin(p*t),
            center[2] + r_minor*np.sin(q*t))


def make_hopf_link(center, scale, n_pts=200):
    """Two linked rings (Hopf link, simplest link)."""
    t = np.linspace(0, 2*np.pi, n_pts, endpoint=False)
    R = scale * 0.5
    # Ring 1: in xy-plane
    x1 = center[0] + R*np.cos(t)
    y1 = center[1] + R*np.sin(t)
    z1 = np.full(n_pts, center[2])
    # Ring 2: in xz-plane, offset by R/2
    x2 = center[0] + R/2 + R*np.cos(t)
    y2 = np.full(n_pts, center[1])
    z2 = center[2] + R*np.sin(t)
    return (np.concatenate([x1, x2]),
            np.concatenate([y1, y2]),
            np.concatenate([z1, z2]))


# ── Simulation core ──

def compute_vorticity(ux, uy, uz, KX, KY, KZ):
    ux_h = fftn(ux); uy_h = fftn(uy); uz_h = fftn(uz)
    wx = np.real(ifftn(1j*KY*uz_h - 1j*KZ*uy_h))
    wy = np.real(ifftn(1j*KZ*ux_h - 1j*KX*uz_h))
    wz = np.real(ifftn(1j*KX*uy_h - 1j*KY*ux_h))
    return np.sqrt(wx**2 + wy**2 + wz**2), wx, wy, wz


def step(ux, uy, uz, KX, KY, KZ, K2, K2_safe):
    omega, wx, wy, wz = compute_vorticity(ux, uy, uz, KX, KY, KZ)

    # MCT coupling
    rho_hat = fftn(omega)
    phi_hat = -4*np.pi*alpha_coupling * rho_hat / K2_safe
    phi_hat[0,0,0] = 0
    gx = -np.real(ifftn(1j*KX*phi_hat))
    gy = -np.real(ifftn(1j*KY*phi_hat))
    gz = -np.real(ifftn(1j*KZ*phi_hat))

    # Lamb vector + coupling force
    rhsx = (wy*uz - wz*uy) + gx
    rhsy = (wz*ux - wx*uz) + gy
    rhsz = (wx*uy - wy*ux) + gz

    ux_h = fftn(ux) + dt*fftn(rhsx)
    uy_h = fftn(uy) + dt*fftn(rhsy)
    uz_h = fftn(uz) + dt*fftn(rhsz)

    visc = np.exp(-nu*K2*dt)
    ux_h *= visc; uy_h *= visc; uz_h *= visc

    div = KX*ux_h + KY*uy_h + KZ*uz_h
    ux_h -= KX*div/K2_safe
    uy_h -= KY*div/K2_safe
    uz_h -= KZ*div/K2_safe
    ux_h[0,0,0] = 0; uy_h[0,0,0] = 0; uz_h[0,0,0] = 0

    ux = np.clip(np.real(ifftn(ux_h)), -20, 20)
    uy = np.clip(np.real(ifftn(uy_h)), -20, 20)
    uz = np.clip(np.real(ifftn(uz_h)), -20, 20)

    phi = np.real(ifftn(phi_hat))
    return ux, uy, uz, phi, omega


def radial_profile(phi, center):
    x = np.linspace(0, L, N, endpoint=False)
    X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
    rx = X - center[0]; ry = Y - center[1]; rz = Z - center[2]
    rx -= L*np.round(rx/L); ry -= L*np.round(ry/L); rz -= L*np.round(rz/L)
    R = np.sqrt(rx**2 + ry**2 + rz**2)
    n_bins = N//3
    edges = np.linspace(dx, L/3, n_bins+1)
    ctrs = 0.5*(edges[:-1]+edges[1:])
    avg = np.zeros(n_bins)
    Rf = R.ravel(); pf = phi.ravel()
    for i in range(n_bins):
        m = (Rf >= edges[i]) & (Rf < edges[i+1])
        if np.any(m): avg[i] = np.mean(pf[m])
    v = avg != 0
    return ctrs[v], avg[v]


def fit_power(r, phi, r_min, r_max):
    m = (r >= r_min) & (r <= r_max) & (np.abs(phi) > 1e-30)
    if np.sum(m) < 5: return 0, 0, 0
    lr = np.log(r[m]); lp = np.log(np.abs(phi[m]))
    c = np.polyfit(lr, lp, 1)
    pred = c[0]*lr + c[1]
    ss_r = np.sum((lp-pred)**2); ss_t = np.sum((lp-np.mean(lp))**2)
    return c[0], np.exp(c[1]), (1-ss_r/ss_t if ss_t > 0 else 0)


def run_topology(name, curve_func, curve_args, Gamma=2.0, core_a=0.2):
    """Run coupled simulation for one topology, return final effective mass."""
    center = [L/2, L/2, L/2]
    print(f"\n  [{name}] Generating Biot-Savart field...", end="", flush=True)
    t0 = time.time()

    cx, cy, cz = curve_func(*curve_args)
    ux, uy, uz = biot_savart(cx, cy, cz, Gamma, core_a)
    print(f" {time.time()-t0:.1f}s")

    KX, KY, KZ, K2, K2_safe = make_wavenumbers()

    # Collect frames for GIF
    frames = []
    exponents = []
    amplitudes = []

    for s in range(N_STEPS + 1):
        omega, _, _, _ = compute_vorticity(ux, uy, uz, KX, KY, KZ)
        rho_hat = fftn(omega)
        phi_hat = -4*np.pi*alpha_coupling * rho_hat / K2_safe
        phi_hat[0,0,0] = 0
        phi = np.real(ifftn(phi_hat))

        r, phi_avg = radial_profile(phi, center)
        n_exp, A, r2 = fit_power(r, phi_avg, 0.4, L/3)
        exponents.append(n_exp)
        amplitudes.append(A)

        if s % SAVE_EVERY == 0:
            KE = 0.5*np.sum(ux**2+uy**2+uz**2)*dx**3
            ens = 0.5*np.sum(omega**2)*dx**3
            print(f"    step {s:4d}: KE={KE:.3f} ens={ens:.1f} n={n_exp:+.3f} GM={A:.4f}")

            # Frame for GIF: 3D vorticity + potential slice
            fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))

            # Vorticity slice
            mid = N//2
            ax = axes[0]
            im = ax.imshow(omega[:,:,mid].T, origin='lower', extent=[0,L,0,L], cmap='inferno')
            ax.set_title(f'{name}: vorticity (step {s})', fontsize=11)
            ax.set_xlabel('x'); ax.set_ylabel('y')
            plt.colorbar(im, ax=ax, shrink=0.8)

            # Potential slice
            ax = axes[1]
            vmax = max(np.max(np.abs(phi[:,:,mid]))*0.7, 1e-6)
            im = ax.imshow(phi[:,:,mid].T, origin='lower', extent=[0,L,0,L],
                          cmap='RdBu_r', vmin=-vmax, vmax=vmax)
            ax.set_title(f'MCT potential $\\phi$ (step {s})', fontsize=11)
            ax.set_xlabel('x'); ax.set_ylabel('y')
            plt.colorbar(im, ax=ax, shrink=0.8)

            # Radial profile
            ax = axes[2]
            if len(r) > 3 and np.any(np.abs(phi_avg) > 1e-30):
                v = np.abs(phi_avg) > 1e-30
                ax.loglog(r[v], np.abs(phi_avg[v]), 'b-', lw=2, label='Simulation')
                rr = r[v]
                if A > 0:
                    ax.loglog(rr, A/rr, 'r--', alpha=0.5, label='$1/r$')
                ax.legend(fontsize=9)
            ax.set_title(f'$|\\phi(r)|$: n={n_exp:+.3f}', fontsize=11)
            ax.set_xlabel('r'); ax.set_ylabel('$|\\phi|$')
            ax.grid(True, alpha=0.3)

            plt.suptitle(f'{name} (step {s}/{N_STEPS})', fontsize=13)
            plt.tight_layout()
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=80)
            buf.seek(0)
            frames.append(Image.open(buf).copy())
            plt.close(); buf.close()

        if s < N_STEPS:
            ux, uy, uz, _, _ = step(ux, uy, uz, KX, KY, KZ, K2, K2_safe)

    # Save GIF
    if frames:
        frames[0].save(RESULTS / f"spectrum_{name}.gif", save_all=True,
                       append_images=frames[1:], duration=300, loop=0)
        print(f"    GIF: spectrum_{name}.gif ({len(frames)} frames)")

    # Save first and last frame as PNG
    if frames:
        frames[0].save(RESULTS / f"spectrum_{name}_start.png")
        frames[-1].save(RESULTS / f"spectrum_{name}_final.png")

    # Use late-time average for stable measurement
    n_avg = min(50, len(exponents))
    final_exp = np.mean(exponents[-n_avg:])
    final_amp = np.mean(amplitudes[-n_avg:])
    total_enstrophy = 0.5*np.sum(omega**2)*dx**3

    return {
        "name": name,
        "final_exponent": float(final_exp),
        "final_GM": float(final_amp),
        "final_enstrophy": float(total_enstrophy),
        "crossing_number": get_crossing_number(name),
    }


def get_crossing_number(name):
    mapping = {
        "ring": 0, "trefoil": 3, "figure_eight": 4,
        "T25_cinquefoil": 5, "T27": 7, "hopf_link": 0,
    }
    return mapping.get(name, -1)


def main():
    print("="*70)
    print("MCT MASS SPECTRUM: Effective Mass vs Knot Topology")
    print(f"Grid: {N}^3, steps: {N_STEPS}, alpha={alpha_coupling}, nu={nu}")
    print("="*70)

    center = [L/2, L/2, L/2]
    Gamma = 2.0
    core = 0.2
    scale = 1.0

    topologies = [
        ("ring",           make_ring,         (center, 0.8)),
        ("trefoil",        make_trefoil,      (center, scale)),
        ("figure_eight",   make_figure_eight, (center, scale)),
        ("T25_cinquefoil", make_torus_knot,   (center, scale, 2, 5)),
        ("T27",            make_torus_knot,   (center, scale, 2, 7)),
        ("hopf_link",      make_hopf_link,    (center, scale)),
    ]

    results = []
    for name, func, args in topologies:
        res = run_topology(name, func, args, Gamma=Gamma, core_a=core)
        results.append(res)

    # ── Results summary ──
    print("\n" + "="*70)
    print("MASS SPECTRUM RESULTS")
    print("="*70)
    print(f"  {'Topology':<20s} {'Crossings':>9s} {'Exponent':>10s} {'GM_eff':>10s} {'Enstrophy':>12s}")
    print("  " + "-"*63)
    for r in results:
        print(f"  {r['name']:<20s} {r['crossing_number']:>9d} "
              f"{r['final_exponent']:>+10.3f} {r['final_GM']:>10.4f} "
              f"{r['final_enstrophy']:>12.2f}")

    # Normalize to ring mass
    ring_GM = [r['final_GM'] for r in results if r['name'] == 'ring'][0]
    print(f"\n  Mass ratios (normalized to ring = 1.0):")
    for r in results:
        ratio = r['final_GM'] / ring_GM if ring_GM > 0 else 0
        r['mass_ratio'] = float(ratio)
        print(f"    {r['name']:<20s}: {ratio:.3f}")

    # ── Plot: Mass vs Crossing Number ──
    fig, axes = plt.subplots(1, 3, figsize=(20, 6))

    # Mass vs crossing number
    ax = axes[0]
    cn = [r['crossing_number'] for r in results]
    gm = [r['mass_ratio'] for r in results]
    names = [r['name'] for r in results]
    ax.scatter(cn, gm, s=120, c='blue', zorder=5)
    for i, n in enumerate(names):
        ax.annotate(n, (cn[i], gm[i]), textcoords="offset points",
                    xytext=(5, 8), fontsize=9)
    ax.set_xlabel('Crossing number', fontsize=13)
    ax.set_ylabel('Effective mass (ring = 1)', fontsize=13)
    ax.set_title('MCT Mass Spectrum: Mass vs Topological Complexity', fontsize=13)
    ax.grid(True, alpha=0.3)

    # Mass vs enstrophy
    ax = axes[1]
    ens = [r['final_enstrophy'] for r in results]
    ax.scatter(ens, gm, s=120, c='red', zorder=5)
    for i, n in enumerate(names):
        ax.annotate(n, (ens[i], gm[i]), textcoords="offset points",
                    xytext=(5, 8), fontsize=9)
    # Fit
    if len(ens) > 2:
        ens_arr = np.array(ens); gm_arr = np.array(gm)
        k = np.polyfit(ens_arr, gm_arr, 1)
        x_fit = np.linspace(min(ens)*0.9, max(ens)*1.1, 50)
        ax.plot(x_fit, np.polyval(k, x_fit), 'r--', alpha=0.5)
    ax.set_xlabel('Final enstrophy', fontsize=13)
    ax.set_ylabel('Effective mass (ring = 1)', fontsize=13)
    ax.set_title('Mass vs Angular Momentum Content', fontsize=13)
    ax.grid(True, alpha=0.3)

    # Bar chart of mass ratios
    ax = axes[2]
    sorted_res = sorted(results, key=lambda r: r['mass_ratio'])
    names_sorted = [r['name'] for r in sorted_res]
    ratios_sorted = [r['mass_ratio'] for r in sorted_res]
    colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(sorted_res)))
    ax.barh(range(len(sorted_res)), ratios_sorted, color=colors)
    ax.set_yticks(range(len(sorted_res)))
    ax.set_yticklabels(names_sorted, fontsize=10)
    ax.set_xlabel('Effective mass (ring = 1)', fontsize=13)
    ax.set_title('Mass Spectrum: All Topologies', fontsize=13)
    ax.grid(True, alpha=0.3, axis='x')

    plt.tight_layout()
    plt.savefig(RESULTS / "mass_spectrum.png", dpi=150)
    plt.close()
    print(f"\n  Plot saved: mass_spectrum.png")

    # Save data
    with open(RESULTS / "mass_spectrum_data.json", 'w') as f:
        json.dump({"parameters": {"N": N, "L": L, "dt": dt, "nu": nu,
                                   "alpha": alpha_coupling, "Gamma": Gamma,
                                   "steps": N_STEPS},
                    "results": results}, f, indent=2)
    print(f"  Data saved: mass_spectrum_data.json")
    print("="*70)


if __name__ == "__main__":
    main()
