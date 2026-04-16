"""
EXPERIMENT: Helicity as the True Topological Coupling
======================================================

HYPOTHESIS EVOLUTION:
  Original MCT: mass = |omega| coupling. Failed because |omega| doesn't
  distinguish topologies.

  Revised: mass = HELICITY coupling.

  Helicity H = integral(u . omega) d^3x is the true topological
  invariant of fluid flow:
    - Conserved in ideal (inviscid) flow (Kelvin/Moffatt theorem)
    - Zero for unknotted vortex tubes (rings)
    - Nonzero for knotted tubes (trefoil, figure-eight)
    - Proportional to linking number for linked tubes (Hopf link)
    - H = Gamma^2 * (Writhe + Twist) for a single tube

  If helicity is the coupling source, then:
    - Unknotted rings have ~zero mass (they're "photon-like")
    - Knotted structures have mass proportional to helicity
    - Different knots have different helicity -> mass spectrum

EXPERIMENT PART 1: Measure helicity for all topologies
  Just diagnostic. No coupling change. What IS the helicity?

EXPERIMENT PART 2: Helicity-based viscosity coupling
  nu_eff(x) = nu_0 * (1 - beta * |h(x)| / h_ref)
  where h(x) = u(x) . omega(x) is the helicity density.

  Critical test: does the trefoil (high helicity) now get stabilized
  MORE than the ring (low helicity)?

EXPERIMENT PART 3: Helicity-based Poisson coupling
  Same equations but source for Poisson is |h| not |omega|:
    laplacian(phi) = -4*pi*alpha * |u . omega|

  The gradient force alpha*grad(phi) still gets projected out in
  incompressible flow. BUT: if we use this phi to define the
  "gravitational mass" as a diagnostic, the mass spectrum will
  naturally reflect topology. The question is whether a proper
  compressible formulation with helicity source would produce
  real dynamics.

SELF-CRITICISM:
  - Helicity density h(x) = u.omega is a LOCAL quantity that depends
    on the gauge (velocity decomposition). Total helicity H is gauge-
    invariant but the local density is not. Using local h(x) for
    variable viscosity may introduce gauge artifacts.
  - For a thin vortex tube, H = Gamma^2 * (Writhe + Twist). Writhe
    is a geometric property of the centerline (how it wraps in space).
    Twist is how the cross-section rotates. Both contribute. We
    initialize with Biot-Savart which gives a specific twist, so
    the helicity depends on our initialization, not just topology.
  - A vortex ring CAN have nonzero helicity if it has internal twist
    (like a twisted rubber band formed into a loop). Our initialization
    may or may not produce this. Need to check.
"""

import numpy as np
import cupy as cp
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
import json
import time

import taichi as ti
ti.init(arch=ti.cuda, default_fp=ti.f64)

RESULTS = Path(__file__).parent / "results"
RESULTS.mkdir(exist_ok=True)

N = 128
L = 2.0 * np.pi
dx = L / N
dt = 0.002
nu_0 = 0.01
N_STEPS = 3000
MEASURE_EVERY = 15

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

def make_ring(c, R=0.8, n=200):
    t = np.linspace(0, 2*np.pi, n, endpoint=False)
    return c[0]+R*np.cos(t), c[1]+R*np.sin(t), np.full(n, c[2])

def make_trefoil(c, scale=1.0, n=300):
    t = np.linspace(0, 2*np.pi, n, endpoint=False)
    s = scale/3.0
    return (c[0]+s*(np.sin(t)+2*np.sin(2*t)),
            c[1]+s*(np.cos(t)-2*np.cos(2*t)),
            c[2]+s*(-np.sin(3*t)))

def make_figure_eight(c, scale=1.0, n=300):
    t = np.linspace(0, 2*np.pi, n, endpoint=False)
    s = scale/2.5
    return (c[0]+s*(2+np.cos(2*t))*np.cos(3*t),
            c[1]+s*(2+np.cos(2*t))*np.sin(3*t),
            c[2]+s*np.sin(4*t))

def make_hopf_link(c, scale=1.0, n=150):
    t = np.linspace(0, 2*np.pi, n, endpoint=False)
    R = scale*0.5
    x1=c[0]+R*np.cos(t); y1=c[1]+R*np.sin(t); z1=np.full(n, c[2])
    x2=c[0]+R/2+R*np.cos(t); y2=np.full(n, c[1]); z2=c[2]+R*np.sin(t)
    return np.concatenate([x1,x2]), np.concatenate([y1,y2]), np.concatenate([z1,z2])

