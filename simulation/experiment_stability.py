"""
RIGOROUS EXPERIMENT: Does MCT Coupling Stabilize Vortex Structures?
=====================================================================

QUESTION: In pure Navier-Stokes, all vortex structures dissipate from
viscosity. MCT claims particles are stable topological structures. Does
the coupling feedback (vorticity -> gravity -> force on fluid) slow the
dissipation? Does it stabilize certain topologies more than others?

PROTOCOL:
  For each of 4 topologies (ring, trefoil, figure-eight, hopf link):
    Run A: coupling OFF (alpha=0), pure Navier-Stokes
    Run B: coupling ON  (alpha=0.05)
    Run C: coupling ON  (alpha=0.15), stronger

  All runs: identical initial conditions, 2000 steps, same viscosity.

MEASUREMENTS (every 10 steps):
  - Enstrophy (total vorticity squared, measures structure strength)
  - Kinetic energy
  - Maximum vorticity (peak structure intensity)
  - Coupling potential energy (integral of omega * phi)
  - Far-field GM (effective gravitational mass)

WHAT WOULD BE SIGNIFICANT:
  - If coupling slows enstrophy decay: the feedback stabilizes structures.
    This is genuinely new, pure NS cannot do this.
  - If coupling accelerates decay: the feedback destabilizes structures.
    This would be a problem for MCT.
  - If no difference: coupling has no dynamical effect. Disappointing
    but honest.
  - If the effect is topology-dependent: some knots are stabilized more
    than others. This would predict which particles are more stable.

WHAT WOULD BE TRIVIAL (don't overclaim):
  - GM scaling with alpha (linear by construction)
  - Different topologies having different initial GM (geometric fact)

SELF-CRITICISM (things that could invalidate results):
  - The coupling force (alpha * grad(phi)) adds energy to the system.
    If enstrophy is higher with coupling, it might just be because we
    injected energy, not because the structure is stabilized. Must check
    by comparing kinetic energy too.
  - Periodic boundary conditions create image interactions. The
    "stabilization" could be an artifact of the structure interacting
    with its own periodic images through the coupling potential.
  - The spectral method imposes smoothness. Real topological stability
    requires the knot to resist reconnection, which spectral methods
    cannot capture (no sharp features). Any stability we see is about
    the smooth vorticity envelope, not true topological protection.
  - 128^3 resolution may be too coarse. Need to verify any positive
    result at 256^3 (resolution study).
  - 2000 steps (t=4.0) may not be long enough to see topology-dependent
    effects if the characteristic timescale is longer.

STEELMAN FOR STANDARD PHYSICS:
  - A body force proportional to vorticity (which is what the coupling
    term effectively is) will naturally slow vorticity decay because it
    converts potential energy back to kinetic energy. This is just
    forced turbulence, not a novel stabilization mechanism. The Poisson
    equation is linear, so this is equivalent to adding a vorticity-
    dependent forcing. Standard forced-turbulence results may apply.
  - If this IS just forced turbulence, then the "mass" is just the
    forcing amplitude, and "mass depends on topology" just means
    "the forcing depends on the source shape." Not new.
"""

import taichi as ti
import numpy as np
import cupy as cp
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
from pathlib import Path
import json
import io
import time

ti.init(arch=ti.cuda, default_fp=ti.f64)

RESULTS = Path(__file__).parent / "results"
RESULTS.mkdir(exist_ok=True)

N = 128
L = 2.0 * np.pi
dx = L / N
dt = 0.002
nu = 0.008
N_STEPS = 2000
MEASURE_EVERY = 10

# ── Taichi Biot-Savart ──
max_pts = 500
fil_x = ti.field(dtype=ti.f64, shape=max_pts)
fil_y = ti.field(dtype=ti.f64, shape=max_pts)
fil_z = ti.field(dtype=ti.f64, shape=max_pts)
fil_dlx = ti.field(dtype=ti.f64, shape=max_pts)
fil_dly = ti.field(dtype=ti.f64, shape=max_pts)
fil_dlz = ti.field(dtype=ti.f64, shape=max_pts)
vel_x = ti.field(dtype=ti.f64, shape=(N, N, N))
vel_y = ti.field(dtype=ti.f64, shape=(N, N, N))
vel_z = ti.field(dtype=ti.f64, shape=(N, N, N))


