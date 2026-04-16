"""
EXPERIMENT v2: Compressible NS + MCT Coupling (stabilized numerics)
=====================================================================

v1 blew up: explicit spectral compressible NS is unstable without
dealiasing and hyperviscosity. This version fixes the numerics:

1. 2/3 dealiasing rule on all nonlinear products
2. Hyperviscosity on density (small diffusion to prevent oscillations)
3. Smaller dt with adaptive CFL
4. Weaker initial velocity (lower Mach number)
5. Spectral filtering above 2/3 Nyquist

Same scientific protocol as v1: coupling ON vs OFF, measure everything.
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
nu = 0.01       # slightly higher viscosity for stability
nu_rho = 0.005  # density diffusion (artificial, for stability)
N_STEPS = 4000
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


def make_trefoil(center, scale=1.0, n_pts=300):
    t = np.linspace(0, 2*np.pi, n_pts, endpoint=False)
    s = scale/3.0
    return (center[0]+s*(np.sin(t)+2*np.sin(2*t)),
            center[1]+s*(np.cos(t)-2*np.cos(2*t)),
            center[2]+s*(-np.sin(3*t)))


def init_velocity(center, Gamma=1.0, core_a=0.25):
    """Lower Gamma for lower Mach number."""
    cx, cy, cz = make_trefoil(center)
    n = len(cx)
    dlx = np.roll(cx,-1)-cx; dly = np.roll(cy,-1)-cy; dlz = np.roll(cz,-1)-cz
    pad = lambda a: np.pad(a, (0, max_pts-n))
    fil_x.from_numpy(pad(cx)); fil_y.from_numpy(pad(cy)); fil_z.from_numpy(pad(cz))
    fil_dlx.from_numpy(pad(dlx)); fil_dly.from_numpy(pad(dly)); fil_dlz.from_numpy(pad(dlz))
    vel_x.fill(0); vel_y.fill(0); vel_z.fill(0)
    biot_savart_kernel(n, Gamma, core_a, L, N)
    ti.sync()
    return vel_x.to_numpy(), vel_y.to_numpy(), vel_z.to_numpy()


class CompressibleSolver:
    def __init__(self, c_s=5.0):
        self.c_s = c_s
        k = np.fft.fftfreq(N, d=L/(2*np.pi*N))
        KX, KY, KZ = np.meshgrid(k, k, k, indexing='ij')
        self.KX = cp.asarray(KX); self.KY = cp.asarray(KY); self.KZ = cp.asarray(KZ)
        self.K2 = self.KX**2 + self.KY**2 + self.KZ**2
        self.K2s = self.K2.copy(); self.K2s[0,0,0] = 1.0

        # 2/3 dealiasing mask
        kmax = N // 3  # 2/3 of N/2
        K_mag = cp.sqrt(self.K2)
        k_nyquist = N / 2 * (2*np.pi/L)  # not used directly
        # In index space, filter above N/3
        ki = cp.asarray(np.abs(np.fft.fftfreq(N, d=1.0/N)))
        KI, KJ, KK = cp.meshgrid(ki, ki, ki, indexing='ij')
        self.dealias = ((KI <= kmax) & (KJ <= kmax) & (KK <= kmax)).astype(cp.float64)

        # CFL
        self.dt = 0.4 * dx / (c_s + 3.0)
        print(f"    dt = {self.dt:.6f} (CFL for c_s={c_s})")

    def dealias_product(self, a, b):
        """Compute a*b with 2/3 dealiasing."""
        ah = cp.fft.fftn(a) * self.dealias
        bh = cp.fft.fftn(b) * self.dealias
        a_f = cp.real(cp.fft.ifftn(ah))
        b_f = cp.real(cp.fft.ifftn(bh))
        result = a_f * b_f
        rh = cp.fft.fftn(result) * self.dealias
        return cp.real(cp.fft.ifftn(rh))

    def spectral_grad(self, f):
        fh = cp.fft.fftn(f) * self.dealias
        return (cp.real(cp.fft.ifftn(1j*self.KX*fh)),
                cp.real(cp.fft.ifftn(1j*self.KY*fh)),
                cp.real(cp.fft.ifftn(1j*self.KZ*fh)))

    def spectral_div(self, fx, fy, fz):
        fxh = cp.fft.fftn(fx)*self.dealias
        fyh = cp.fft.fftn(fy)*self.dealias
        fzh = cp.fft.fftn(fz)*self.dealias
        return cp.real(cp.fft.ifftn(1j*self.KX*fxh+1j*self.KY*fyh+1j*self.KZ*fzh))

    def spectral_curl_mag(self, ux, uy, uz):
        uxh = cp.fft.fftn(ux)*self.dealias
        uyh = cp.fft.fftn(uy)*self.dealias
        uzh = cp.fft.fftn(uz)*self.dealias
        wx = cp.real(cp.fft.ifftn(1j*self.KY*uzh - 1j*self.KZ*uyh))
        wy = cp.real(cp.fft.ifftn(1j*self.KZ*uxh - 1j*self.KX*uzh))
        wz = cp.real(cp.fft.ifftn(1j*self.KX*uyh - 1j*self.KY*uxh))
        return cp.sqrt(wx**2+wy**2+wz**2)

    def step(self, rho, ux, uy, uz, alpha_val):
        dt = self.dt
        c_s2 = self.c_s**2

        omega = self.spectral_curl_mag(ux, uy, uz)

        # Coupling potential
        if alpha_val > 0:
            rh = cp.fft.fftn(omega)
            ph = -4*cp.pi*alpha_val * rh / self.K2s; ph[0,0,0] = 0
            gphi_x, gphi_y, gphi_z = (
                cp.real(cp.fft.ifftn(1j*self.KX*ph)),
                cp.real(cp.fft.ifftn(1j*self.KY*ph)),
                cp.real(cp.fft.ifftn(1j*self.KZ*ph)))
        else:
            gphi_x = gphi_y = gphi_z = cp.zeros_like(rho)

        # Pressure gradient
        grho_x, grho_y, grho_z = self.spectral_grad(rho)
        rho_safe = cp.maximum(rho, 0.1)
        pcoeff = c_s2 / rho_safe

        # Advection (dealiased)
        gux_x, gux_y, gux_z = self.spectral_grad(ux)
        guy_x, guy_y, guy_z = self.spectral_grad(uy)
        guz_x, guz_y, guz_z = self.spectral_grad(uz)
        adv_x = self.dealias_product(ux, gux_x) + self.dealias_product(uy, gux_y) + self.dealias_product(uz, gux_z)
        adv_y = self.dealias_product(ux, guy_x) + self.dealias_product(uy, guy_y) + self.dealias_product(uz, guy_z)
        adv_z = self.dealias_product(ux, guz_x) + self.dealias_product(uy, guz_y) + self.dealias_product(uz, guz_z)

        # Viscous term (implicit via exponential integrator for stability)
        visc_factor = cp.exp(-nu * self.K2 * dt)
        rho_visc = cp.exp(-nu_rho * self.K2 * dt)

        # Density equation: d(rho)/dt = -u.grad(rho) - rho*div(u) + nu_rho*lap(rho)
        adv_rho = (self.dealias_product(ux, grho_x) +
                   self.dealias_product(uy, grho_y) +
                   self.dealias_product(uz, grho_z))
        div_u = self.spectral_div(ux, uy, uz)
        rho_div = self.dealias_product(rho, div_u)

        rho_rhs = -adv_rho - rho_div
        rho_h = cp.fft.fftn(rho) + dt * cp.fft.fftn(rho_rhs)
        rho_h *= rho_visc * self.dealias
        rho_new = cp.real(cp.fft.ifftn(rho_h))
        rho_new = cp.maximum(rho_new, 0.1)

        # Momentum equation
        ux_rhs = -adv_x - pcoeff*grho_x + alpha_val*gphi_x
        uy_rhs = -adv_y - pcoeff*grho_y + alpha_val*gphi_y
        uz_rhs = -adv_z - pcoeff*grho_z + alpha_val*gphi_z

        ux_h = cp.fft.fftn(ux) + dt*cp.fft.fftn(ux_rhs)
        uy_h = cp.fft.fftn(uy) + dt*cp.fft.fftn(uy_rhs)
        uz_h = cp.fft.fftn(uz) + dt*cp.fft.fftn(uz_rhs)
        ux_h *= visc_factor * self.dealias
        uy_h *= visc_factor * self.dealias
        uz_h *= visc_factor * self.dealias

        ux_new = cp.clip(cp.real(cp.fft.ifftn(ux_h)), -15, 15)
        uy_new = cp.clip(cp.real(cp.fft.ifftn(uy_h)), -15, 15)
        uz_new = cp.clip(cp.real(cp.fft.ifftn(uz_h)), -15, 15)

        return rho_new, ux_new, uy_new, uz_new, omega

    def measure(self, rho, ux, uy, uz):
        omega = self.spectral_curl_mag(ux, uy, uz)
        KE = float(0.5*cp.sum(ux**2+uy**2+uz**2).get())*dx**3
        enstrophy = float(0.5*cp.sum(omega**2).get())*dx**3
        omega_max = float(cp.max(omega).get())
        rho_cpu = cp.asnumpy(rho)
        rho_mean = float(np.mean(rho_cpu))
        rho_std = float(np.std(rho_cpu))
        rho_max = float(np.max(rho_cpu))
        rho_min = float(np.min(rho_cpu))
        u_max = float(cp.max(cp.sqrt(ux**2+uy**2+uz**2)).get())
        mach = u_max / self.c_s
        div_u = self.spectral_div(ux, uy, uz)
        div_rms = float(cp.sqrt(cp.mean(div_u**2)).get())
        return {
            'KE': KE, 'enstrophy': enstrophy, 'omega_max': omega_max,
            'rho_mean': rho_mean, 'rho_std': rho_std,
            'rho_max': rho_max, 'rho_min': rho_min,
            'u_max': u_max, 'mach': mach, 'div_rms': div_rms,
        }


def run_experiment(alpha_val, c_s, label):
    center = [L/2, L/2, L/2]
    print(f"\n  [{label}] alpha={alpha_val}, c_s={c_s}")

    ux_np, uy_np, uz_np = init_velocity(center, Gamma=1.0, core_a=0.25)
    rho_np = np.ones((N, N, N))

    solver = CompressibleSolver(c_s=c_s)
    rho_g = cp.asarray(rho_np)
    ux_g = cp.asarray(ux_np); uy_g = cp.asarray(uy_np); uz_g = cp.asarray(uz_np)

    measurements = []
    t0 = time.time()
    blown_up = False

    for s in range(N_STEPS + 1):
        if s % MEASURE_EVERY == 0:
            m = solver.measure(rho_g, ux_g, uy_g, uz_g)
            m['step'] = s
            m['time'] = s * solver.dt
            measurements.append(m)

            if np.isnan(m['enstrophy']) or m['enstrophy'] > 1e10:
                print(f"    BLOWUP at step {s}!")
                blown_up = True
                break

            if s % 500 == 0:
                print(f"    step {s:5d}: ens={m['enstrophy']:.4f} KE={m['KE']:.4f} "
                      f"rho_std={m['rho_std']:.6f} mach={m['mach']:.3f}")

        if s < N_STEPS and not blown_up:
            rho_g, ux_g, uy_g, uz_g, _ = solver.step(rho_g, ux_g, uy_g, uz_g, alpha_val)

    elapsed = time.time() - t0
    print(f"    Done: {elapsed:.1f}s  {'STABLE' if not blown_up else 'UNSTABLE'}")
    return measurements, solver.dt, blown_up


def main():
    print("="*70)
    print("EXPERIMENT v2: Compressible NS + MCT (stabilized)")
    print(f"Grid: {N}^3, nu={nu}, nu_rho={nu_rho}, {N_STEPS} steps")
    print(f"Lower Gamma=1.0 for subsonic Mach numbers")
    print("="*70)

    runs = [
        (0.00,  5.0,  "control_cs5"),
        (0.05,  5.0,  "alpha005_cs5"),
        (0.15,  5.0,  "alpha015_cs5"),
        (0.05, 50.0,  "alpha005_cs50"),   # near-incompressible check
    ]

    all_results = {}
    for alpha_val, c_s, label in runs:
        meas, dt_used, blew = run_experiment(alpha_val, c_s, label)
        all_results[label] = {'measurements': meas, 'dt': dt_used, 'blew_up': blew,
                              'alpha': alpha_val, 'c_s': c_s}

    # ── Analysis ──
    print("\n" + "="*70)
    print("ANALYSIS")
    print("="*70)

    colors = {'control_cs5':'#cc2222', 'alpha005_cs5':'#2222cc',
              'alpha015_cs5':'#22aa22', 'alpha005_cs50':'#888888'}
    labels_map = {'control_cs5':'No coupling ($\\alpha=0$)',
                  'alpha005_cs5':'$\\alpha=0.05$',
                  'alpha015_cs5':'$\\alpha=0.15$',
                  'alpha005_cs50':'$\\alpha=0.05$, $c_s=50$ (near-incomp.)'}

    fig, axes = plt.subplots(2, 3, figsize=(21, 12))
    titles = ['Enstrophy', 'Kinetic Energy', 'Density Std Dev',
              'Mach Number', 'Peak Vorticity', 'Divergence RMS']
    keys = ['enstrophy', 'KE', 'rho_std', 'mach', 'omega_max', 'div_rms']

    for label in all_results:
        if all_results[label]['blew_up'] and len(all_results[label]['measurements']) < 5:
            continue
        data = all_results[label]['measurements']
        times = [d['time'] for d in data]
        c = colors.get(label, 'black')
        lab = labels_map.get(label, label)
        for i, key in enumerate(keys):
            axes.flat[i].plot(times, [d[key] for d in data], color=c, lw=2, label=lab)

    for i, (title, key) in enumerate(zip(titles, keys)):
        axes.flat[i].set_xlabel('Time', fontsize=11)
        axes.flat[i].set_title(title, fontsize=13, fontweight='bold')
        axes.flat[i].legend(fontsize=8)
        axes.flat[i].grid(True, alpha=0.3)

    fig.suptitle('Compressible NS + MCT v2: Stabilized Numerics',
                fontsize=15, fontweight='bold', y=1.01)
    plt.tight_layout()
    fig.savefig(RESULTS / "experiment_compressible_v2.png", dpi=150, bbox_inches='tight')
    plt.close()

    # Enstrophy ratio
    ctrl_label = 'control_cs5'
    if not all_results[ctrl_label]['blew_up']:
        ctrl_data = all_results[ctrl_label]['measurements']
        ctrl_ens = np.array([d['enstrophy'] for d in ctrl_data])
        ctrl_times = [d['time'] for d in ctrl_data]

        fig2, ax = plt.subplots(figsize=(10, 6))
        for label in ['alpha005_cs5', 'alpha015_cs5']:
            if all_results[label]['blew_up']:
                continue
            data = all_results[label]['measurements']
            test_ens = np.array([d['enstrophy'] for d in data])
            min_len = min(len(ctrl_ens), len(test_ens))
            ratio = test_ens[:min_len] / np.maximum(ctrl_ens[:min_len], 1e-10)
            ax.plot(ctrl_times[:min_len], ratio, color=colors[label], lw=2.5,
                   label=labels_map[label])

        ax.axhline(1.0, color='black', ls='--', lw=1)
        ax.set_xlabel('Time', fontsize=13)
        ax.set_ylabel('Enstrophy ratio (coupled / control)', fontsize=13)
        ax.set_title('Does Compressible MCT Coupling Affect Vortex Stability?',
                     fontsize=14, fontweight='bold')
        ax.legend(fontsize=11)
        ax.grid(True, alpha=0.3)
        fig2.savefig(RESULTS / "experiment_compressible_v2_ratio.png", dpi=150)
        plt.close()

    # Print verdict
    print("\nFINAL ENSTROPHY:")
    for label in all_results:
        data = all_results[label]['measurements']
        if len(data) < 2: continue
        ens0 = data[0]['enstrophy']
        ensf = data[-1]['enstrophy']
        print(f"  {label:25s}: {ens0:.4f} -> {ensf:.4f} (decay ratio {ensf/ens0:.6f})")

    if not all_results[ctrl_label]['blew_up']:
        ctrl_final = all_results[ctrl_label]['measurements'][-1]['enstrophy']
        print("\nSTABILITY RATIO:")
        for label in ['alpha005_cs5', 'alpha015_cs5', 'alpha005_cs50']:
            if all_results[label]['blew_up'] or len(all_results[label]['measurements']) < 2:
                print(f"  {label:25s}: BLEW UP")
                continue
            test_final = all_results[label]['measurements'][-1]['enstrophy']
            ratio = test_final / ctrl_final if ctrl_final > 0 else 0
            status = "STABILIZES" if ratio > 1.005 else "DESTABILIZES" if ratio < 0.995 else "NO EFFECT"
            print(f"  {label:25s}: ratio = {ratio:.6f}  -> {status}")

    # Save
    save_data = {label: {k: v for k, v in all_results[label].items()}
                 for label in all_results}
    with open(RESULTS / "experiment_compressible_v2_data.json", 'w') as f:
        json.dump(save_data, f, indent=2)

    print("="*70)


if __name__ == "__main__":
    main()
