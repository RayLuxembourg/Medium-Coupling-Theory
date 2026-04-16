"""
EXPERIMENT: Compressible NS + MCT Coupling
============================================

BACKGROUND:
  The incompressible formulation killed the coupling: grad(phi) is a
  gradient field, absorbed by the Leray projection. In compressible
  flow there is no projection. The coupling force creates real density
  variations through compression/rarefaction. These density variations
  propagate as sound waves and affect the flow.

  This is how gravity actually works in astrophysical fluids.

EQUATIONS (compressible, primitive variables):
  d(rho)/dt + u . grad(rho) + rho * div(u) = 0
  d(u)/dt + (u . grad)u = -(c_s^2 / rho) * grad(rho) + nu * laplacian(u) + alpha * grad(phi)
  laplacian(phi) = -4*pi*alpha * |omega|

  Equation of state: p = c_s^2 * rho  (isothermal)

PROTOCOL:
  For trefoil knot:
    Run A: coupling OFF (alpha=0), compressible NS
    Run B: coupling ON  (alpha=0.05), compressible NS
    Run C: coupling ON  (alpha=0.15), compressible NS
    Run D: coupling ON  (alpha=0.05), nearly incompressible (c_s=100)

  Run D is the sanity check: at high c_s, density variations vanish
  and we should recover the incompressible null result.

MEASUREMENTS:
  - Enstrophy (structure strength)
  - Kinetic energy
  - Density contrast: max(rho)/min(rho) and std(rho)
  - Density at vortex center vs background
  - Sound wave energy (compressible KE component)

SELF-CRITICISM:
  - The coupling force alpha*grad(phi) is still a gradient. It creates
    density variations but does NOT directly generate vorticity. The
    baroclinic term (grad(rho) x grad(p) / rho^2) only generates
    vorticity when density and pressure gradients are misaligned. For
    our barotropic EOS (p = c_s^2 * rho), they are always aligned.
    So the coupling may create density variations without affecting
    the vorticity evolution. This would mean it changes where mass
    accumulates but not how the vortex evolves.
  - However: the density-weighted momentum (rho*u) IS affected even
    if vorticity isn't. A denser vortex core has more momentum and
    may resist dissipation differently.
  - The isothermal EOS is simple but limiting. A more realistic
    polytropic or adiabatic EOS would have baroclinic effects.

STEELMAN FOR STANDARD PHYSICS:
  - Compressible flow with self-gravity is standard astrophysics
    (Jeans instability, star formation). If the coupling produces
    gravitational collapse, that's just Jeans instability, not MCT.
  - The novel MCT claim is that VORTICITY (not mass density) is the
    gravitational source. In standard gravity, the source is rho.
    In MCT, the source is |omega|. If using vorticity as the source
    produces qualitatively different behavior from using density,
    THAT would be genuinely new.
"""

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

# We don't need Taichi for the initial condition anymore if we use a
# simpler initialization. But let's keep it for consistency.
import taichi as ti
ti.init(arch=ti.cuda, default_fp=ti.f64)

RESULTS = Path(__file__).parent / "results"
RESULTS.mkdir(exist_ok=True)

N = 128
L = 2.0 * np.pi
dx = L / N
nu = 0.008
N_STEPS = 3000
MEASURE_EVERY = 10

# ── Taichi Biot-Savart for initialization ──
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


def init_velocity(center, Gamma=2.0, core_a=0.2):
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


