"""
EXPERIMENT v2: Helicity-Inertia (FIXED CONTROLS)
==================================================

v1 BUG: Control used exponential viscosity integrator, test cases used
explicit viscosity. Different numerical dissipation rates produced
apparent "stabilization" that was purely numerical artifact.

FIX: ALL runs (control and test) use the SAME step function.
alpha=0 gives rho_eff=1 everywhere, so the step is numerically
identical to standard NS with explicit viscosity. Apples to apples.

Also: sweep alpha more finely (0.1, 0.2, 0.3, 0.5) to find the
regime where the coupling matters without blowing up.
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

def make_ring(c, R=0.8, n=200):
    t = np.linspace(0, 2*np.pi, n, endpoint=False)
    return c[0]+R*np.cos(t), c[1]+R*np.sin(t), np.full(n, c[2])

def make_trefoil(c, scale=1.0, n=300):
    t = np.linspace(0, 2*np.pi, n, endpoint=False); s = scale/3.0
    return (c[0]+s*(np.sin(t)+2*np.sin(2*t)), c[1]+s*(np.cos(t)-2*np.cos(2*t)), c[2]+s*(-np.sin(3*t)))

def make_figure_eight(c, scale=1.0, n=300):
    t = np.linspace(0, 2*np.pi, n, endpoint=False); s = scale/2.5
    return (c[0]+s*(2+np.cos(2*t))*np.cos(3*t), c[1]+s*(2+np.cos(2*t))*np.sin(3*t), c[2]+s*np.sin(4*t))

def make_hopf_link(c, scale=1.0, n=150):
    t = np.linspace(0, 2*np.pi, n, endpoint=False); R = scale*0.5
    x1=c[0]+R*np.cos(t); y1=c[1]+R*np.sin(t); z1=np.full(n, c[2])
    x2=c[0]+R/2+R*np.cos(t); y2=np.full(n, c[1]); z2=c[2]+R*np.sin(t)
    return np.concatenate([x1,x2]), np.concatenate([y1,y2]), np.concatenate([z1,z2])

def init_velocity(curve_func, center, Gamma=2.0, core_a=0.2):
    cx, cy, cz = curve_func(center); n = len(cx)
    dlx = np.roll(cx,-1)-cx; dly = np.roll(cy,-1)-cy; dlz = np.roll(cz,-1)-cz
    pad = lambda a: np.pad(a, (0, max_pts-n))
    fil_x.from_numpy(pad(cx)); fil_y.from_numpy(pad(cy)); fil_z.from_numpy(pad(cz))
    fil_dlx.from_numpy(pad(dlx)); fil_dly.from_numpy(pad(dly)); fil_dlz.from_numpy(pad(dlz))
    vel_x.fill(0); vel_y.fill(0); vel_z.fill(0)
    biot_savart_kernel(n, Gamma, core_a, L, N); ti.sync()
    return vel_x.to_numpy(), vel_y.to_numpy(), vel_z.to_numpy()


class UnifiedSolver:
    """Single step function for ALL runs. alpha=0 is the control."""
    def __init__(self):
        k = np.fft.fftfreq(N, d=L/(2*np.pi*N))
        KX, KY, KZ = np.meshgrid(k, k, k, indexing='ij')
        self.KX = cp.asarray(KX); self.KY = cp.asarray(KY); self.KZ = cp.asarray(KZ)
        self.K2 = self.KX**2 + self.KY**2 + self.KZ**2
        self.K2s = self.K2.copy(); self.K2s[0,0,0] = 1.0

    def step(self, ux, uy, uz, alpha, h_ref):
        """UNIFIED step: same code path for control and test.
        alpha=0 -> rho_eff=1 -> standard NS with explicit viscosity.
        alpha>0 -> rho_eff>1 in helical regions -> modified dynamics.
        """
        uxh = cp.fft.fftn(ux); uyh = cp.fft.fftn(uy); uzh = cp.fft.fftn(uz)

        # Vorticity
        wx = cp.real(cp.fft.ifftn(1j*self.KY*uzh - 1j*self.KZ*uyh))
        wy = cp.real(cp.fft.ifftn(1j*self.KZ*uxh - 1j*self.KX*uzh))
        wz = cp.real(cp.fft.ifftn(1j*self.KX*uyh - 1j*self.KY*uxh))

        # Helicity density and effective density
        h = ux*wx + uy*wy + uz*wz
        h_norm = cp.abs(h) / max(float(h_ref), 1e-10)
        h_norm = cp.minimum(h_norm, 3.0)
        rho_eff = 1.0 + alpha * h_norm
        inv_rho = 1.0 / rho_eff

        # Advection: (u.grad)u
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

        # Viscous term: (nu/rho_eff) * laplacian(u)
        lap_ux = cp.real(cp.fft.ifftn(-self.K2*uxh))
        lap_uy = cp.real(cp.fft.ifftn(-self.K2*uyh))
        lap_uz = cp.real(cp.fft.ifftn(-self.K2*uzh))
        visc_x = inv_rho * nu * lap_ux
        visc_y = inv_rho * nu * lap_uy
        visc_z = inv_rho * nu * lap_uz

        # Time step
        rhs_x = -adv_x + visc_x
        rhs_y = -adv_y + visc_y
        rhs_z = -adv_z + visc_z
        uxh_new = uxh + dt * cp.fft.fftn(rhs_x)
        uyh_new = uyh + dt * cp.fft.fftn(rhs_y)
        uzh_new = uzh + dt * cp.fft.fftn(rhs_z)

        # Projection
        div = self.KX*uxh_new + self.KY*uyh_new + self.KZ*uzh_new
        uxh_new -= self.KX*div/self.K2s
        uyh_new -= self.KY*div/self.K2s
        uzh_new -= self.KZ*div/self.K2s
        uxh_new[0,0,0]=0; uyh_new[0,0,0]=0; uzh_new[0,0,0]=0

        ux = cp.clip(cp.real(cp.fft.ifftn(uxh_new)), -20, 20)
        uy = cp.clip(cp.real(cp.fft.ifftn(uyh_new)), -20, 20)
        uz = cp.clip(cp.real(cp.fft.ifftn(uzh_new)), -20, 20)
        return ux, uy, uz

    def measure(self, ux, uy, uz):
        uxh = cp.fft.fftn(ux); uyh = cp.fft.fftn(uy); uzh = cp.fft.fftn(uz)
        wx = cp.real(cp.fft.ifftn(1j*self.KY*uzh-1j*self.KZ*uyh))
        wy = cp.real(cp.fft.ifftn(1j*self.KZ*uxh-1j*self.KX*uzh))
        wz = cp.real(cp.fft.ifftn(1j*self.KX*uyh-1j*self.KY*uxh))
        omega = cp.sqrt(wx**2+wy**2+wz**2)
        h = ux*wx+uy*wy+uz*wz
        return {
            'KE': float(0.5*cp.sum(ux**2+uy**2+uz**2).get())*dx**3,
            'enstrophy': float(0.5*cp.sum(omega**2).get())*dx**3,
            'H_total': float(cp.sum(h).get())*dx**3,
            'H_abs': float(cp.sum(cp.abs(h)).get())*dx**3,
            'omega_max': float(cp.max(omega).get()),
        }


def run_exp(topo_name, curve_func, alpha_val, solver):
    center = [L/2, L/2, L/2]
    ux_np, uy_np, uz_np = init_velocity(curve_func, center)
    ux_g = cp.asarray(ux_np); uy_g = cp.asarray(uy_np); uz_g = cp.asarray(uz_np)

    m0 = solver.measure(ux_g, uy_g, uz_g)
    h_ref = max(m0['H_abs'] / (N**3 * dx**3), 1e-6)

    measurements = []
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
            ux_g, uy_g, uz_g = solver.step(ux_g, uy_g, uz_g, alpha_val, h_ref)

    elapsed = time.time() - t0
    e0 = measurements[0]['enstrophy']; ef = measurements[-1]['enstrophy']
    H0 = measurements[0]['H_total']
    status = "STABLE" if not blown else "BLOWUP"
    print(f"    alpha={alpha_val:.2f}: {elapsed:.0f}s ens {e0:.2f}->{ef:.2f} "
          f"({ef/e0:.4f}) H0={H0:+.3f} [{status}]")
    return measurements, blown


def main():
    print("="*70)
    print("EXPERIMENT v2: Helicity-Inertia (FIXED CONTROLS)")
    print(f"Grid: {N}^3, dt={dt}, nu={nu}, {N_STEPS} steps")
    print(f"UNIFIED step function: alpha=0 IS the control")
    print("="*70)

    topologies = [
        ("ring",         make_ring),
        ("trefoil",      make_trefoil),
        ("figure_eight", make_figure_eight),
        ("hopf_link",    make_hopf_link),
    ]
    alphas = [0.0, 0.1, 0.2, 0.3, 0.5]

    solver = UnifiedSolver()
    all_results = {}

    for topo_name, curve_func in topologies:
        print(f"\n  [{topo_name}]")
        all_results[topo_name] = {}
        for a in alphas:
            meas, blown = run_exp(topo_name, curve_func, a, solver)
            all_results[topo_name][f"a{a:.1f}"] = {'data': meas, 'blown': blown}

    # ── Analysis ──
    print("\n" + "="*70)
    print("STABILITY RATIOS (coupled / control)")
    print("="*70)

    # Known helicities (from Part 1 measurement)
    known_H = {'ring': 0.0, 'trefoil': 9.08, 'figure_eight': 0.20, 'hopf_link': 3.66}

    for a in alphas[1:]:
        a_key = f"a{a:.1f}"
        print(f"\n  alpha = {a}:")
        pairs = []
        for topo_name, _ in topologies:
            ctrl = all_results[topo_name]['a0.0']
            test = all_results[topo_name][a_key]
            if ctrl['blown'] or test['blown']:
                print(f"    {topo_name:16s}: BLOWUP")
                continue
            ctrl_f = ctrl['data'][-1]['enstrophy']
            test_f = test['data'][-1]['enstrophy']
            ratio = test_f / ctrl_f if ctrl_f > 0 else 0
            H = known_H.get(topo_name, 0)
            pairs.append((topo_name, H, ratio))
            print(f"    {topo_name:16s}: |H|={H:.2f}  ratio={ratio:.6f}")

        if len(pairs) >= 3:
            H_list = [p[1] for p in pairs]
            R_list = [p[2] for p in pairs]
            corr = np.corrcoef(H_list, R_list)[0,1]
            print(f"    Correlation(|H|, stability): {corr:+.4f}")
            if corr > 0.5:
                print(f"    >>> POSITIVE: Higher helicity = more stabilization")
            elif corr < -0.5:
                print(f"    NEGATIVE: Wrong direction")
            else:
                print(f"    WEAK/NONE: No clear relationship")

    # ── Plots ──
    colors_a = {'a0.0':'#cc2222', 'a0.1':'#cc8800', 'a0.2':'#888800',
                'a0.3':'#2222cc', 'a0.5':'#22aa22'}

    fig, axes = plt.subplots(2, 4, figsize=(24, 10))
    for idx, (topo_name, _) in enumerate(topologies):
        for a_key in sorted(all_results[topo_name].keys()):
            res = all_results[topo_name][a_key]
            if res['blown'] and len(res['data']) < 5: continue
            data = res['data']
            times = [d['time'] for d in data]
            ens = [d['enstrophy'] for d in data]
            Habs = [abs(d['H_total']) for d in data]
            a_val = a_key[1:]
            c = colors_a.get(a_key, '#888888')
            axes[0][idx].plot(times, ens, color=c, lw=2, label=f'$\\alpha={a_val}$')
            axes[1][idx].plot(times, Habs, color=c, lw=2, label=f'$\\alpha={a_val}$')

        H = known_H.get(topo_name, 0)
        axes[0][idx].set_title(f'{topo_name} (|H|={H:.1f})', fontsize=13, fontweight='bold')
        axes[0][idx].set_xlabel('Time'); axes[0][idx].set_ylabel('Enstrophy')
        axes[0][idx].legend(fontsize=8); axes[0][idx].grid(True, alpha=0.3)
        axes[1][idx].set_xlabel('Time'); axes[1][idx].set_ylabel('$|H_{total}|$')
        axes[1][idx].legend(fontsize=8); axes[1][idx].grid(True, alpha=0.3)

    fig.suptitle('Helicity-Inertia v2 (FIXED: unified step function, apples-to-apples)',
                fontsize=14, fontweight='bold', y=1.01)
    plt.tight_layout()
    fig.savefig(RESULTS / "experiment_helicity_inertia_v2.png", dpi=150, bbox_inches='tight')
    plt.close()

    # Stability ratio bar chart
    fig2, axes2 = plt.subplots(1, len(alphas)-1, figsize=(5*(len(alphas)-1), 5))
    if len(alphas)-1 == 1: axes2 = [axes2]
    for ai, a in enumerate(alphas[1:]):
        a_key = f"a{a:.1f}"
        ax = axes2[ai]
        names = []; ratios = []; colors = []
        for topo_name, _ in topologies:
            ctrl = all_results[topo_name]['a0.0']
            test = all_results[topo_name][a_key]
            if ctrl['blown'] or test['blown']: continue
            ctrl_f = ctrl['data'][-1]['enstrophy']
            test_f = test['data'][-1]['enstrophy']
            ratio = test_f / ctrl_f if ctrl_f > 0 else 0
            names.append(topo_name)
            ratios.append(ratio)
            H = known_H.get(topo_name, 0)
            colors.append('#22aa22' if H > 1 else '#cc2222')
        ax.barh(range(len(names)), ratios, color=colors, alpha=0.8)
        ax.set_yticks(range(len(names))); ax.set_yticklabels(names)
        ax.axvline(1.0, color='black', ls='--', lw=1)
        ax.set_xlabel('Stability ratio (>1 = stabilized)')
        ax.set_title(f'$\\alpha={a}$', fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='x')

    fig2.suptitle('Green = has helicity (knotted), Red = no helicity (unknotted)',
                 fontsize=12)
    plt.tight_layout()
    fig2.savefig(RESULTS / "experiment_helicity_inertia_v2_bars.png", dpi=150, bbox_inches='tight')
    plt.close()

    # Save
    save = {}
    for t, _ in topologies:
        save[t] = {}
        for a_key in all_results[t]:
            save[t][a_key] = {'data': all_results[t][a_key]['data'],
                              'blown': all_results[t][a_key]['blown']}
    with open(RESULTS / "experiment_helicity_inertia_v2_data.json", 'w') as f:
        json.dump(save, f, indent=2)

    print("="*70)


if __name__ == "__main__":
    main()