@ti.kernel
def biot_savart_kernel(n_pts: ti.i32, Gamma: ti.f64, core_a: ti.f64,
                       box_L: ti.f64, grid_N: ti.i32):
    grid_dx = box_L / grid_N
    for i, j, k in ti.ndrange(grid_N, grid_N, grid_N):
        px = i * grid_dx; py = j * grid_dx; pz = k * grid_dx
        ux_sum = 0.0; uy_sum = 0.0; uz_sum = 0.0
        for p in range(n_pts):
            rx = px - fil_x[p]; ry = py - fil_y[p]; rz = pz - fil_z[p]
            rx -= box_L * ti.round(rx / box_L)
            ry -= box_L * ti.round(ry / box_L)
            rz -= box_L * ti.round(rz / box_L)
            r2 = rx*rx + ry*ry + rz*rz + core_a*core_a
            r3i = 1.0 / (r2 * ti.sqrt(r2))
            ux_sum += (fil_dly[p]*rz - fil_dlz[p]*ry) * r3i
            uy_sum += (fil_dlz[p]*rx - fil_dlx[p]*rz) * r3i
            uz_sum += (fil_dlx[p]*ry - fil_dly[p]*rx) * r3i
        c = Gamma / (4.0 * 3.14159265358979323846)
        vel_x[i, j, k] = ux_sum * c
        vel_y[i, j, k] = uy_sum * c
        vel_z[i, j, k] = uz_sum * c


def make_ring(center, R=0.8, n_pts=200):
    t = np.linspace(0, 2*np.pi, n_pts, endpoint=False)
    return center[0]+R*np.cos(t), center[1]+R*np.sin(t), np.full(n_pts, center[2])

def make_trefoil(center, scale=1.0, n_pts=300):
    t = np.linspace(0, 2*np.pi, n_pts, endpoint=False)
    s = scale/3.0
    return (center[0]+s*(np.sin(t)+2*np.sin(2*t)),
            center[1]+s*(np.cos(t)-2*np.cos(2*t)),
            center[2]+s*(-np.sin(3*t)))

def make_figure_eight(center, scale=1.0, n_pts=300):
    t = np.linspace(0, 2*np.pi, n_pts, endpoint=False)
    s = scale/2.5
    return (center[0]+s*(2+np.cos(2*t))*np.cos(3*t),
            center[1]+s*(2+np.cos(2*t))*np.sin(3*t),
            center[2]+s*np.sin(4*t))

def make_hopf_link(center, scale=1.0, n_pts=150):
    t = np.linspace(0, 2*np.pi, n_pts, endpoint=False)
    R = scale*0.5
    x1=center[0]+R*np.cos(t); y1=center[1]+R*np.sin(t); z1=np.full(n_pts, center[2])
    x2=center[0]+R/2+R*np.cos(t); y2=np.full(n_pts, center[1]); z2=center[2]+R*np.sin(t)
    return np.concatenate([x1,x2]), np.concatenate([y1,y2]), np.concatenate([z1,z2])


def init_velocity(curve_func, center, Gamma=2.0, core_a=0.2):
    """Initialize velocity field from a knot curve. Returns numpy arrays."""
    cx, cy, cz = curve_func(center)
    n = len(cx)
    dlx = np.roll(cx,-1)-cx; dly = np.roll(cy,-1)-cy; dlz = np.roll(cz,-1)-cz
    pad = lambda a: np.pad(a, (0, max_pts-n))
    fil_x.from_numpy(pad(cx)); fil_y.from_numpy(pad(cy)); fil_z.from_numpy(pad(cz))
    fil_dlx.from_numpy(pad(dlx)); fil_dly.from_numpy(pad(dly)); fil_dlz.from_numpy(pad(dlz))
    vel_x.fill(0); vel_y.fill(0); vel_z.fill(0)
    biot_savart_kernel(n, Gamma, core_a, L, N)
    ti.sync()
    return vel_x.to_numpy(), vel_y.to_numpy(), vel_z.to_numpy()


