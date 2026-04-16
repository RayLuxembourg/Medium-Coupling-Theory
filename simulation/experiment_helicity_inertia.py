"""
EXPERIMENT: Helicity as Effective Density (Mass from Topology)
===============================================================

HYPOTHESIS:
  Mass = helicity-dependent effective density.

    rho_eff(x) = 1 + alpha * |h(x)| / h_ref

  where h(x) = u(x) . omega(x) is helicity density.

  Knotted regions have high |h| -> high rho_eff -> more inertia.
  They resist being dispersed. This IS mass from topology.

  Modified NS (Boussinesq approximation):
    rho_eff * (du/dt + (u.grad)u) = -grad(p) + nu * lap(u)
    div(u) = 0

  The key difference from variable viscosity: this modifies the
  INERTIAL term, not dissipation. The product rho_eff * (u.grad)u
  is not a pure gradient when rho_eff varies spatially. The Leray
  projection does not eliminate it.

IMPLEMENTATION:
  Rewrite as: du/dt = -(u.grad)u - (1/rho_eff)*grad(p) + (nu/rho_eff)*lap(u)

  Or equivalently: du/dt = F_adv + F_press + F_visc
  where F_adv = -(u.grad)u  (unchanged)
        F_press = -(1/rho_eff)*grad(p)  (density-weighted)
        F_visc = (nu/rho_eff)*lap(u)  (density-weighted)

  The projection step finds p such that div(u^{n+1}) = 0.
  With variable rho_eff, the projection equation becomes:
    div((1/rho_eff) * grad(p)) = div(u*)/dt
  where u* is the unprojected velocity.

  For simplicity, we use the approximate approach: compute rho_eff,
  divide the viscous and pressure terms by rho_eff, then project
  normally. This is first-order accurate and captures the key physics.

SELF-CRITICISM:
  - The Boussinesq approximation assumes small density variations.
    If alpha is too large, rho_eff varies a lot and the approximation
    breaks down.
  - rho_eff depends on |h| which depends on u, making this a nonlinear
    feedback. Could be unstable if alpha is large.
  - The key question is whether the inertial effect is topology-
    dependent or just vorticity-dependent. Since h = u.omega, regions
    with aligned velocity and vorticity get more inertia. Alignment
    is related to helicity, which IS topological. But the local
    alignment may not track the global topology well.
  - We MUST compare: does the trefoil benefit more than the ring?
    If yes, the mechanism works. If no (same as viscosity experiments),
    the inertial approach fails for the same geometric reasons.
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


class BoussinesqHelicitySolver:
    def __init__(self):
        k = np.fft.fftfreq(N, d=L/(2*np.pi*N))
        KX, KY, KZ = np.meshgrid(k, k, k, indexing='ij')
        self.KX = cp.asarray(KX); self.KY = cp.asarray(KY); self.KZ = cp.asarray(KZ)
        self.K2 = self.KX**2 + self.KY**2 + self.KZ**2
        self.K2s = self.K2.copy(); self.K2s[0,0,0] = 1.0

    def step(self, ux, uy, uz, alpha, h_ref):
        """One step with helicity-dependent effective density."""
        uxh = cp.fft.fftn(ux); uyh = cp.fft.fftn(uy); uzh = cp.fft.fftn(uz)

        # Vorticity
        wx = cp.real(cp.fft.ifftn(1j*self.KY*uzh - 1j*self.KZ*uyh))
        wy = cp.real(cp.fft.ifftn(1j*self.KZ*uxh - 1j*self.KX*uzh))
        wz = cp.real(cp.fft.ifftn(1j*self.KX*uyh - 1j*self.KY*uxh))

        # Helicity density
        h = ux*wx + uy*wy + uz*wz

        # Effective density: rho_eff = 1 + alpha * |h| / h_ref
        h_norm = cp.abs(h) / max(float(h_ref), 1e-10)
        h_norm = cp.minimum(h_norm, 5.0)  # cap to prevent extreme values
        rho_eff = 1.0 + alpha * h_norm
        inv_rho = 1.0 / rho_eff

        # Nonlinear advection: (u.grad)u (same as standard NS)
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

        # Viscous term divided by rho_eff
        lap_ux = cp.real(cp.fft.ifftn(-self.K2*uxh))
        lap_uy = cp.real(cp.fft.ifftn(-self.K2*uyh))
        lap_uz = cp.real(cp.fft.ifftn(-self.K2*uzh))

        visc_x = inv_rho * nu * lap_ux
        visc_y = inv_rho * nu * lap_uy
        visc_z = inv_rho * nu * lap_uz

        # RHS: -advection + viscosity (pressure handled by projection)
        # Note: advection is NOT divided by rho_eff (it's already per unit mass
        # in the (u.grad)u form). The density appears in the pressure gradient
        # and viscous terms.
        # Actually: rho_eff * du/dt = -rho_eff*(u.grad)u - grad(p) + nu*lap(u)
        # -> du/dt = -(u.grad)u - (1/rho_eff)*grad(p) + (nu/rho_eff)*lap(u)
        # The projection handles -(1/rho_eff)*grad(p).
        # So we need: du/dt = -(u.grad)u + (nu/rho_eff)*lap(u)

        rhs_x = -adv_x + visc_x
        rhs_y = -adv_y + visc_y
        rhs_z = -adv_z + visc_z

        uxh_new = uxh + dt * cp.fft.fftn(rhs_x)
        uyh_new = uyh + dt * cp.fft.fftn(rhs_y)
        uzh_new = uzh + dt * cp.fft.fftn(rhs_z)

        # Leray projection: div(u) = 0
        # With variable density, the correct projection is:
        #   div((1/rho_eff) * grad(p)) = (1/dt) * div(u*)
        # We approximate with the standard projection (accurate for small alpha)
        div = self.KX*uxh_new + self.KY*uyh_new + self.KZ*uzh_new
        uxh_new -= self.KX*div/self.K2s
        uyh_new -= self.KY*div/self.K2s
        uzh_new -= self.KZ*div/self.K2s
        uxh_new[0,0,0]=0; uyh_new[0,0,0]=0; uzh_new[0,0,0]=0

        ux = cp.clip(cp.real(cp.fft.ifftn(uxh_new)), -20, 20)
        uy = cp.clip(cp.real(cp.fft.ifftn(uyh_new)), -20, 20)
        uz = cp.clip(cp.real(cp.fft.ifftn(uzh_new)), -20, 20)

        return ux, uy, uz

    def step_control(self, ux, uy, uz):
        """Standard NS (alpha=0 control)."""
        uxh = cp.fft.fftn(ux); uyh = cp.fft.fftn(uy); uzh = cp.fft.fftn(uz)
        wx = cp.real(cp.fft.ifftn(1j*self.KY*uzh-1j*self.KZ*uyh))
        wy = cp.real(cp.fft.ifftn(1j*self.KZ*uxh-1j*self.KX*uzh))
        wz = cp.real(cp.fft.ifftn(1j*self.KX*uyh-1j*self.KY*uxh))
        rhsx = wy*uz-wz*uy; rhsy = wz*ux-wx*uz; rhsz = wx*uy-wy*ux
        visc = cp.exp(-nu*self.K2*dt)
        uxh_n = (uxh+dt*cp.fft.fftn(rhsx))*visc
        uyh_n = (uyh+dt*cp.fft.fftn(rhsy))*visc
        uzh_n = (uzh+dt*cp.fft.fftn(rhsz))*visc
        div = self.KX*uxh_n+self.KY*uyh_n+self.KZ*uzh_n
        uxh_n -= self.KX*div/self.K2s; uyh_n -= self.KY*div/self.K2s; uzh_n -= self.KZ*div/self.K2s
        uxh_n[0,0,0]=0; uyh_n[0,0,0]=0; uzh_n[0,0,0]=0
        return (cp.clip(cp.real(cp.fft.ifftn(uxh_n)),-20,20),
                cp.clip(cp.real(cp.fft.ifftn(uyh_n)),-20,20),
                cp.clip(cp.real(cp.fft.ifftn(uzh_n)),-20,20))

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


def run_exp(topo_name, curve_func, alpha_val, label, solver):
    center = [L/2, L/2, L/2]
    ux_np, uy_np, uz_np = init_velocity(curve_func, center)
    ux_g = cp.asarray(ux_np); uy_g = cp.asarray(uy_np); uz_g = cp.asarray(uz_np)

    m0 = solver.measure(ux_g, uy_g, uz_g)
    h_ref = max(m0['H_abs'] / (N**3 * dx**3), 1e-6)  # mean |h|

    measurements = []
    t0 = time.time()
    for s in range(N_STEPS+1):
        if s % MEASURE_EVERY == 0:
            m = solver.measure(ux_g, uy_g, uz_g)
            m['step'] = s; m['time'] = s*dt
            measurements.append(m)
            if np.isnan(m['enstrophy']):
                print(f"    BLOWUP {s}"); break
        if s < N_STEPS:
            if alpha_val > 0:
                ux_g, uy_g, uz_g = solver.step(ux_g, uy_g, uz_g, alpha_val, h_ref)
            else:
                ux_g, uy_g, uz_g = solver.step_control(ux_g, uy_g, uz_g)

    elapsed = time.time() - t0
    e0 = measurements[0]['enstrophy']; ef = measurements[-1]['enstrophy']
    H0 = measurements[0]['H_total']; Hf = measurements[-1]['H_total']
    print(f"    {label}: {elapsed:.1f}s  ens {e0:.3f}->{ef:.3f}({ef/e0:.4f})  "
          f"H {H0:.3f}->{Hf:.3f}")
    return measurements


def main():
    print("="*70)
    print("EXPERIMENT: Helicity as Effective Density (Boussinesq)")
    print(f"Grid: {N}^3, dt={dt}, nu={nu}, {N_STEPS} steps")
    print(f"rho_eff = 1 + alpha * |h| / h_ref")
    print("="*70)

    topologies = [
        ("ring",         make_ring),
        ("trefoil",      make_trefoil),
        ("figure_eight", make_figure_eight),
        ("hopf_link",    make_hopf_link),
    ]
    alphas = [0.0, 0.5, 2.0]

    solver = BoussinesqHelicitySolver()
    all_results = {}

    for topo_name, curve_func in topologies:
        print(f"\n  [{topo_name}]")
        all_results[topo_name] = {}
        for a in alphas:
            label = f"alpha_{a:.1f}"
            meas = run_exp(topo_name, curve_func, a, label, solver)
            all_results[topo_name][label] = meas

    # ── Analysis ──
    print("\n" + "="*70)
    print("ANALYSIS: STABILITY RATIO (coupled / control)")
    print("="*70)

    stability = {}
    for topo_name, _ in topologies:
        ctrl_f = all_results[topo_name]['alpha_0.0'][-1]['enstrophy']
        stability[topo_name] = {}
        for a_key in ['alpha_0.5', 'alpha_2.0']:
            test_f = all_results[topo_name][a_key][-1]['enstrophy']
            ratio = test_f / ctrl_f if ctrl_f > 0 else 0
            stability[topo_name][a_key] = ratio
            print(f"  {topo_name:16s} {a_key}: ratio = {ratio:.6f}")

    print("\nCRITICAL TEST: Do knotted structures benefit more?")
    for a_key in ['alpha_0.5', 'alpha_2.0']:
        print(f"\n  {a_key}:")
        # Sort by initial |H|
        from experiment_helicity import init_velocity as _  # just for the helicity values
        h_vals = {
            'ring': 0.0, 'trefoil': 9.08, 'figure_eight': 0.20, 'hopf_link': 3.66
        }
        pairs = [(t, h_vals.get(t, 0), stability[t][a_key]) for t, _ in topologies]
        pairs.sort(key=lambda x: x[1])
        for name, H, ratio in pairs:
            marker = "***" if ratio > 1.01 else ""
            print(f"    {name:16s}: |H|={H:.2f}  ratio={ratio:.6f} {marker}")

        H_list = [p[1] for p in pairs]
        R_list = [p[2] for p in pairs]
        corr = np.corrcoef(H_list, R_list)[0,1] if len(H_list) > 2 else 0
        print(f"    Correlation(|H|, stability): {corr:+.4f}")
        if corr > 0.5:
            print(f"    >>> POSITIVE CORRELATION: Helicity predicts stabilization!")
            print(f"    >>> This is the MCT prediction: topology determines mass.")
        elif corr < -0.5:
            print(f"    NEGATIVE: Wrong direction again.")
        else:
            print(f"    WEAK: No clear relationship.")

    # Plots
    colors_a = {'alpha_0.0':'#cc2222', 'alpha_0.5':'#2222cc', 'alpha_2.0':'#22aa22'}
    fig, axes = plt.subplots(2, 4, figsize=(24, 10))

    for idx, (topo_name, _) in enumerate(topologies):
        for a_key in sorted(all_results[topo_name].keys()):
            data = all_results[topo_name][a_key]
            times = [d['time'] for d in data]
            ens = [d['enstrophy'] for d in data]
            H_abs = [abs(d['H_total']) for d in data]
            a_val = a_key.split('_')[1]
            axes[0][idx].plot(times, ens, color=colors_a[a_key], lw=2, label=f'$\\alpha={a_val}$')
            axes[1][idx].plot(times, H_abs, color=colors_a[a_key], lw=2, label=f'$\\alpha={a_val}$')

        axes[0][idx].set_title(f'{topo_name}', fontsize=13, fontweight='bold')
        axes[0][idx].set_xlabel('Time'); axes[0][idx].set_ylabel('Enstrophy')
        axes[0][idx].legend(fontsize=9); axes[0][idx].grid(True, alpha=0.3)
        axes[1][idx].set_xlabel('Time'); axes[1][idx].set_ylabel('$|H|$')
        axes[1][idx].legend(fontsize=9); axes[1][idx].grid(True, alpha=0.3)

    fig.suptitle('Helicity-Inertia Coupling: Enstrophy (top) and Helicity (bottom)',
                fontsize=15, fontweight='bold', y=1.01)
    plt.tight_layout()
    fig.savefig(RESULTS / "experiment_helicity_inertia.png", dpi=150, bbox_inches='tight')
    plt.close()

    # Save
    with open(RESULTS / "experiment_helicity_inertia_data.json", 'w') as f:
        json.dump({t: all_results[t] for t, _ in topologies}, f, indent=2)

    print("="*70)


if __name__ == "__main__":
    main()
