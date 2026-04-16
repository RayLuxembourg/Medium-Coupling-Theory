"""
EXPERIMENT: Variable Viscosity MCT Coupling
=============================================

BACKGROUND:
  The gradient force alpha*grad(phi) is algebraically invisible in
  incompressible flow (Leray projection kills it; curl(grad)=0).

  MCT says coupling provides 'grip' on the medium. Grip means
  resistance to deformation. Resistance to deformation IS viscosity.

  Reformulation: the coupling makes the medium locally stiffer where
  angular momentum density is high. The effective viscosity is:

    nu_eff(x) = nu_0 - alpha * phi(x)

  where phi < 0 near vortex structures (gravitational potential well).
  So nu_eff is LOWER where the potential well is deeper, meaning
  LESS dissipation where coupling is strongest.

  Alternatively (and more directly):
    nu_eff(x) = nu_0 * (1 - beta * omega_normalized(x))

  where omega_normalized = |omega| / max(|omega|). This means: more
  vorticity -> less local dissipation -> the structure resists decay.

PHYSICAL MOTIVATION:
  In MCT, a structure's angular momentum interlocks with the medium.
  A strongly coupled region has its flow pattern 'locked in' by the
  interaction with the surrounding medium. This is analogous to
  reduced effective viscosity: the coupling prevents the flow from
  being smoothed away.

  This is similar to how superfluids have zero viscosity because their
  angular momentum is quantized and topologically protected. MCT
  coupling provides a partial version of this protection.

SELF-CRITICISM:
  - Variable viscosity is ad hoc. We chose it because it survives
    the projection, not because it was derived from first principles.
    Any variable viscosity model will produce topology-dependent
    stability. The question is whether the SPECIFIC dependence
    (on vorticity/coupling) produces anything non-trivial.
  - If nu_eff depends on |omega|, then by definition regions with
    more vorticity dissipate less. This is just a nonlinear viscosity
    model. Standard turbulence models (Smagorinsky, dynamic) already
    have variable viscosity. Is this different?
  - The critical test: does the topology of the structure matter,
    or just the total vorticity? If a ring and a trefoil with the
    same total enstrophy decay at the same rate, this is just
    nonlinear viscosity. If they decay at DIFFERENT rates because
    of their topology, that's something new.

PROTOCOL:
  Method A: nu_eff = nu_0 * (1 - beta * |omega|/omega_max)
    beta = 0 (control), 0.3, 0.6, 0.9

  Run for ring AND trefoil. Compare:
    1. Enstrophy decay rate (does coupling slow decay?)
    2. Topology dependence (do ring and trefoil respond differently?)
    3. Structure shape (does coupling change the morphology?)
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

def make_ring(center, R=0.8, n_pts=200):
    t = np.linspace(0, 2*np.pi, n_pts, endpoint=False)
    return center[0]+R*np.cos(t), center[1]+R*np.sin(t), np.full(n_pts, center[2])

def make_trefoil(center, scale=1.0, n_pts=300):
    t = np.linspace(0, 2*np.pi, n_pts, endpoint=False)
    s = scale/3.0
    return (center[0]+s*(np.sin(t)+2*np.sin(2*t)),
            center[1]+s*(np.cos(t)-2*np.cos(2*t)),
            center[2]+s*(-np.sin(3*t)))

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


class VariableViscositySolver:
    """Incompressible NS with vorticity-dependent viscosity.

    nu_eff(x) = nu_0 * (1 - beta * |omega(x)| / omega_ref)

    Implemented in spectral space: the viscous term becomes
    spatially variable, so we compute it in physical space
    and transform back.
    """
    def __init__(self):
        k = np.fft.fftfreq(N, d=L/(2*np.pi*N))
        KX, KY, KZ = np.meshgrid(k, k, k, indexing='ij')
        self.KX = cp.asarray(KX); self.KY = cp.asarray(KY); self.KZ = cp.asarray(KZ)
        self.K2 = self.KX**2 + self.KY**2 + self.KZ**2
        self.K2s = self.K2.copy(); self.K2s[0,0,0] = 1.0

    def step(self, ux, uy, uz, beta, omega_ref):
        """One step with variable viscosity."""
        # Compute vorticity
        uxh = cp.fft.fftn(ux); uyh = cp.fft.fftn(uy); uzh = cp.fft.fftn(uz)
        wx = cp.real(cp.fft.ifftn(1j*self.KY*uzh - 1j*self.KZ*uyh))
        wy = cp.real(cp.fft.ifftn(1j*self.KZ*uxh - 1j*self.KX*uzh))
        wz = cp.real(cp.fft.ifftn(1j*self.KX*uyh - 1j*self.KY*uxh))
        omega = cp.sqrt(wx**2 + wy**2 + wz**2)

        # Variable viscosity field
        # nu_eff = nu_0 * (1 - beta * omega/omega_ref), clamped to [nu_min, nu_0]
        nu_min = nu_0 * 0.05  # never go below 5% of base viscosity
        omega_norm = omega / max(float(omega_ref), 1e-6)
        omega_norm = cp.minimum(omega_norm, 1.0)  # cap at 1
        nu_field = nu_0 * (1.0 - beta * omega_norm)
        nu_field = cp.maximum(nu_field, nu_min)

        # Nonlinear term: omega x u (vortex stretching)
        rhsx = wy*uz - wz*uy
        rhsy = wz*ux - wx*uz
        rhsz = wx*uy - wy*ux

        # Variable viscosity diffusion: div(nu_field * grad(u))
        # In spectral: for each component, compute nu_field * laplacian(u)
        # This is approximate (exact would be div(nu*grad(u)) = nu*lap(u) + grad(nu).grad(u))
        # The full form includes the gradient correction term
        lap_ux = cp.real(cp.fft.ifftn(-self.K2 * uxh))
        lap_uy = cp.real(cp.fft.ifftn(-self.K2 * uyh))
        lap_uz = cp.real(cp.fft.ifftn(-self.K2 * uzh))

        # grad(nu) . grad(u) correction
        gnu_x, gnu_y, gnu_z = self._grad(nu_field)
        gux_x, gux_y, gux_z = self._grad(ux)
        guy_x, guy_y, guy_z = self._grad(uy)
        guz_x, guz_y, guz_z = self._grad(uz)

        visc_x = nu_field * lap_ux + gnu_x*gux_x + gnu_y*gux_y + gnu_z*gux_z
        visc_y = nu_field * lap_uy + gnu_x*guy_x + gnu_y*guy_y + gnu_z*guy_z
        visc_z = nu_field * lap_uz + gnu_x*guz_x + gnu_y*guz_y + gnu_z*guz_z

        # Time step
        uxh_new = uxh + dt * cp.fft.fftn(rhsx + visc_x)
        uyh_new = uyh + dt * cp.fft.fftn(rhsy + visc_y)
        uzh_new = uzh + dt * cp.fft.fftn(rhsz + visc_z)

        # Leray projection (enforce incompressibility)
        div = self.KX*uxh_new + self.KY*uyh_new + self.KZ*uzh_new
        uxh_new -= self.KX*div/self.K2s
        uyh_new -= self.KY*div/self.K2s
        uzh_new -= self.KZ*div/self.K2s
        uxh_new[0,0,0] = 0; uyh_new[0,0,0] = 0; uzh_new[0,0,0] = 0

        ux = cp.clip(cp.real(cp.fft.ifftn(uxh_new)), -20, 20)
        uy = cp.clip(cp.real(cp.fft.ifftn(uyh_new)), -20, 20)
        uz = cp.clip(cp.real(cp.fft.ifftn(uzh_new)), -20, 20)

        return ux, uy, uz, omega

    def _grad(self, f):
        fh = cp.fft.fftn(f)
        return (cp.real(cp.fft.ifftn(1j*self.KX*fh)),
                cp.real(cp.fft.ifftn(1j*self.KY*fh)),
                cp.real(cp.fft.ifftn(1j*self.KZ*fh)))

    def measure(self, ux, uy, uz, beta, omega_ref):
        uxh = cp.fft.fftn(ux); uyh = cp.fft.fftn(uy); uzh = cp.fft.fftn(uz)
        wx = cp.real(cp.fft.ifftn(1j*self.KY*uzh - 1j*self.KZ*uyh))
        wy = cp.real(cp.fft.ifftn(1j*self.KZ*uxh - 1j*self.KX*uzh))
        wz = cp.real(cp.fft.ifftn(1j*self.KX*uyh - 1j*self.KY*uxh))
        omega = cp.sqrt(wx**2+wy**2+wz**2)

        KE = float(0.5*cp.sum(ux**2+uy**2+uz**2).get())*dx**3
        enstrophy = float(0.5*cp.sum(omega**2).get())*dx**3
        omega_max = float(cp.max(omega).get())

        # Effective viscosity stats
        omega_norm = omega / max(float(omega_ref), 1e-6)
        omega_norm = cp.minimum(omega_norm, 1.0)
        nu_field = nu_0 * (1.0 - beta * omega_norm)
        nu_field = cp.maximum(nu_field, nu_0 * 0.05)
        nu_mean = float(cp.mean(nu_field).get())
        nu_min_actual = float(cp.min(nu_field).get())

        return {
            'KE': KE, 'enstrophy': enstrophy, 'omega_max': omega_max,
            'nu_mean': nu_mean, 'nu_min': nu_min_actual,
        }


def run_experiment(topo_name, curve_func, beta, label):
    center = [L/2, L/2, L/2]
    ux_np, uy_np, uz_np = init_velocity(curve_func, center)

    solver = VariableViscositySolver()
    ux_g = cp.asarray(ux_np); uy_g = cp.asarray(uy_np); uz_g = cp.asarray(uz_np)

    # Get initial omega_max as reference for normalization
    m0 = solver.measure(ux_g, uy_g, uz_g, 0, 1.0)
    omega_ref = m0['omega_max']

    measurements = []
    t0 = time.time()

    for s in range(N_STEPS + 1):
        if s % MEASURE_EVERY == 0:
            m = solver.measure(ux_g, uy_g, uz_g, beta, omega_ref)
            m['step'] = s
            m['time'] = s * dt
            measurements.append(m)

            if np.isnan(m['enstrophy']):
                print(f"    BLOWUP at step {s}")
                break

        if s < N_STEPS:
            ux_g, uy_g, uz_g, _ = solver.step(ux_g, uy_g, uz_g, beta, omega_ref)

    elapsed = time.time() - t0
    ens0 = measurements[0]['enstrophy']
    ensf = measurements[-1]['enstrophy']
    print(f"    {label}: {elapsed:.1f}s  ens {ens0:.4f} -> {ensf:.4f} "
          f"(ratio {ensf/ens0:.6f})")
    return measurements


def main():
    print("="*70)
    print("EXPERIMENT: Variable Viscosity MCT Coupling")
    print(f"Grid: {N}^3, dt={dt}, nu_0={nu_0}, {N_STEPS} steps")
    print(f"nu_eff = nu_0 * (1 - beta * |omega|/omega_ref)")
    print("="*70)

    betas = [0.0, 0.3, 0.6, 0.9]
    topologies = [
        ("ring", make_ring),
        ("trefoil", make_trefoil),
    ]

    all_results = {}
    for topo_name, curve_func in topologies:
        print(f"\n  [{topo_name}]")
        all_results[topo_name] = {}
        for beta in betas:
            label = f"beta_{beta:.1f}"
            meas = run_experiment(topo_name, curve_func, beta, label)
            all_results[topo_name][label] = meas

    # ── Analysis ──
    print("\n" + "="*70)
    print("ANALYSIS")
    print("="*70)

    colors = {'beta_0.0':'#cc2222', 'beta_0.3':'#cc8800',
              'beta_0.6':'#2222cc', 'beta_0.9':'#22aa22'}

    fig, axes = plt.subplots(2, 3, figsize=(21, 12))

    for idx, (topo_name, _) in enumerate(topologies):
        results = all_results[topo_name]

        # Enstrophy over time
        ax = axes[0][idx]
        for key in sorted(results.keys()):
            data = results[key]
            times = [d['time'] for d in data]
            ens = [d['enstrophy'] for d in data]
            ax.plot(times, ens, color=colors[key], lw=2,
                   label=f'$\\beta={key.split("_")[1]}$')
        ax.set_xlabel('Time', fontsize=11)
        ax.set_ylabel('Enstrophy', fontsize=11)
        ax.set_title(f'{topo_name}: Enstrophy Decay', fontsize=13, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)

        # Enstrophy ratio to control
        ax = axes[1][idx]
        ctrl = results['beta_0.0']
        ctrl_ens = np.array([d['enstrophy'] for d in ctrl])
        for key in sorted(results.keys()):
            if key == 'beta_0.0': continue
            data = results[key]
            test_ens = np.array([d['enstrophy'] for d in data])
            min_len = min(len(ctrl_ens), len(test_ens))
            ratio = test_ens[:min_len] / np.maximum(ctrl_ens[:min_len], 1e-10)
            times = [d['time'] for d in ctrl[:min_len]]
            ax.plot(times, ratio, color=colors[key], lw=2,
                   label=f'$\\beta={key.split("_")[1]}$')
        ax.axhline(1.0, color='black', ls='--', lw=1)
        ax.set_xlabel('Time', fontsize=11)
        ax.set_ylabel('Enstrophy ratio\n(coupled / control)', fontsize=11)
        ax.set_title(f'{topo_name}: Coupling Effect', fontsize=13, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)

    # Cross-topology comparison: does topology matter?
    ax = axes[0][2]
    for beta_key in ['beta_0.0', 'beta_0.9']:
        for topo_name in ['ring', 'trefoil']:
            data = all_results[topo_name][beta_key]
            ens = np.array([d['enstrophy'] for d in data])
            ens_norm = ens / ens[0]  # normalize to initial
            times = [d['time'] for d in data]
            style = '-' if topo_name == 'ring' else '--'
            color = '#cc2222' if beta_key == 'beta_0.0' else '#22aa22'
            ax.plot(times, ens_norm, style, color=color, lw=2,
                   label=f'{topo_name}, $\\beta={beta_key.split("_")[1]}$')
    ax.set_xlabel('Time', fontsize=11)
    ax.set_ylabel('Normalized enstrophy', fontsize=11)
    ax.set_title('Cross-topology: Does Shape Matter?', fontsize=13, fontweight='bold')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # Topology-dependent effect
    ax = axes[1][2]
    for beta_key in ['beta_0.3', '0.6', 'beta_0.9']:
        if beta_key not in all_results['ring']:
            beta_key_full = f'beta_{beta_key}' if not beta_key.startswith('beta') else beta_key
        else:
            beta_key_full = beta_key

        if beta_key_full not in all_results['ring']: continue

        ring_data = all_results['ring'][beta_key_full]
        tref_data = all_results['trefoil'][beta_key_full]
        ring_ctrl = all_results['ring']['beta_0.0']
        tref_ctrl = all_results['trefoil']['beta_0.0']

        ring_ens = np.array([d['enstrophy'] for d in ring_data])
        tref_ens = np.array([d['enstrophy'] for d in tref_data])
        ring_ctrl_ens = np.array([d['enstrophy'] for d in ring_ctrl])
        tref_ctrl_ens = np.array([d['enstrophy'] for d in tref_ctrl])

        min_len = min(len(ring_ens), len(tref_ens), len(ring_ctrl_ens), len(tref_ctrl_ens))
        ring_ratio = ring_ens[:min_len] / np.maximum(ring_ctrl_ens[:min_len], 1e-10)
        tref_ratio = tref_ens[:min_len] / np.maximum(tref_ctrl_ens[:min_len], 1e-10)

        # Difference in response: does trefoil benefit more than ring?
        diff = tref_ratio - ring_ratio
        times = [d['time'] for d in ring_data[:min_len]]
        color = colors.get(beta_key_full, '#888888')
        beta_val = beta_key_full.split('_')[1]
        ax.plot(times, diff, color=color, lw=2,
               label=f'$\\beta={beta_val}$: trefoil$-$ring ratio')

    ax.axhline(0, color='black', ls='--', lw=1)
    ax.set_xlabel('Time', fontsize=11)
    ax.set_ylabel('Trefoil ratio $-$ Ring ratio', fontsize=11)
    ax.set_title('Topology-Dependent Response\n(>0 = trefoil stabilized more)',
                fontsize=12, fontweight='bold')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    fig.suptitle('Variable Viscosity MCT: Does Coupling Stabilize Structures Topology-Dependently?',
                fontsize=15, fontweight='bold', y=1.01)
    plt.tight_layout()
    fig.savefig(RESULTS / "experiment_variable_viscosity.png", dpi=150, bbox_inches='tight')
    plt.close()

    # ── Print verdict ──
    print("\nENSTROPHY SURVIVAL RATIO (final/initial):")
    for topo_name in ['ring', 'trefoil']:
        for beta_key in sorted(all_results[topo_name].keys()):
            data = all_results[topo_name][beta_key]
            ens0 = data[0]['enstrophy']
            ensf = data[-1]['enstrophy']
            beta_val = beta_key.split('_')[1]
            print(f"  {topo_name:10s} beta={beta_val}: {ensf/ens0:.6f}")

    print("\nSTABILITY RATIO (coupled/control):")
    for topo_name in ['ring', 'trefoil']:
        ctrl = all_results[topo_name]['beta_0.0']
        ctrl_final = ctrl[-1]['enstrophy']
        for beta_key in sorted(all_results[topo_name].keys()):
            if beta_key == 'beta_0.0': continue
            data = all_results[topo_name][beta_key]
            test_final = data[-1]['enstrophy']
            ratio = test_final / ctrl_final if ctrl_final > 0 else 0
            beta_val = beta_key.split('_')[1]
            status = "STABILIZES" if ratio > 1.01 else "DESTABILIZES" if ratio < 0.99 else "NO EFFECT"
            print(f"  {topo_name:10s} beta={beta_val}: ratio={ratio:.6f} -> {status}")

    # Key question: topology dependence
    print("\nTOPOLOGY DEPENDENCE:")
    for beta_key in ['beta_0.3', 'beta_0.6', 'beta_0.9']:
        ring_ctrl = all_results['ring']['beta_0.0'][-1]['enstrophy']
        tref_ctrl = all_results['trefoil']['beta_0.0'][-1]['enstrophy']
        ring_test = all_results['ring'][beta_key][-1]['enstrophy']
        tref_test = all_results['trefoil'][beta_key][-1]['enstrophy']

        ring_ratio = ring_test / ring_ctrl if ring_ctrl > 0 else 1
        tref_ratio = tref_test / tref_ctrl if tref_ctrl > 0 else 1

        beta_val = beta_key.split('_')[1]
        print(f"  beta={beta_val}: ring ratio={ring_ratio:.6f}, trefoil ratio={tref_ratio:.6f}, "
              f"diff={tref_ratio-ring_ratio:.6f}")
        if abs(tref_ratio - ring_ratio) > 0.01:
            if tref_ratio > ring_ratio:
                print(f"    -> Trefoil stabilized MORE than ring. Topology matters!")
            else:
                print(f"    -> Ring stabilized MORE than trefoil.")
        else:
            print(f"    -> No significant topology dependence.")

    # Save
    save_data = {}
    for topo_name in all_results:
        save_data[topo_name] = all_results[topo_name]
    with open(RESULTS / "experiment_variable_viscosity_data.json", 'w') as f:
        json.dump(save_data, f, indent=2)

    print("="*70)


if __name__ == "__main__":
    main()
