"""
CRITICAL EXPERIMENT: Is Helicity-Inertia Genuinely Topological?
================================================================

The helicity-inertia result (ring < trefoil < hopf) goes in the right
direction. But is this because:

  (A) The TOPOLOGY (helicity) genuinely matters, or
  (B) It's just nonlinear viscosity reduction that happens to correlate
      with topology because of how helicity is distributed spatially?

TEST: Run THREE coupling mechanisms on the same topologies, calibrated
to produce the SAME average effective viscosity reduction:

  1. HELICITY-INERTIA: nu_eff = nu / (1 + alpha * |h|/h_ref)
     Reduces viscosity where velocity and vorticity are ALIGNED.

  2. OMEGA-INERTIA: nu_eff = nu / (1 + alpha * |omega|/omega_ref)
     Reduces viscosity where vorticity is HIGH (compact cores).

  3. RANDOM-INERTIA: nu_eff = nu / (1 + alpha * R(x))
     R(x) is a random field with the same power spectrum as |h|.
     Reduces viscosity in random locations. Control for spatial pattern.

If (A) is true: helicity-inertia gives trefoil > ring, while omega-
inertia gives ring > trefoil (as in previous experiment), and random
gives roughly equal. The spatial PATTERN of where viscosity is reduced
is what matters, and helicity puts it in the right places.

If (B) is true: all three give similar results because it's just the
total amount of viscosity reduction, not where it happens.

Also: add T(2,5) and T(2,7) torus knots for more data points.
6 topologies should give better correlation statistics.

CALIBRATION: For each mechanism, choose alpha so that the volume-
averaged effective viscosity is the same (~0.8 * nu_0).
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
nu = 0.01
N_STEPS = 3000
MEASURE_EVERY = 20

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

# ── Topologies ──
def make_ring(c):
    t = np.linspace(0, 2*np.pi, 200, endpoint=False)
    return c[0]+0.8*np.cos(t), c[1]+0.8*np.sin(t), np.full(200, c[2])

def make_trefoil(c):
    t = np.linspace(0, 2*np.pi, 300, endpoint=False); s = 1.0/3.0
    return (c[0]+s*(np.sin(t)+2*np.sin(2*t)), c[1]+s*(np.cos(t)-2*np.cos(2*t)), c[2]+s*(-np.sin(3*t)))

def make_figure_eight(c):
    t = np.linspace(0, 2*np.pi, 300, endpoint=False); s = 1.0/2.5
    return (c[0]+s*(2+np.cos(2*t))*np.cos(3*t), c[1]+s*(2+np.cos(2*t))*np.sin(3*t), c[2]+s*np.sin(4*t))

def make_hopf_link(c):
    t = np.linspace(0, 2*np.pi, 150, endpoint=False); R = 0.5
    x1=c[0]+R*np.cos(t); y1=c[1]+R*np.sin(t); z1=np.full(150, c[2])
    x2=c[0]+R/2+R*np.cos(t); y2=np.full(150, c[1]); z2=c[2]+R*np.sin(t)
    return np.concatenate([x1,x2]), np.concatenate([y1,y2]), np.concatenate([z1,z2])

def make_T25(c):
    t = np.linspace(0, 2*np.pi, 300, endpoint=False); rm=0.6; rn=0.3
    return (c[0]+(rm+rn*np.cos(5*t))*np.cos(2*t), c[1]+(rm+rn*np.cos(5*t))*np.sin(2*t), c[2]+rn*np.sin(5*t))

def make_T27(c):
    t = np.linspace(0, 2*np.pi, 300, endpoint=False); rm=0.6; rn=0.3
    return (c[0]+(rm+rn*np.cos(7*t))*np.cos(2*t), c[1]+(rm+rn*np.cos(7*t))*np.sin(2*t), c[2]+rn*np.sin(7*t))


def init_velocity(curve_func, center, Gamma=2.0, core_a=0.2):
    cx, cy, cz = curve_func(center); n = len(cx)
    dlx = np.roll(cx,-1)-cx; dly = np.roll(cy,-1)-cy; dlz = np.roll(cz,-1)-cz
    pad = lambda a: np.pad(a, (0, max_pts-n))
    fil_x.from_numpy(pad(cx)); fil_y.from_numpy(pad(cy)); fil_z.from_numpy(pad(cz))
    fil_dlx.from_numpy(pad(dlx)); fil_dly.from_numpy(pad(dly)); fil_dlz.from_numpy(pad(dlz))
    vel_x.fill(0); vel_y.fill(0); vel_z.fill(0)
    biot_savart_kernel(n, Gamma, core_a, L, N); ti.sync()
    return vel_x.to_numpy(), vel_y.to_numpy(), vel_z.to_numpy()


class Solver:
    def __init__(self):
        k = np.fft.fftfreq(N, d=L/(2*np.pi*N))
        KX, KY, KZ = np.meshgrid(k, k, k, indexing='ij')
        self.KX = cp.asarray(KX); self.KY = cp.asarray(KY); self.KZ = cp.asarray(KZ)
        self.K2 = self.KX**2 + self.KY**2 + self.KZ**2
        self.K2s = self.K2.copy(); self.K2s[0,0,0] = 1.0

    def compute_fields(self, ux, uy, uz):
        uxh = cp.fft.fftn(ux); uyh = cp.fft.fftn(uy); uzh = cp.fft.fftn(uz)
        wx = cp.real(cp.fft.ifftn(1j*self.KY*uzh - 1j*self.KZ*uyh))
        wy = cp.real(cp.fft.ifftn(1j*self.KZ*uxh - 1j*self.KX*uzh))
        wz = cp.real(cp.fft.ifftn(1j*self.KX*uyh - 1j*self.KY*uxh))
        omega = cp.sqrt(wx**2 + wy**2 + wz**2)
        h = ux*wx + uy*wy + uz*wz
        return uxh, uyh, uzh, wx, wy, wz, omega, h

    def step(self, ux, uy, uz, mode, alpha, ref_field):
        """Unified step. mode: 'control', 'helicity', 'omega', 'random'."""
        uxh, uyh, uzh, wx, wy, wz, omega, h = self.compute_fields(ux, uy, uz)

        # Compute effective density based on mode
        if mode == 'control':
            inv_rho = cp.ones((N,N,N), dtype=cp.float64)
        elif mode == 'helicity':
            field = cp.abs(h)
            f_norm = field / max(float(ref_field), 1e-10)
            f_norm = cp.minimum(f_norm, 3.0)
            inv_rho = 1.0 / (1.0 + alpha * f_norm)
        elif mode == 'omega':
            field = omega
            f_norm = field / max(float(ref_field), 1e-10)
            f_norm = cp.minimum(f_norm, 3.0)
            inv_rho = 1.0 / (1.0 + alpha * f_norm)
        elif mode == 'random':
            # ref_field is the random field itself (CuPy array)
            inv_rho = 1.0 / (1.0 + alpha * ref_field)
        else:
            inv_rho = cp.ones((N,N,N), dtype=cp.float64)

        # Advection
        gux_x = cp.real(cp.fft.ifftn(1j*self.KX*uxh))
        gux_y = cp.real(cp.fft.ifftn(1j*self.KY*uxh))
        gux_z = cp.real(cp.fft.ifftn(1j*self.KZ*uxh))
        guy_x = cp.real(cp.fft.ifftn(1j*self.KX*uyh))
        guy_y = cp.real(cp.fft.ifftn(1j*self.KY*uyh))
        guy_z = cp.real(cp.fft.ifftn(1j*self.KZ*uyh))
        guz_x = cp.real(cp.fft.ifftn(1j*self.KX*uzh))
        guz_y = cp.real(cp.fft.ifftn(1j*self.KY*uzh))
        guz_z = cp.real(cp.fft.ifftn(1j*self.KZ*uzh))
        adv_x = ux*gux_x + uy*gux_y + uz*gux_z
        adv_y = ux*guy_x + uy*guy_y + uz*guy_z
        adv_z = ux*guz_x + uy*guz_y + uz*guz_z

        # Viscous: (nu / rho_eff) * laplacian(u)
        lap_ux = cp.real(cp.fft.ifftn(-self.K2*uxh))
        lap_uy = cp.real(cp.fft.ifftn(-self.K2*uyh))
        lap_uz = cp.real(cp.fft.ifftn(-self.K2*uzh))

        rhs_x = -adv_x + inv_rho * nu * lap_ux
        rhs_y = -adv_y + inv_rho * nu * lap_uy
        rhs_z = -adv_z + inv_rho * nu * lap_uz

        uxh_n = uxh + dt*cp.fft.fftn(rhs_x)
        uyh_n = uyh + dt*cp.fft.fftn(rhs_y)
        uzh_n = uzh + dt*cp.fft.fftn(rhs_z)

        div = self.KX*uxh_n + self.KY*uyh_n + self.KZ*uzh_n
        uxh_n -= self.KX*div/self.K2s; uyh_n -= self.KY*div/self.K2s; uzh_n -= self.KZ*div/self.K2s
        uxh_n[0,0,0]=0; uyh_n[0,0,0]=0; uzh_n[0,0,0]=0

        ux = cp.clip(cp.real(cp.fft.ifftn(uxh_n)), -20, 20)
        uy = cp.clip(cp.real(cp.fft.ifftn(uyh_n)), -20, 20)
        uz = cp.clip(cp.real(cp.fft.ifftn(uzh_n)), -20, 20)

        # Average effective viscosity for calibration check
        nu_eff_mean = float(cp.mean(inv_rho).get()) * nu

        return ux, uy, uz, nu_eff_mean

    def measure(self, ux, uy, uz):
        _, _, _, wx, wy, wz, omega, h = self.compute_fields(ux, uy, uz)
        return {
            'KE': float(0.5*cp.sum(ux**2+uy**2+uz**2).get())*dx**3,
            'enstrophy': float(0.5*cp.sum(omega**2).get())*dx**3,
            'H_total': float(cp.sum(h).get())*dx**3,
            'H_abs': float(cp.sum(cp.abs(h)).get())*dx**3,
            'omega_max': float(cp.max(omega).get()),
        }


def run_experiment(topo_name, curve_func, mode, alpha, solver):
    center = [L/2, L/2, L/2]
    ux_np, uy_np, uz_np = init_velocity(curve_func, center)
    ux_g = cp.asarray(ux_np); uy_g = cp.asarray(uy_np); uz_g = cp.asarray(uz_np)

    # Compute reference values
    m0 = solver.measure(ux_g, uy_g, uz_g)
    _, _, _, _, _, _, omega0, h0 = solver.compute_fields(ux_g, uy_g, uz_g)

    if mode == 'helicity':
        ref = float(cp.mean(cp.abs(h0)).get())
    elif mode == 'omega':
        ref = float(cp.mean(omega0).get())
    elif mode == 'random':
        # Generate random field with same mean as |h|
        h_mean = float(cp.mean(cp.abs(h0)).get())
        ref = cp.abs(cp.random.normal(size=(N,N,N), dtype=cp.float64)) * h_mean / max(h_mean, 1e-10)
        ref = cp.minimum(ref, 3.0)
    else:
        ref = 1.0

    measurements = []
    nu_eff_samples = []
    t0 = time.time()
    blown = False

    for s in range(N_STEPS+1):
        if s % MEASURE_EVERY == 0:
            m = solver.measure(ux_g, uy_g, uz_g)
            m['step'] = s; m['time'] = s*dt
            measurements.append(m)
            if np.isnan(m['enstrophy']) or m['enstrophy'] > 1e8:
                blown = True; break
        if s < N_STEPS and not blown:
            ux_g, uy_g, uz_g, nu_eff = solver.step(ux_g, uy_g, uz_g, mode, alpha, ref)
            if s % 100 == 0: nu_eff_samples.append(nu_eff)

    elapsed = time.time() - t0
    e0 = measurements[0]['enstrophy']; ef = measurements[-1]['enstrophy']
    H0 = m0['H_total']; Ha = m0['H_abs']
    avg_nu = np.mean(nu_eff_samples) if nu_eff_samples else nu
    status = "OK" if not blown else "BLEW"
    print(f"    {mode:10s}: {elapsed:.0f}s ens {ef/e0:.4f} nu_avg={avg_nu:.5f} [{status}]")
    return measurements, blown, avg_nu


def main():
    print("="*70)
    print("CRITICAL: Is Helicity-Inertia Genuinely Topological?")
    print(f"Grid: {N}^3, dt={dt}, nu={nu}, {N_STEPS} steps")
    print(f"3 mechanisms: helicity, omega, random (+ control)")
    print(f"6 topologies: ring, trefoil, figure-eight, hopf, T(2,5), T(2,7)")
    print("="*70)

    topologies = [
        ("ring",         make_ring),
        ("trefoil",      make_trefoil),
        ("figure_eight", make_figure_eight),
        ("hopf_link",    make_hopf_link),
        ("T25",          make_T25),
        ("T27",          make_T27),
    ]

    modes = ['control', 'helicity', 'omega', 'random']
    alpha = 0.3  # moderate coupling

    solver = Solver()
    all_results = {}

    # First pass: measure initial helicity for all topologies
    print("\n  Initial helicity measurement:")
    center = [L/2, L/2, L/2]
    init_data = {}
    for topo_name, curve_func in topologies:
        ux_np, uy_np, uz_np = init_velocity(curve_func, center)
        ux_g = cp.asarray(ux_np); uy_g = cp.asarray(uy_np); uz_g = cp.asarray(uz_np)
        m = solver.measure(ux_g, uy_g, uz_g)
        init_data[topo_name] = m
        print(f"    {topo_name:16s}: H={m['H_total']:+8.3f}  |H|_abs={m['H_abs']:8.3f}  "
              f"ens={m['enstrophy']:.2f}  KE={m['KE']:.3f}")

    # Run all experiments
    for topo_name, curve_func in topologies:
        print(f"\n  [{topo_name}]")
        all_results[topo_name] = {}
        for mode in modes:
            meas, blown, avg_nu = run_experiment(topo_name, curve_func, mode, alpha, solver)
            all_results[topo_name][mode] = {
                'data': meas, 'blown': blown, 'avg_nu': avg_nu}

    # ── Analysis ──
    print("\n" + "="*70)
    print("RESULTS: STABILITY RATIO (mode / control) at alpha=0.3")
    print("="*70)

    stability = {}
    for topo_name, _ in topologies:
        ctrl_f = all_results[topo_name]['control']['data'][-1]['enstrophy']
        stability[topo_name] = {}
        for mode in ['helicity', 'omega', 'random']:
            res = all_results[topo_name][mode]
            if res['blown']:
                stability[topo_name][mode] = float('nan')
                continue
            test_f = res['data'][-1]['enstrophy']
            ratio = test_f / ctrl_f if ctrl_f > 0 else 0
            stability[topo_name][mode] = ratio

    # Print table
    print(f"\n  {'Topology':16s} {'|H|_total':>10s} {'|H|_abs':>10s} "
          f"{'Helicity':>10s} {'Omega':>10s} {'Random':>10s}")
    print("  " + "-"*70)
    for topo_name, _ in topologies:
        H = init_data[topo_name]['H_total']
        Ha = init_data[topo_name]['H_abs']
        h_r = stability[topo_name].get('helicity', 0)
        o_r = stability[topo_name].get('omega', 0)
        r_r = stability[topo_name].get('random', 0)
        print(f"  {topo_name:16s} {abs(H):10.3f} {Ha:10.3f} "
              f"{h_r:10.4f} {o_r:10.4f} {r_r:10.4f}")

    # Correlations
    print("\nCORRELATIONS with |H|_total:")
    for mode in ['helicity', 'omega', 'random']:
        pairs = [(abs(init_data[t]['H_total']), stability[t][mode])
                 for t, _ in topologies
                 if not np.isnan(stability[t].get(mode, float('nan')))]
        if len(pairs) >= 3:
            H_list = [p[0] for p in pairs]
            R_list = [p[1] for p in pairs]
            corr = np.corrcoef(H_list, R_list)[0,1]
            print(f"  {mode:10s}: corr = {corr:+.4f}")

    print("\nCORRELATIONS with |H|_abs:")
    for mode in ['helicity', 'omega', 'random']:
        pairs = [(init_data[t]['H_abs'], stability[t][mode])
                 for t, _ in topologies
                 if not np.isnan(stability[t].get(mode, float('nan')))]
        if len(pairs) >= 3:
            H_list = [p[0] for p in pairs]
            R_list = [p[1] for p in pairs]
            corr = np.corrcoef(H_list, R_list)[0,1]
            print(f"  {mode:10s}: corr = {corr:+.4f}")

    # Average effective viscosity (calibration check)
    print("\nAVERAGE EFFECTIVE VISCOSITY (should be similar across modes):")
    for mode in modes:
        nu_vals = [all_results[t][mode]['avg_nu'] for t, _ in topologies
                   if not all_results[t][mode]['blown']]
        if nu_vals:
            print(f"  {mode:10s}: mean nu_eff = {np.mean(nu_vals):.6f}")

    # ── KEY VERDICT ──
    print("\n" + "="*70)
    print("VERDICT: Is helicity-inertia genuinely topological?")
    print("="*70)

    # Compare ranking: does helicity-inertia rank differently from omega-inertia?
    h_ranks = sorted([(stability[t]['helicity'], t) for t, _ in topologies
                       if not np.isnan(stability[t].get('helicity', float('nan')))],
                      reverse=True)
    o_ranks = sorted([(stability[t]['omega'], t) for t, _ in topologies
                       if not np.isnan(stability[t].get('omega', float('nan')))],
                      reverse=True)

    print(f"\n  Helicity-inertia ranking (most -> least stabilized):")
    for i, (r, t) in enumerate(h_ranks):
        print(f"    {i+1}. {t:16s} ratio={r:.4f}")

    print(f"\n  Omega-inertia ranking (most -> least stabilized):")
    for i, (r, t) in enumerate(o_ranks):
        print(f"    {i+1}. {t:16s} ratio={r:.4f}")

    # Check if ring is last in helicity but first in omega
    h_names = [t for _, t in h_ranks]
    o_names = [t for _, t in o_ranks]
    ring_h_pos = h_names.index('ring') + 1 if 'ring' in h_names else -1
    ring_o_pos = o_names.index('ring') + 1 if 'ring' in o_names else -1

    print(f"\n  Ring position: helicity #{ring_h_pos}/{len(h_names)}, "
          f"omega #{ring_o_pos}/{len(o_names)}")

    if ring_h_pos > len(h_names)//2 and ring_o_pos <= len(o_names)//2:
        print("  -> Ring is LESS stabilized by helicity, MORE by omega.")
        print("  -> The coupling mechanism DOES distinguish topology from geometry.")
        print("  -> This is evidence for helicity-based coupling being topological.")
    elif ring_h_pos == ring_o_pos:
        print("  -> Ring has same relative position in both rankings.")
        print("  -> No clear topological distinction between mechanisms.")
    else:
        print(f"  -> Mixed result. Need more analysis.")

    # Plots
    fig, axes = plt.subplots(1, 3, figsize=(21, 6))
    mode_colors = {'helicity': '#2222cc', 'omega': '#cc2222', 'random': '#888888'}

    for mi, mode in enumerate(['helicity', 'omega', 'random']):
        ax = axes[mi]
        topo_names = [t for t, _ in topologies]
        ratios = [stability[t].get(mode, 0) for t in topo_names]
        H_abs_vals = [init_data[t]['H_abs'] for t in topo_names]

        # Color by helicity
        colors = ['#22aa22' if H > 1 else '#cc8800' if H > 0.15 else '#cc2222'
                  for H in H_abs_vals]

        valid = [(t, r) for t, r in zip(topo_names, ratios)
                 if not np.isnan(r) and r < 100]
        if valid:
            names_v, ratios_v = zip(*valid)
            ax.barh(range(len(names_v)), ratios_v,
                   color=[colors[topo_names.index(n)] for n in names_v], alpha=0.8)
            ax.set_yticks(range(len(names_v)))
            ax.set_yticklabels(names_v, fontsize=10)
            ax.axvline(1.0, color='black', ls='--', lw=1)
        ax.set_xlabel('Stability ratio', fontsize=11)
        ax.set_title(f'{mode.upper()}-inertia', fontsize=14, fontweight='bold',
                    color=mode_colors[mode])
        ax.grid(True, alpha=0.3, axis='x')

    fig.suptitle('Critical Test: 3 Mechanisms x 6 Topologies\n'
                 'Green=high helicity, Orange=some, Red=low/zero',
                fontsize=14, fontweight='bold', y=1.03)
    plt.tight_layout()
    fig.savefig(RESULTS / "experiment_critical_comparison.png", dpi=150, bbox_inches='tight')
    plt.close()

    # Save
    save = {
        'init_data': {t: init_data[t] for t in init_data},
        'stability': stability,
        'params': {'alpha': alpha, 'nu': nu, 'N': N, 'N_STEPS': N_STEPS},
    }
    with open(RESULTS / "experiment_critical_comparison_data.json", 'w') as f:
        json.dump(save, f, indent=2)

    print("="*70)


if __name__ == "__main__":
    main()