def init_velocity(curve_func, center, Gamma=2.0, core_a=0.2):
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


class HelicitySolver:
    def __init__(self):
        k = np.fft.fftfreq(N, d=L/(2*np.pi*N))
        KX, KY, KZ = np.meshgrid(k, k, k, indexing='ij')
        self.KX = cp.asarray(KX); self.KY = cp.asarray(KY); self.KZ = cp.asarray(KZ)
        self.K2 = self.KX**2 + self.KY**2 + self.KZ**2
        self.K2s = self.K2.copy(); self.K2s[0,0,0] = 1.0

    def compute_fields(self, ux, uy, uz):
        """Compute vorticity, helicity density, and totals."""
        uxh = cp.fft.fftn(ux); uyh = cp.fft.fftn(uy); uzh = cp.fft.fftn(uz)
        wx = cp.real(cp.fft.ifftn(1j*self.KY*uzh - 1j*self.KZ*uyh))
        wy = cp.real(cp.fft.ifftn(1j*self.KZ*uxh - 1j*self.KX*uzh))
        wz = cp.real(cp.fft.ifftn(1j*self.KX*uyh - 1j*self.KY*uxh))
        omega = cp.sqrt(wx**2 + wy**2 + wz**2)

        # Helicity density: h = u . omega
        h = ux*wx + uy*wy + uz*wz

        # Totals
        H_total = float(cp.sum(h).get()) * dx**3
        H_abs = float(cp.sum(cp.abs(h)).get()) * dx**3
        enstrophy = float(0.5*cp.sum(omega**2).get()) * dx**3
        KE = float(0.5*cp.sum(ux**2+uy**2+uz**2).get()) * dx**3
        omega_max = float(cp.max(omega).get())
        h_max = float(cp.max(cp.abs(h)).get())

        return {
            'omega': omega, 'wx': wx, 'wy': wy, 'wz': wz,
            'h': h,
            'H_total': H_total,
            'H_abs': H_abs,
            'enstrophy': enstrophy,
            'KE': KE,
            'omega_max': omega_max,
            'h_max': h_max,
        }

    def step_with_helicity_viscosity(self, ux, uy, uz, beta, h_ref):
        """NS step with helicity-dependent viscosity.
        nu_eff(x) = nu_0 * (1 - beta * |h(x)| / h_ref)
        """
        fields = self.compute_fields(ux, uy, uz)
        wx, wy, wz = fields['wx'], fields['wy'], fields['wz']
        h = fields['h']

        # Helicity-dependent viscosity
        h_norm = cp.abs(h) / max(float(h_ref), 1e-10)
        h_norm = cp.minimum(h_norm, 1.0)
        nu_field = nu_0 * (1.0 - beta * h_norm)
        nu_field = cp.maximum(nu_field, nu_0 * 0.05)

        # Nonlinear term
        rhsx = wy*uz - wz*uy
        rhsy = wz*ux - wx*uz
        rhsz = wx*uy - wy*ux

        # Variable viscosity: nu_field * laplacian(u) + grad(nu_field) . grad(u)
        uxh = cp.fft.fftn(ux); uyh = cp.fft.fftn(uy); uzh = cp.fft.fftn(uz)
        lap_ux = cp.real(cp.fft.ifftn(-self.K2*uxh))
        lap_uy = cp.real(cp.fft.ifftn(-self.K2*uyh))
        lap_uz = cp.real(cp.fft.ifftn(-self.K2*uzh))

        nuh = cp.fft.fftn(nu_field)
        gnu_x = cp.real(cp.fft.ifftn(1j*self.KX*nuh))
        gnu_y = cp.real(cp.fft.ifftn(1j*self.KY*nuh))
        gnu_z = cp.real(cp.fft.ifftn(1j*self.KZ*nuh))

        gux_x = cp.real(cp.fft.ifftn(1j*self.KX*uxh))
        gux_y = cp.real(cp.fft.ifftn(1j*self.KY*uxh))
        gux_z = cp.real(cp.fft.ifftn(1j*self.KZ*uxh))
        guy_x = cp.real(cp.fft.ifftn(1j*self.KX*uyh))
        guy_y = cp.real(cp.fft.ifftn(1j*self.KY*uyh))
        guy_z = cp.real(cp.fft.ifftn(1j*self.KZ*uyh))
        guz_x = cp.real(cp.fft.ifftn(1j*self.KX*uzh))
        guz_y = cp.real(cp.fft.ifftn(1j*self.KY*uzh))
        guz_z = cp.real(cp.fft.ifftn(1j*self.KZ*uzh))

        visc_x = nu_field*lap_ux + gnu_x*gux_x + gnu_y*gux_y + gnu_z*gux_z
        visc_y = nu_field*lap_uy + gnu_x*guy_x + gnu_y*guy_y + gnu_z*guy_z
        visc_z = nu_field*lap_uz + gnu_x*guz_x + gnu_y*guz_y + gnu_z*guz_z

        uxh_new = uxh + dt*cp.fft.fftn(rhsx + visc_x)
        uyh_new = uyh + dt*cp.fft.fftn(rhsy + visc_y)
        uzh_new = uzh + dt*cp.fft.fftn(rhsz + visc_z)

        # Projection
        div = self.KX*uxh_new+self.KY*uyh_new+self.KZ*uzh_new
        uxh_new -= self.KX*div/self.K2s
        uyh_new -= self.KY*div/self.K2s
        uzh_new -= self.KZ*div/self.K2s
        uxh_new[0,0,0]=0; uyh_new[0,0,0]=0; uzh_new[0,0,0]=0

        ux = cp.clip(cp.real(cp.fft.ifftn(uxh_new)), -20, 20)
        uy = cp.clip(cp.real(cp.fft.ifftn(uyh_new)), -20, 20)
        uz = cp.clip(cp.real(cp.fft.ifftn(uzh_new)), -20, 20)
        return ux, uy, uz

    def step_control(self, ux, uy, uz):
        """Standard NS step (constant viscosity). Control case."""
        uxh = cp.fft.fftn(ux); uyh = cp.fft.fftn(uy); uzh = cp.fft.fftn(uz)
        wx = cp.real(cp.fft.ifftn(1j*self.KY*uzh - 1j*self.KZ*uyh))
        wy = cp.real(cp.fft.ifftn(1j*self.KZ*uxh - 1j*self.KX*uzh))
        wz = cp.real(cp.fft.ifftn(1j*self.KX*uyh - 1j*self.KY*uxh))

        rhsx = wy*uz-wz*uy; rhsy = wz*ux-wx*uz; rhsz = wx*uy-wy*ux
        visc = cp.exp(-nu_0*self.K2*dt)
        uxh_new = (uxh+dt*cp.fft.fftn(rhsx))*visc
        uyh_new = (uyh+dt*cp.fft.fftn(rhsy))*visc
        uzh_new = (uzh+dt*cp.fft.fftn(rhsz))*visc
        div = self.KX*uxh_new+self.KY*uyh_new+self.KZ*uzh_new
        uxh_new -= self.KX*div/self.K2s
        uyh_new -= self.KY*div/self.K2s
        uzh_new -= self.KZ*div/self.K2s
        uxh_new[0,0,0]=0; uyh_new[0,0,0]=0; uzh_new[0,0,0]=0
        ux = cp.clip(cp.real(cp.fft.ifftn(uxh_new)),-20,20)
        uy = cp.clip(cp.real(cp.fft.ifftn(uyh_new)),-20,20)
        uz = cp.clip(cp.real(cp.fft.ifftn(uzh_new)),-20,20)
        return ux, uy, uz