# ── Compressible GPU Solver ──
class CompressibleSolver:
    def __init__(self, c_s=10.0):
        self.c_s = c_s

        # Wavenumbers for spectral derivatives
        k = np.fft.fftfreq(N, d=L/(2*np.pi*N))
        KX, KY, KZ = np.meshgrid(k, k, k, indexing='ij')
        self.KX = cp.asarray(KX); self.KY = cp.asarray(KY); self.KZ = cp.asarray(KZ)
        self.K2 = self.KX**2 + self.KY**2 + self.KZ**2
        self.K2s = self.K2.copy(); self.K2s[0,0,0] = 1.0

        # CFL: dt < dx / (c_s + u_max)
        # With c_s=10, u_max~3: dt < 0.049/13 ~ 0.0038
        # Use dt = 0.001 for safety
        self.dt = min(0.001, 0.3 * dx / (c_s + 5.0))
        print(f"    dt = {self.dt:.6f} (CFL for c_s={c_s})")

    def spectral_grad(self, f):
        """Compute gradient of scalar field f using FFT."""
        fh = cp.fft.fftn(f)
        gx = cp.real(cp.fft.ifftn(1j * self.KX * fh))
        gy = cp.real(cp.fft.ifftn(1j * self.KY * fh))
        gz = cp.real(cp.fft.ifftn(1j * self.KZ * fh))
        return gx, gy, gz

    def spectral_div(self, fx, fy, fz):
        """Compute divergence of vector field."""
        fxh = cp.fft.fftn(fx); fyh = cp.fft.fftn(fy); fzh = cp.fft.fftn(fz)
        return cp.real(cp.fft.ifftn(1j*self.KX*fxh + 1j*self.KY*fyh + 1j*self.KZ*fzh))

    def spectral_curl_mag(self, ux, uy, uz):
        """Compute |curl(u)|."""
        uxh = cp.fft.fftn(ux); uyh = cp.fft.fftn(uy); uzh = cp.fft.fftn(uz)
        wx = cp.real(cp.fft.ifftn(1j*self.KY*uzh - 1j*self.KZ*uyh))
        wy = cp.real(cp.fft.ifftn(1j*self.KZ*uxh - 1j*self.KX*uzh))
        wz = cp.real(cp.fft.ifftn(1j*self.KX*uyh - 1j*self.KY*uxh))
        return cp.sqrt(wx**2 + wy**2 + wz**2)

    def spectral_laplacian(self, f):
        """Compute laplacian."""
        fh = cp.fft.fftn(f)
        return cp.real(cp.fft.ifftn(-self.K2 * fh))

    def poisson_solve(self, source):
        """Solve laplacian(phi) = source."""
        sh = cp.fft.fftn(source)
        ph = -sh / self.K2s
        ph[0, 0, 0] = 0
        return cp.real(cp.fft.ifftn(ph))

    def step(self, rho, ux, uy, uz, alpha_val):
        """One time step of compressible NS + MCT coupling.

        Equations (primitive variables):
          d(rho)/dt = -u.grad(rho) - rho * div(u)
          d(u)/dt   = -(u.grad)u - (c_s^2/rho)*grad(rho) + nu*lap(u) + alpha*grad(phi)
          lap(phi)  = -4*pi*alpha*|omega|
        """
        dt = self.dt
        c_s2 = self.c_s**2

        # Vorticity magnitude (MCT source)
        omega = self.spectral_curl_mag(ux, uy, uz)

        # Coupling potential
        if alpha_val > 0:
            phi = self.poisson_solve(-4*cp.pi*alpha_val * omega)
            gphi_x, gphi_y, gphi_z = self.spectral_grad(phi)
        else:
            phi = cp.zeros_like(rho)
            gphi_x = gphi_y = gphi_z = cp.zeros_like(rho)

        # Pressure gradient: (c_s^2 / rho) * grad(rho)
        grho_x, grho_y, grho_z = self.spectral_grad(rho)
        rho_safe = cp.maximum(rho, 0.01)  # prevent division by zero
        pcoeff = c_s2 / rho_safe

        # Advection: (u . grad) u
        gux_x, gux_y, gux_z = self.spectral_grad(ux)
        guy_x, guy_y, guy_z = self.spectral_grad(uy)
        guz_x, guz_y, guz_z = self.spectral_grad(uz)
        adv_x = ux*gux_x + uy*gux_y + uz*gux_z
        adv_y = ux*guy_x + uy*guy_y + uz*guy_z
        adv_z = ux*guz_x + uy*guz_y + uz*guz_z

        # Viscous diffusion
        lap_ux = self.spectral_laplacian(ux)
        lap_uy = self.spectral_laplacian(uy)
        lap_uz = self.spectral_laplacian(uz)

        # Density advection: u . grad(rho)
        adv_rho = ux*grho_x + uy*grho_y + uz*grho_z
        div_u = self.spectral_div(ux, uy, uz)

        # Update density
        rho_new = rho + dt * (-adv_rho - rho * div_u)
        rho_new = cp.maximum(rho_new, 0.01)  # floor

        # Update velocity
        ux_new = ux + dt * (-adv_x - pcoeff*grho_x + nu*lap_ux + alpha_val*gphi_x)
        uy_new = uy + dt * (-adv_y - pcoeff*grho_y + nu*lap_uy + alpha_val*gphi_y)
        uz_new = uz + dt * (-adv_z - pcoeff*grho_z + nu*lap_uz + alpha_val*gphi_z)

        # Clip for stability
        ux_new = cp.clip(ux_new, -20, 20)
        uy_new = cp.clip(uy_new, -20, 20)
        uz_new = cp.clip(uz_new, -20, 20)

        return rho_new, ux_new, uy_new, uz_new, omega, phi

    def measure(self, rho, ux, uy, uz, alpha_val):
        """Compute diagnostics."""
        omega = self.spectral_curl_mag(ux, uy, uz)
        KE = float(0.5 * cp.sum(rho * (ux**2 + uy**2 + uz**2)).get()) * dx**3
        enstrophy = float(0.5 * cp.sum(omega**2).get()) * dx**3
        omega_max = float(cp.max(omega).get())

        rho_cpu = cp.asnumpy(rho)
        rho_mean = float(np.mean(rho_cpu))
        rho_std = float(np.std(rho_cpu))
        rho_min = float(np.min(rho_cpu))
        rho_max = float(np.max(rho_cpu))
        rho_contrast = rho_max / max(rho_min, 0.001)

        # Density at vortex center vs background
        mid = N//2
        rho_center = float(rho_cpu[mid, mid, mid])

        # Divergence (compressibility measure)
        div_u = self.spectral_div(ux, uy, uz)
        div_rms = float(cp.sqrt(cp.mean(div_u**2)).get())

        return {
            'KE': KE,
            'enstrophy': enstrophy,
            'omega_max': omega_max,
            'rho_mean': rho_mean,
            'rho_std': rho_std,
            'rho_min': rho_min,
            'rho_max': rho_max,
            'rho_contrast': rho_contrast,
            'rho_center': rho_center,
            'div_rms': div_rms,
        }