# ── GPU Solver ──
class Solver:
    def __init__(self):
        k = np.fft.fftfreq(N, d=L/(2*np.pi*N))
        KX, KY, KZ = np.meshgrid(k, k, k, indexing='ij')
        self.KX = cp.asarray(KX); self.KY = cp.asarray(KY); self.KZ = cp.asarray(KZ)
        self.K2 = self.KX**2 + self.KY**2 + self.KZ**2
        self.K2s = self.K2.copy(); self.K2s[0,0,0] = 1.0
        self.visc = cp.exp(-nu * self.K2 * dt)

    def step(self, ux, uy, uz, alpha_val):
        uxh = cp.fft.fftn(ux); uyh = cp.fft.fftn(uy); uzh = cp.fft.fftn(uz)
        wx = cp.real(cp.fft.ifftn(1j*self.KY*uzh - 1j*self.KZ*uyh))
        wy = cp.real(cp.fft.ifftn(1j*self.KZ*uxh - 1j*self.KX*uzh))
        wz = cp.real(cp.fft.ifftn(1j*self.KX*uyh - 1j*self.KY*uxh))
        omega = cp.sqrt(wx**2 + wy**2 + wz**2)

        if alpha_val > 0:
            rh = cp.fft.fftn(omega)
            ph = -4*cp.pi*alpha_val * rh / self.K2s; ph[0,0,0] = 0
            phi = cp.real(cp.fft.ifftn(ph))
            gx = -cp.real(cp.fft.ifftn(1j*self.KX*ph))
            gy = -cp.real(cp.fft.ifftn(1j*self.KY*ph))
            gz = -cp.real(cp.fft.ifftn(1j*self.KZ*ph))
        else:
            phi = cp.zeros_like(omega)
            gx = gy = gz = cp.zeros_like(omega)

        rhsx = (wy*uz-wz*uy)+gx; rhsy = (wz*ux-wx*uz)+gy; rhsz = (wx*uy-wy*ux)+gz
        uxh2 = cp.fft.fftn(ux)+dt*cp.fft.fftn(rhsx)
        uyh2 = cp.fft.fftn(uy)+dt*cp.fft.fftn(rhsy)
        uzh2 = cp.fft.fftn(uz)+dt*cp.fft.fftn(rhsz)
        uxh2 *= self.visc; uyh2 *= self.visc; uzh2 *= self.visc
        div = self.KX*uxh2+self.KY*uyh2+self.KZ*uzh2
        uxh2 -= self.KX*div/self.K2s; uyh2 -= self.KY*div/self.K2s; uzh2 -= self.KZ*div/self.K2s
        uxh2[0,0,0]=0; uyh2[0,0,0]=0; uzh2[0,0,0]=0

        ux = cp.clip(cp.real(cp.fft.ifftn(uxh2)), -20, 20)
        uy = cp.clip(cp.real(cp.fft.ifftn(uyh2)), -20, 20)
        uz = cp.clip(cp.real(cp.fft.ifftn(uzh2)), -20, 20)
        return ux, uy, uz, omega, phi

    def measure(self, ux, uy, uz, alpha_val):
        """Compute all diagnostics without stepping."""
        uxh = cp.fft.fftn(ux); uyh = cp.fft.fftn(uy); uzh = cp.fft.fftn(uz)
        wx = cp.real(cp.fft.ifftn(1j*self.KY*uzh - 1j*self.KZ*uyh))
        wy = cp.real(cp.fft.ifftn(1j*self.KZ*uxh - 1j*self.KX*uzh))
        wz = cp.real(cp.fft.ifftn(1j*self.KX*uyh - 1j*self.KY*uxh))
        omega = cp.sqrt(wx**2 + wy**2 + wz**2)

        KE = float(0.5 * cp.sum(ux**2 + uy**2 + uz**2).get()) * dx**3
        enstrophy = float(0.5 * cp.sum(omega**2).get()) * dx**3
        omega_max = float(cp.max(omega).get())

        # Coupling potential energy: integral of omega * phi
        if alpha_val > 0:
            rh = cp.fft.fftn(omega)
            ph = -4*cp.pi*alpha_val * rh / self.K2s; ph[0,0,0] = 0
            phi = cp.real(cp.fft.ifftn(ph))
            PE_coupling = float(cp.sum(omega * phi).get()) * dx**3
        else:
            PE_coupling = 0.0

        return {
            'KE': KE,
            'enstrophy': enstrophy,
            'omega_max': omega_max,
            'PE_coupling': PE_coupling,
        }