def run_experiment(topo_name, curve_func, beta, label, solver):
    center = [L/2, L/2, L/2]
    ux_np, uy_np, uz_np = init_velocity(curve_func, center)
    ux_g = cp.asarray(ux_np); uy_g = cp.asarray(uy_np); uz_g = cp.asarray(uz_np)

    # Measure initial helicity
    f0 = solver.compute_fields(ux_g, uy_g, uz_g)
    h_ref = f0['h_max']

    measurements = []
    t0 = time.time()

    for s in range(N_STEPS + 1):
        if s % MEASURE_EVERY == 0:
            f = solver.compute_fields(ux_g, uy_g, uz_g)
            m = {
                'step': s, 'time': s*dt,
                'KE': f['KE'], 'enstrophy': f['enstrophy'],
                'omega_max': f['omega_max'],
                'H_total': f['H_total'], 'H_abs': f['H_abs'],
                'h_max': f['h_max'],
            }
            measurements.append(m)

            if np.isnan(m['enstrophy']):
                print(f"    BLOWUP at step {s}")
                break

        if s < N_STEPS:
            if beta > 0:
                ux_g, uy_g, uz_g = solver.step_with_helicity_viscosity(
                    ux_g, uy_g, uz_g, beta, h_ref)
            else:
                ux_g, uy_g, uz_g = solver.step_control(ux_g, uy_g, uz_g)

    elapsed = time.time() - t0
    ens0 = measurements[0]['enstrophy']
    ensf = measurements[-1]['enstrophy']
    H0 = measurements[0]['H_total']
    Hf = measurements[-1]['H_total']
    print(f"    {label}: {elapsed:.1f}s  ens {ens0:.3f}->{ensf:.3f} "
          f"H {H0:.4f}->{Hf:.4f}")
    return measurements