def run_experiment(alpha_val, c_s, label):
    """Run one compressible simulation."""
    center = [L/2, L/2, L/2]
    print(f"\n  [{label}] alpha={alpha_val}, c_s={c_s}")

    # Initialize velocity from Biot-Savart
    ux_np, uy_np, uz_np = init_velocity(center)

    # Initialize density: uniform rho=1
    rho_np = np.ones((N, N, N))

    solver = CompressibleSolver(c_s=c_s)
    rho_g = cp.asarray(rho_np)
    ux_g = cp.asarray(ux_np); uy_g = cp.asarray(uy_np); uz_g = cp.asarray(uz_np)

    # Adjust step count for CFL
    actual_steps = N_STEPS
    effective_time = actual_steps * solver.dt
    print(f"    {actual_steps} steps, dt={solver.dt:.6f}, T_final={effective_time:.3f}")

    measurements = []
    t0 = time.time()

    for s in range(actual_steps + 1):
        if s % MEASURE_EVERY == 0:
            m = solver.measure(rho_g, ux_g, uy_g, uz_g, alpha_val)
            m['step'] = s
            m['time'] = s * solver.dt
            measurements.append(m)

            if s % 500 == 0:
                print(f"    step {s:5d}: ens={m['enstrophy']:.4f} KE={m['KE']:.4f} "
                      f"rho_std={m['rho_std']:.6f} div_rms={m['div_rms']:.6f} "
                      f"rho_contrast={m['rho_contrast']:.6f}")

        if s < actual_steps:
            rho_g, ux_g, uy_g, uz_g, _, _ = solver.step(rho_g, ux_g, uy_g, uz_g, alpha_val)

    elapsed = time.time() - t0
    print(f"    Done: {elapsed:.1f}s ({elapsed/actual_steps*1000:.1f}ms/step)")

    return measurements, solver.dt