def run_experiment(topo_name, curve_func, alpha_val, label):
    """Run one experiment: one topology, one coupling value, 2000 steps."""
    center = [L/2, L/2, L/2]
    ux_np, uy_np, uz_np = init_velocity(curve_func, center)

    solver = Solver()
    ux_g = cp.asarray(ux_np); uy_g = cp.asarray(uy_np); uz_g = cp.asarray(uz_np)

    measurements = []
    t0 = time.time()

    for s in range(N_STEPS + 1):
        if s % MEASURE_EVERY == 0:
            m = solver.measure(ux_g, uy_g, uz_g, alpha_val)
            m['step'] = s
            m['time'] = s * dt
            measurements.append(m)

        if s < N_STEPS:
            ux_g, uy_g, uz_g, _, _ = solver.step(ux_g, uy_g, uz_g, alpha_val)

    elapsed = time.time() - t0
    print(f"    {label}: {elapsed:.1f}s  "
          f"enstrophy {measurements[0]['enstrophy']:.2f} -> {measurements[-1]['enstrophy']:.2f}  "
          f"ratio {measurements[-1]['enstrophy']/measurements[0]['enstrophy']:.4f}")

    return measurements


def main():
    print("="*70)
    print("RIGOROUS EXPERIMENT: Does MCT Coupling Stabilize Structures?")
    print(f"Grid: {N}^3, dt={dt}, nu={nu}, {N_STEPS} steps")
    print(f"Control: alpha=0 (pure NS)")
    print(f"Test A:  alpha=0.05")
    print(f"Test B:  alpha=0.15")
    print("="*70)

    topologies = [
        ("ring",         make_ring),
        ("trefoil",      make_trefoil),
        ("figure_eight", make_figure_eight),
        ("hopf_link",    make_hopf_link),
    ]

    alphas = [0.0, 0.05, 0.15]
    alpha_labels = ["control (alpha=0)", "alpha=0.05", "alpha=0.15"]

    all_results = {}

    for topo_name, curve_func in topologies:
        print(f"\n  [{topo_name}]")
        all_results[topo_name] = {}

        for alpha_val, alpha_label in zip(alphas, alpha_labels):
            measurements = run_experiment(topo_name, curve_func, alpha_val, alpha_label)
            all_results[topo_name][f"alpha_{alpha_val:.2f}"] = measurements

    # ── Analysis ──
    print("\n" + "="*70)
    print("ANALYSIS")
    print("="*70)

    # For each topology, compare enstrophy decay rates
    fig, axes = plt.subplots(2, 4, figsize=(24, 10))

    colors = {'alpha_0.00': '#cc2222', 'alpha_0.05': '#2222cc', 'alpha_0.15': '#22aa22'}
    labels_map = {'alpha_0.00': 'No coupling ($\\alpha=0$)',
                  'alpha_0.05': '$\\alpha=0.05$',
                  'alpha_0.15': '$\\alpha=0.15$'}

    summary = {}

    for idx, (topo_name, _) in enumerate(topologies):
        results = all_results[topo_name]

        # Top row: enstrophy over time
        ax = axes[0][idx]
        for key in ['alpha_0.00', 'alpha_0.05', 'alpha_0.15']:
            data = results[key]
            steps = [d['step'] for d in data]
            ens = [d['enstrophy'] for d in data]
            ax.plot(steps, ens, color=colors[key], linewidth=2, label=labels_map[key])

        ax.set_xlabel('Step', fontsize=11)
        ax.set_ylabel('Enstrophy', fontsize=11)
        ax.set_title(f'{topo_name}', fontsize=13, fontweight='bold')
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)

        # Bottom row: enstrophy RATIO (coupled / uncoupled)
        ax = axes[1][idx]
        control = results['alpha_0.00']
        for key in ['alpha_0.05', 'alpha_0.15']:
            data = results[key]
            ens_ctrl = [d['enstrophy'] for d in control]
            ens_test = [d['enstrophy'] for d in data]
            steps = [d['step'] for d in data]

            # Ratio: if > 1, coupling PRESERVES structure; if < 1, coupling DESTROYS
            ratio = [t/c if c > 1e-10 else 1.0 for t, c in zip(ens_test, ens_ctrl)]
            ax.plot(steps, ratio, color=colors[key], linewidth=2, label=labels_map[key])

            # Compute late-time average ratio
            late = ratio[len(ratio)//2:]
            avg_ratio = np.mean(late)
            summary[f"{topo_name}_{key}"] = avg_ratio

        ax.axhline(1.0, color='black', linestyle='--', linewidth=1, alpha=0.5,
                   label='No difference')
        ax.set_xlabel('Step', fontsize=11)
        ax.set_ylabel('Enstrophy ratio\n(coupled / uncoupled)', fontsize=10)
        ax.set_title(f'{topo_name}: coupling effect', fontsize=12)
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)

    fig.suptitle(
        'Does MCT Coupling Stabilize Vortex Structures?\n'
        'Top: enstrophy decay. Bottom: ratio to uncoupled control (>1 = coupling helps, <1 = coupling hurts)',
        fontsize=14, fontweight='bold', y=1.02
    )
    plt.tight_layout()
    fig.savefig(RESULTS / "experiment_stability.png", dpi=150, bbox_inches='tight')
    plt.close()

    # ── Energy budget ──
    fig2, axes2 = plt.subplots(1, 4, figsize=(24, 5))
    for idx, (topo_name, _) in enumerate(topologies):
        ax = axes2[idx]
        for key in ['alpha_0.00', 'alpha_0.05', 'alpha_0.15']:
            data = all_results[topo_name][key]
            steps = [d['step'] for d in data]
            ke = [d['KE'] for d in data]
            ax.plot(steps, ke, color=colors[key], linewidth=2, label=labels_map[key])
        ax.set_xlabel('Step', fontsize=11)
        ax.set_ylabel('Kinetic Energy', fontsize=11)
        ax.set_title(f'{topo_name}', fontsize=13, fontweight='bold')
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)

    fig2.suptitle('Kinetic Energy Decay: Coupled vs Uncoupled', fontsize=14, fontweight='bold')
    plt.tight_layout()
    fig2.savefig(RESULTS / "experiment_energy.png", dpi=150, bbox_inches='tight')
    plt.close()

    # ── Peak vorticity ──
    fig3, axes3 = plt.subplots(1, 4, figsize=(24, 5))
    for idx, (topo_name, _) in enumerate(topologies):
        ax = axes3[idx]
        for key in ['alpha_0.00', 'alpha_0.05', 'alpha_0.15']:
            data = all_results[topo_name][key]
            steps = [d['step'] for d in data]
            om = [d['omega_max'] for d in data]
            ax.plot(steps, om, color=colors[key], linewidth=2, label=labels_map[key])
        ax.set_xlabel('Step', fontsize=11)
        ax.set_ylabel('Max vorticity', fontsize=11)
        ax.set_title(f'{topo_name}', fontsize=13, fontweight='bold')
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)

    fig3.suptitle('Peak Vorticity: Does Coupling Concentrate or Diffuse?',
                  fontsize=14, fontweight='bold')
    plt.tight_layout()
    fig3.savefig(RESULTS / "experiment_peak_vorticity.png", dpi=150, bbox_inches='tight')
    plt.close()

    # ── Print verdict ──
    print("\nSTABILITY RATIO (coupled enstrophy / uncoupled enstrophy, late-time average)")
    print("  > 1.0 = coupling STABILIZES structure")
    print("  < 1.0 = coupling DESTABILIZES structure")
    print("  = 1.0 = coupling has no effect")
    print()
    for topo_name, _ in topologies:
        for key in ['alpha_0.05', 'alpha_0.15']:
            r = summary[f"{topo_name}_{key}"]
            status = "STABILIZES" if r > 1.005 else "DESTABILIZES" if r < 0.995 else "NO EFFECT"
            print(f"  {topo_name:16s} {key}: ratio = {r:.6f}  -> {status}")

    print()
    # Overall verdict
    stabilizing = sum(1 for v in summary.values() if v > 1.005)
    destabilizing = sum(1 for v in summary.values() if v < 0.995)
    neutral = len(summary) - stabilizing - destabilizing

    if stabilizing > destabilizing and stabilizing > neutral:
        print("VERDICT: Coupling appears to STABILIZE vortex structures.")
        print("  This would be a genuine dynamical effect of the MCT feedback loop.")
        print("  Caveat: need to verify this is not numerical artifact (resolution study).")
    elif destabilizing > stabilizing:
        print("VERDICT: Coupling DESTABILIZES structures.")
        print("  This is a problem for MCT: particles should be stable.")
    else:
        print("VERDICT: Coupling has NO significant effect on stability.")
        print("  The feedback loop does not change the dynamics meaningfully.")
        print("  MCT's coupled equations reduce to standard NS for this regime.")

    # Save raw data
    save_data = {}
    for topo_name in all_results:
        save_data[topo_name] = {}
        for alpha_key in all_results[topo_name]:
            save_data[topo_name][alpha_key] = all_results[topo_name][alpha_key]

    with open(RESULTS / "experiment_stability_data.json", 'w') as f:
        json.dump(save_data, f, indent=2)

    print(f"\nSaved: experiment_stability.png, experiment_energy.png,")
    print(f"       experiment_peak_vorticity.png, experiment_stability_data.json")
    print("="*70)


if __name__ == "__main__":
    main()