def main():
    print("="*70)
    print("EXPERIMENT: Helicity as Topological Coupling")
    print(f"Grid: {N}^3, dt={dt}, nu_0={nu_0}, {N_STEPS} steps")
    print("="*70)

    topologies = [
        ("ring",         make_ring),
        ("trefoil",      make_trefoil),
        ("figure_eight", make_figure_eight),
        ("hopf_link",    make_hopf_link),
    ]

    solver = HelicitySolver()

    # ── PART 1: Measure helicity for all topologies ──
    print("\n--- PART 1: Helicity Measurement ---")
    center = [L/2, L/2, L/2]

    helicity_data = {}
    for topo_name, curve_func in topologies:
        ux_np, uy_np, uz_np = init_velocity(curve_func, center)
        ux_g = cp.asarray(ux_np); uy_g = cp.asarray(uy_np); uz_g = cp.asarray(uz_np)
        f = solver.compute_fields(ux_g, uy_g, uz_g)
        helicity_data[topo_name] = {
            'H_total': f['H_total'],
            'H_abs': f['H_abs'],
            'enstrophy': f['enstrophy'],
            'KE': f['KE'],
            'h_max': f['h_max'],
            'omega_max': f['omega_max'],
        }
        print(f"  {topo_name:16s}: H_total={f['H_total']:+10.4f}  "
              f"|H|_abs={f['H_abs']:8.4f}  enstrophy={f['enstrophy']:.3f}  "
              f"KE={f['KE']:.4f}")

    # ── PART 2: Helicity-based viscosity coupling ──
    print("\n--- PART 2: Helicity-Based Viscosity Coupling ---")
    betas = [0.0, 0.5, 0.9]
    all_results = {}

    for topo_name, curve_func in topologies:
        print(f"\n  [{topo_name}]")
        all_results[topo_name] = {}
        for beta in betas:
            label = f"beta_{beta:.1f}"
            meas = run_experiment(topo_name, curve_func, beta, label, solver)
            all_results[topo_name][label] = meas

    # ── Analysis ──
    print("\n" + "="*70)
    print("ANALYSIS")
    print("="*70)

    # Part 1 plot: helicity comparison
    fig1, axes1 = plt.subplots(1, 3, figsize=(18, 5))
    topo_names = [t[0] for t in topologies]
    H_totals = [helicity_data[t]['H_total'] for t in topo_names]
    H_abs_vals = [helicity_data[t]['H_abs'] for t in topo_names]
    enstrophies = [helicity_data[t]['enstrophy'] for t in topo_names]

    colors_topo = ['#ff6600', '#4444ff', '#cc2222', '#22aa22']

    ax = axes1[0]
    ax.bar(topo_names, H_totals, color=colors_topo, alpha=0.8)
    ax.set_ylabel('Total Helicity $H$', fontsize=12)
    ax.set_title('Total Helicity by Topology', fontsize=13, fontweight='bold')
    ax.axhline(0, color='black', lw=0.5)
    ax.grid(True, alpha=0.3, axis='y')

    ax = axes1[1]
    ax.bar(topo_names, H_abs_vals, color=colors_topo, alpha=0.8)
    ax.set_ylabel('$\\int |h| d^3x$', fontsize=12)
    ax.set_title('Absolute Helicity Density', fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')

    ax = axes1[2]
    # Helicity normalized by enstrophy (topology signature)
    H_norm = [abs(helicity_data[t]['H_total']) / max(helicity_data[t]['enstrophy'], 1e-10)
              for t in topo_names]
    ax.bar(topo_names, H_norm, color=colors_topo, alpha=0.8)
    ax.set_ylabel('$|H| / $ Enstrophy', fontsize=12)
    ax.set_title('Helicity per Unit Enstrophy\n(topology signature)', fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')

    fig1.suptitle('Helicity: The Topological Invariant That Distinguishes Knots',
                 fontsize=15, fontweight='bold', y=1.02)
    plt.tight_layout()
    fig1.savefig(RESULTS / "experiment_helicity_measurement.png", dpi=150, bbox_inches='tight')
    plt.close()

    # Part 2 plot: stability with helicity coupling
    colors_beta = {'beta_0.0':'#cc2222', 'beta_0.5':'#2222cc', 'beta_0.9':'#22aa22'}
    fig2, axes2 = plt.subplots(2, 4, figsize=(24, 10))

    for idx, (topo_name, _) in enumerate(topologies):
        results = all_results[topo_name]

        # Top: enstrophy
        ax = axes2[0][idx]
        for key in sorted(results.keys()):
            data = results[key]
            times = [d['time'] for d in data]
            ens = [d['enstrophy'] for d in data]
            beta_val = key.split('_')[1]
            ax.plot(times, ens, color=colors_beta[key], lw=2, label=f'$\\beta={beta_val}$')
        ax.set_xlabel('Time'); ax.set_ylabel('Enstrophy')
        ax.set_title(f'{topo_name}', fontsize=13, fontweight='bold')
        ax.legend(fontsize=9); ax.grid(True, alpha=0.3)

        # Bottom: helicity decay
        ax = axes2[1][idx]
        for key in sorted(results.keys()):
            data = results[key]
            times = [d['time'] for d in data]
            H = [abs(d['H_total']) for d in data]
            beta_val = key.split('_')[1]
            ax.plot(times, H, color=colors_beta[key], lw=2, label=f'$\\beta={beta_val}$')
        ax.set_xlabel('Time'); ax.set_ylabel('$|H|$')
        ax.set_title(f'{topo_name}: Helicity decay', fontsize=12)
        ax.legend(fontsize=9); ax.grid(True, alpha=0.3)

    fig2.suptitle('Helicity-Based Coupling: Enstrophy and Helicity Decay',
                 fontsize=15, fontweight='bold', y=1.01)
    plt.tight_layout()
    fig2.savefig(RESULTS / "experiment_helicity_coupling.png", dpi=150, bbox_inches='tight')
    plt.close()

    # ── Key comparison: stability ratios ──
    print("\nSTABILITY RATIO (coupled/control) at final step:")
    stability_data = {}
    for topo_name, _ in topologies:
        ctrl = all_results[topo_name]['beta_0.0']
        ctrl_final_ens = ctrl[-1]['enstrophy']
        stability_data[topo_name] = {}
        for beta_key in ['beta_0.5', 'beta_0.9']:
            data = all_results[topo_name][beta_key]
            test_final_ens = data[-1]['enstrophy']
            ratio = test_final_ens / ctrl_final_ens if ctrl_final_ens > 0 else 0
            stability_data[topo_name][beta_key] = ratio
            beta_val = beta_key.split('_')[1]
            H = helicity_data[topo_name]['H_total']
            print(f"  {topo_name:16s} beta={beta_val}: ratio={ratio:.6f}  (H={H:+.4f})")

    # The critical question: does helicity predict stabilization?
    print("\nCRITICAL TEST: Does higher helicity = more stabilization?")
    print("  (If yes, helicity-based coupling has the right topology dependence)")
    for beta_key in ['beta_0.5', 'beta_0.9']:
        beta_val = beta_key.split('_')[1]
        print(f"\n  beta={beta_val}:")
        pairs = [(topo_name, abs(helicity_data[topo_name]['H_total']),
                  stability_data[topo_name][beta_key])
                 for topo_name, _ in topologies]
        pairs.sort(key=lambda x: x[1])  # sort by |H|
        for name, H, ratio in pairs:
            print(f"    {name:16s}: |H|={H:.4f}  stability_ratio={ratio:.6f}")

        # Check correlation
        H_vals = [p[1] for p in pairs]
        R_vals = [p[2] for p in pairs]
        if len(H_vals) > 2:
            corr = np.corrcoef(H_vals, R_vals)[0, 1]
            print(f"    Correlation(|H|, stability): {corr:+.4f}")
            if corr > 0.5:
                print(f"    -> POSITIVE: Higher helicity = more stabilization!")
            elif corr < -0.5:
                print(f"    -> NEGATIVE: Higher helicity = LESS stabilization (wrong direction)")
            else:
                print(f"    -> WEAK: No clear relationship")

    # Save
    save = {
        'helicity_measurement': helicity_data,
        'stability': {t: {b: all_results[t][b] for b in all_results[t]}
                      for t, _ in topologies},
    }
    with open(RESULTS / "experiment_helicity_data.json", 'w') as f:
        json.dump(save, f, indent=2)

    print(f"\nSaved: experiment_helicity_measurement.png, experiment_helicity_coupling.png")
    print("="*70)


if __name__ == "__main__":
    main()