def main():
    print("="*70)
    print("EXPERIMENT: Compressible NS + MCT Coupling")
    print(f"Grid: {N}^3, nu={nu}, {N_STEPS} steps")
    print("="*70)

    runs = [
        # (alpha, c_s, label)
        (0.00,  10.0, "control_cs10"),
        (0.05,  10.0, "alpha005_cs10"),
        (0.15,  10.0, "alpha015_cs10"),
        (0.05, 100.0, "alpha005_cs100"),  # near-incompressible sanity check
    ]

    all_results = {}
    for alpha_val, c_s, label in runs:
        measurements, dt_used = run_experiment(alpha_val, c_s, label)
        all_results[label] = {'measurements': measurements, 'dt': dt_used,
                              'alpha': alpha_val, 'c_s': c_s}

    # ── Analysis ──
    print("\n" + "="*70)
    print("ANALYSIS")
    print("="*70)

    # Use physical time (not step number) for comparison since dt varies
    fig, axes = plt.subplots(2, 3, figsize=(21, 12))

    colors = {
        'control_cs10': '#cc2222',
        'alpha005_cs10': '#2222cc',
        'alpha015_cs10': '#22aa22',
        'alpha005_cs100': '#888888',
    }
    labels_map = {
        'control_cs10': 'No coupling ($\\alpha=0$, $c_s=10$)',
        'alpha005_cs10': '$\\alpha=0.05$, $c_s=10$',
        'alpha015_cs10': '$\\alpha=0.15$, $c_s=10$',
        'alpha005_cs100': '$\\alpha=0.05$, $c_s=100$ (near-incomp.)',
    }

    for label in all_results:
        data = all_results[label]['measurements']
        times = [d['time'] for d in data]
        c = colors[label]
        lab = labels_map[label]

        # Enstrophy
        axes[0][0].plot(times, [d['enstrophy'] for d in data], color=c, lw=2, label=lab)
        # KE
        axes[0][1].plot(times, [d['KE'] for d in data], color=c, lw=2, label=lab)
        # Density std
        axes[0][2].plot(times, [d['rho_std'] for d in data], color=c, lw=2, label=lab)
        # Density contrast
        axes[1][0].plot(times, [d['rho_contrast'] for d in data], color=c, lw=2, label=lab)
        # Omega max
        axes[1][1].plot(times, [d['omega_max'] for d in data], color=c, lw=2, label=lab)
        # Divergence RMS
        axes[1][2].plot(times, [d['div_rms'] for d in data], color=c, lw=2, label=lab)

    titles = ['Enstrophy', 'Kinetic Energy', 'Density Std Dev',
              'Density Contrast (max/min)', 'Peak Vorticity', 'Divergence RMS']
    ylabels = ['Enstrophy', 'KE', '$\\sigma_\\rho$',
               '$\\rho_{max}/\\rho_{min}$', '$|\\omega|_{max}$', '$\\sqrt{\\langle(\\nabla\\cdot u)^2\\rangle}$']

    for i, ax in enumerate(axes.flat):
        ax.set_xlabel('Time', fontsize=11)
        ax.set_ylabel(ylabels[i], fontsize=11)
        ax.set_title(titles[i], fontsize=13, fontweight='bold')
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

    fig.suptitle('Compressible NS + MCT: Does Coupling Change the Dynamics?',
                fontsize=15, fontweight='bold', y=1.01)
    plt.tight_layout()
    fig.savefig(RESULTS / "experiment_compressible.png", dpi=150, bbox_inches='tight')
    plt.close()

    # ── Enstrophy ratio plot (the key comparison) ──
    fig2, axes2 = plt.subplots(1, 2, figsize=(16, 6))

    ctrl = all_results['control_cs10']['measurements']
    ctrl_times = [d['time'] for d in ctrl]
    ctrl_ens = np.array([d['enstrophy'] for d in ctrl])

    for label in ['alpha005_cs10', 'alpha015_cs10', 'alpha005_cs100']:
        data = all_results[label]['measurements']
        test_times = [d['time'] for d in data]
        test_ens = np.array([d['enstrophy'] for d in data])

        # Interpolate to common time grid for ratio
        min_len = min(len(ctrl_ens), len(test_ens))
        # Use step-matched (same physical time via index since we measure every MEASURE_EVERY)
        ratio = test_ens[:min_len] / np.maximum(ctrl_ens[:min_len], 1e-10)
        t_common = ctrl_times[:min_len]

        axes2[0].plot(t_common, ratio, color=colors[label], lw=2, label=labels_map[label])

    axes2[0].axhline(1.0, color='black', ls='--', lw=1, alpha=0.5, label='No difference')
    axes2[0].set_xlabel('Time', fontsize=12)
    axes2[0].set_ylabel('Enstrophy ratio (coupled / control)', fontsize=12)
    axes2[0].set_title('Coupling Effect on Structure Stability', fontsize=14, fontweight='bold')
    axes2[0].legend(fontsize=9)
    axes2[0].grid(True, alpha=0.3)

    # Density variation comparison
    for label in ['control_cs10', 'alpha005_cs10', 'alpha015_cs10']:
        data = all_results[label]['measurements']
        times = [d['time'] for d in data]
        axes2[1].plot(times, [d['rho_std'] for d in data],
                     color=colors[label], lw=2, label=labels_map[label])

    axes2[1].set_xlabel('Time', fontsize=12)
    axes2[1].set_ylabel('$\\sigma_\\rho$', fontsize=12)
    axes2[1].set_title('Density Variations from Coupling', fontsize=14, fontweight='bold')
    axes2[1].legend(fontsize=9)
    axes2[1].grid(True, alpha=0.3)

    plt.tight_layout()
    fig2.savefig(RESULTS / "experiment_compressible_ratio.png", dpi=150, bbox_inches='tight')
    plt.close()

    # ── Print verdict ──
    print("\nENSTROPHY AT END OF RUN:")
    for label in all_results:
        data = all_results[label]['measurements']
        ens_0 = data[0]['enstrophy']
        ens_f = data[-1]['enstrophy']
        rho_std_f = data[-1]['rho_std']
        print(f"  {label:25s}: ens {ens_0:.4f} -> {ens_f:.4f} "
              f"(ratio {ens_f/ens_0:.6f})  rho_std={rho_std_f:.6f}")

    # Compare coupled vs uncoupled
    ctrl_final = all_results['control_cs10']['measurements'][-1]['enstrophy']
    print("\nENSTROPHY RATIO (coupled / uncoupled) at end:")
    for label in ['alpha005_cs10', 'alpha015_cs10', 'alpha005_cs100']:
        test_final = all_results[label]['measurements'][-1]['enstrophy']
        ratio = test_final / ctrl_final if ctrl_final > 0 else 0
        status = "STABILIZES" if ratio > 1.001 else "DESTABILIZES" if ratio < 0.999 else "NO EFFECT"
        print(f"  {label:25s}: ratio = {ratio:.6f}  -> {status}")

    # Density variations
    print("\nDENSITY VARIATIONS (rho_std at end):")
    for label in all_results:
        data = all_results[label]['measurements']
        rho_std = data[-1]['rho_std']
        coupling_creates_density = rho_std > 0.001
        print(f"  {label:25s}: rho_std = {rho_std:.8f}  "
              f"{'DENSITY VARIES' if coupling_creates_density else 'uniform'}")

    print("\nVERDICT:")
    ctrl_final_ens = all_results['control_cs10']['measurements'][-1]['enstrophy']
    test_final_ens = all_results['alpha015_cs10']['measurements'][-1]['enstrophy']
    ratio_main = test_final_ens / ctrl_final_ens if ctrl_final_ens > 0 else 1.0
    rho_std_ctrl = all_results['control_cs10']['measurements'][-1]['rho_std']
    rho_std_test = all_results['alpha015_cs10']['measurements'][-1]['rho_std']

    if abs(ratio_main - 1.0) > 0.01:
        if ratio_main > 1.0:
            print(f"  Coupling STABILIZES structure (ratio={ratio_main:.4f})")
            print(f"  This is a genuine dynamical effect of compressible MCT coupling.")
        else:
            print(f"  Coupling DESTABILIZES structure (ratio={ratio_main:.4f})")
            print(f"  This is a real effect but problematic for MCT particle stability.")
    elif rho_std_test > rho_std_ctrl * 2:
        print(f"  Coupling creates density variations (rho_std {rho_std_ctrl:.6f} -> {rho_std_test:.6f})")
        print(f"  but does not significantly affect vortex stability.")
        print(f"  The coupling changes WHERE mass accumulates but not HOW the vortex decays.")
    else:
        print(f"  Coupling has NO significant effect even in compressible flow.")
        print(f"  The MCT coupling mechanism may need fundamental rethinking.")

    # Sanity check
    test_cs100 = all_results['alpha005_cs100']['measurements'][-1]['enstrophy']
    ratio_cs100 = test_cs100 / ctrl_final_ens if ctrl_final_ens > 0 else 1.0
    print(f"\nSANITY CHECK (near-incompressible c_s=100):")
    print(f"  Enstrophy ratio = {ratio_cs100:.6f}")
    if abs(ratio_cs100 - 1.0) < abs(ratio_main - 1.0):
        print(f"  Effect is WEAKER at high c_s. Compressibility IS the mechanism.")
    else:
        print(f"  Effect is NOT weaker at high c_s. Something else is going on.")

    # Save data
    save_data = {}
    for label in all_results:
        save_data[label] = {
            'alpha': all_results[label]['alpha'],
            'c_s': all_results[label]['c_s'],
            'dt': all_results[label]['dt'],
            'measurements': all_results[label]['measurements'],
        }
    with open(RESULTS / "experiment_compressible_data.json", 'w') as f:
        json.dump(save_data, f, indent=2)

    print(f"\nSaved: experiment_compressible.png, experiment_compressible_ratio.png")
    print("="*70)


if __name__ == "__main__":
    main()
