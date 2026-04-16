"""
Showcase: Topology = Mass
==========================

Six knot topologies, identical physics, different masses.
Side-by-side 2x3 grid showing vorticity and running mass counter.
The viewer watches mass emerge from geometry in real time.

GPU-accelerated: Taichi (Biot-Savart) + CuPy (FFT spectral solver).
"""

import taichi as ti
import numpy as np
import cupy as cp
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from PIL import Image
from pathlib import Path
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
alpha = 0.05
N_STEPS = 300
SAVE_EVERY = 30

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


# ── Topology curves ──
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

def make_torus_knot(center, scale=1.0, p=2, q=5, n_pts=300):
    t = np.linspace(0, 2*np.pi, n_pts, endpoint=False)
    rm = scale*0.6; rn = scale*0.3
    return (center[0]+(rm+rn*np.cos(q*t))*np.cos(p*t),
            center[1]+(rm+rn*np.cos(q*t))*np.sin(p*t),
            center[2]+rn*np.sin(q*t))

def make_hopf_link(center, scale=1.0, n_pts=150):
    t = np.linspace(0, 2*np.pi, n_pts, endpoint=False)
    R = scale*0.5
    x1=center[0]+R*np.cos(t); y1=center[1]+R*np.sin(t); z1=np.full(n_pts, center[2])
    x2=center[0]+R/2+R*np.cos(t); y2=np.full(n_pts, center[1]); z2=center[2]+R*np.sin(t)
    return np.concatenate([x1,x2]), np.concatenate([y1,y2]), np.concatenate([z1,z2])


def init_topology(curve_func, center, Gamma=2.0, core_a=0.2):
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

    def step_and_measure(self, ux, uy, uz):
        uxh = cp.fft.fftn(ux); uyh = cp.fft.fftn(uy); uzh = cp.fft.fftn(uz)
        wx = cp.real(cp.fft.ifftn(1j*self.KY*uzh - 1j*self.KZ*uyh))
        wy = cp.real(cp.fft.ifftn(1j*self.KZ*uxh - 1j*self.KX*uzh))
        wz = cp.real(cp.fft.ifftn(1j*self.KX*uyh - 1j*self.KY*uxh))
        omega = cp.sqrt(wx**2 + wy**2 + wz**2)

        rh = cp.fft.fftn(omega)
        ph = -4*cp.pi*alpha * rh / self.K2s; ph[0,0,0] = 0
        phi = cp.real(cp.fft.ifftn(ph))

        gx = -cp.real(cp.fft.ifftn(1j*self.KX*ph))
        gy = -cp.real(cp.fft.ifftn(1j*self.KY*ph))
        gz = -cp.real(cp.fft.ifftn(1j*self.KZ*ph))

        rhsx = (wy*uz-wz*uy)+gx; rhsy = (wz*ux-wx*uz)+gy; rhsz = (wx*uy-wy*ux)+gz
        uxh2 = cp.fft.fftn(ux)+dt*cp.fft.fftn(rhsx)
        uyh2 = cp.fft.fftn(uy)+dt*cp.fft.fftn(rhsy)
        uzh2 = cp.fft.fftn(uz)+dt*cp.fft.fftn(rhsz)
        uxh2 *= self.visc; uyh2 *= self.visc; uzh2 *= self.visc
        div = self.KX*uxh2+self.KY*uyh2+self.KZ*uzh2
        uxh2 -= self.KX*div/self.K2s; uyh2 -= self.KY*div/self.K2s; uzh2 -= self.KZ*div/self.K2s
        uxh2[0,0,0]=0; uyh2[0,0,0]=0; uzh2[0,0,0]=0

        ux_new = cp.clip(cp.real(cp.fft.ifftn(uxh2)), -20, 20)
        uy_new = cp.clip(cp.real(cp.fft.ifftn(uyh2)), -20, 20)
        uz_new = cp.clip(cp.real(cp.fft.ifftn(uzh2)), -20, 20)
        return ux_new, uy_new, uz_new, cp.asnumpy(omega), cp.asnumpy(phi)


def radial_profile(phi_cpu, center):
    x = np.linspace(0, L, N, endpoint=False)
    X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
    rx = X-center[0]; ry = Y-center[1]; rz = Z-center[2]
    rx -= L*np.round(rx/L); ry -= L*np.round(ry/L); rz -= L*np.round(rz/L)
    R = np.sqrt(rx**2+ry**2+rz**2)
    edges = np.linspace(dx, L/3, N//3+1)
    ctrs = 0.5*(edges[:-1]+edges[1:])
    avg = np.zeros(len(ctrs))
    Rf = R.ravel(); pf = phi_cpu.ravel()
    for i in range(len(ctrs)):
        m = (Rf >= edges[i]) & (Rf < edges[i+1])
        if np.any(m): avg[i] = np.mean(pf[m])
    v = avg != 0
    return ctrs[v], avg[v]


def fit_power(r, phi):
    m = (r >= 0.4) & (r <= L/3) & (np.abs(phi) > 1e-30)
    if np.sum(m) < 5: return 0, 0
    lr = np.log(r[m]); lp = np.log(np.abs(phi[m]))
    c = np.polyfit(lr, lp, 1)
    return c[0], np.exp(c[1])


def run_all_topologies():
    """Run all 6 topologies and collect snapshots at each save step."""
    center = [L/2, L/2, L/2]

    topos = [
        ("Ring",         lambda c: make_ring(c)),
        ("Hopf Link",    lambda c: make_hopf_link(c)),
        ("Trefoil",      lambda c: make_trefoil(c)),
        ("T(2,5)",       lambda c: make_torus_knot(c, p=2, q=5)),
        ("T(2,7)",       lambda c: make_torus_knot(c, p=2, q=7)),
        ("Figure-Eight", lambda c: make_figure_eight(c)),
    ]

    # Colors for each topology
    colors = ['#ff6600', '#22aa44', '#4444ff', '#aa22aa', '#cc8800', '#cc2222']

    all_data = {}  # name -> list of (step, omega_slice, phi_slice, GM, n_exp)

    solver = Solver()

    for idx, (name, curve_func) in enumerate(topos):
        print(f"\n  [{name}]", end="", flush=True)
        ux, uy, uz = init_topology(curve_func, center)
        ux_g = cp.asarray(ux); uy_g = cp.asarray(uy); uz_g = cp.asarray(uz)

        snapshots = []
        t0 = time.time()

        for s in range(N_STEPS + 1):
            if s % SAVE_EVERY == 0:
                # Compute vorticity + potential for snapshot
                uxh = cp.fft.fftn(ux_g); uyh = cp.fft.fftn(uy_g); uzh = cp.fft.fftn(uz_g)
                wx = cp.real(cp.fft.ifftn(1j*solver.KY*uzh - 1j*solver.KZ*uyh))
                wy = cp.real(cp.fft.ifftn(1j*solver.KZ*uxh - 1j*solver.KX*uzh))
                wz = cp.real(cp.fft.ifftn(1j*solver.KX*uyh - 1j*solver.KY*uxh))
                omega_g = cp.sqrt(wx**2+wy**2+wz**2)
                rh = cp.fft.fftn(omega_g)
                ph = -4*cp.pi*alpha*rh/solver.K2s; ph[0,0,0] = 0
                phi_g = cp.real(cp.fft.ifftn(ph))

                omega_cpu = cp.asnumpy(omega_g)
                phi_cpu = cp.asnumpy(phi_g)

                r, phi_avg = radial_profile(phi_cpu, center)
                n_exp, GM = fit_power(r, phi_avg)

                mid = N//2
                snapshots.append({
                    'step': s,
                    'omega_slice': omega_cpu[:,:,mid].copy(),
                    'phi_slice': phi_cpu[:,:,mid].copy(),
                    'GM': GM,
                    'n_exp': n_exp,
                })
                print(f" {s}", end="", flush=True)

            if s < N_STEPS:
                ux_g, uy_g, uz_g, _, _ = solver.step_and_measure(ux_g, uy_g, uz_g)

        elapsed = time.time() - t0
        print(f" ({elapsed:.1f}s)")
        all_data[name] = snapshots

    return all_data, topos, colors


def render_comparison_frame(all_data, topos, colors, frame_idx):
    """Render a 2x3 grid for one time step."""
    fig = plt.figure(figsize=(21, 13))
    gs = GridSpec(3, 6, figure=fig, hspace=0.35, wspace=0.3,
                  height_ratios=[1, 1, 0.08])

    # Get the step number from the first topology
    first_name = topos[0][0]
    step = all_data[first_name][frame_idx]['step']

    # Collect all GMs for the bar at the bottom
    gm_values = []
    names_short = []

    for idx, (name, _) in enumerate(topos):
        row = idx // 3
        col = idx % 3

        snap = all_data[name][frame_idx]
        omega_slice = snap['omega_slice']
        phi_slice = snap['phi_slice']
        GM = snap['GM']
        n_exp = snap['n_exp']

        gm_values.append(GM)
        names_short.append(name)

        # Vorticity + potential overlay
        ax = fig.add_subplot(gs[row, col*2])
        vmax_o = max(np.max(omega_slice)*0.8, 0.1)
        ax.imshow(omega_slice.T, origin='lower', extent=[0,L,0,L],
                 cmap='inferno', vmin=0, vmax=vmax_o)
        ax.set_title(f'{name}', fontsize=14, fontweight='bold', color=colors[idx])
        ax.set_xticks([]); ax.set_yticks([])

        # Mass counter overlay
        ax.text(0.05, 0.92, f'GM = {GM:.3f}', transform=ax.transAxes,
                fontsize=13, fontweight='bold', color='white',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.7))
        ax.text(0.05, 0.78, f'n = {n_exp:.2f}', transform=ax.transAxes,
                fontsize=10, color='#aaaaaa',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='black', alpha=0.5))

        # Potential
        ax2 = fig.add_subplot(gs[row, col*2+1])
        vmax_p = max(np.max(np.abs(phi_slice))*0.7, 1e-6)
        ax2.imshow(phi_slice.T, origin='lower', extent=[0,L,0,L],
                  cmap='RdBu_r', vmin=-vmax_p, vmax=vmax_p)
        ax2.set_title(f'Potential', fontsize=11, color='#666666')
        ax2.set_xticks([]); ax2.set_yticks([])

    # Bottom: mass comparison bar
    ax_bar = fig.add_subplot(gs[2, :])
    if max(gm_values) > 0:
        ring_GM = gm_values[0]
        ratios = [gm/ring_GM if ring_GM > 0 else 0 for gm in gm_values]
        bars = ax_bar.barh(range(len(topos)), ratios, color=colors, height=0.7, alpha=0.85)
        ax_bar.set_yticks(range(len(topos)))
        ax_bar.set_yticklabels(names_short, fontsize=11, fontweight='bold')
        ax_bar.set_xlabel('Effective Mass (ring = 1.0)', fontsize=12)
        for i, (r, n) in enumerate(zip(ratios, names_short)):
            ax_bar.text(r + 0.02, i, f'{r:.2f}', va='center', fontsize=11, fontweight='bold')
        ax_bar.set_xlim(0, max(ratios)*1.15 if max(ratios) > 0 else 1)
    ax_bar.grid(True, alpha=0.2, axis='x')

    fig.suptitle(
        f'Same Physics, Different Topology = Different Mass  (step {step}/{N_STEPS})',
        fontsize=17, fontweight='bold', y=0.98
    )
    fig.text(0.5, 0.005,
             'All simulations: identical circulation, viscosity, grid, coupling. Only the knot shape differs.',
             ha='center', fontsize=12, style='italic', color='#555555')

    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=90, facecolor='white', bbox_inches='tight')
    buf.seek(0)
    img = Image.open(buf).copy()
    plt.close(fig)
    buf.close()
    return img


def main():
    print("="*70)
    print("SHOWCASE: Topology = Mass (6 topologies side-by-side)")
    print(f"Grid: {N}^3, GPU, {N_STEPS} steps each")
    print("="*70)

    t0 = time.time()
    all_data, topos, colors = run_all_topologies()
    print(f"\n  All topologies computed in {time.time()-t0:.1f}s")

    # Render frames
    n_frames = len(all_data[topos[0][0]])
    print(f"  Rendering {n_frames} frames...")

    frames = []
    for i in range(n_frames):
        frame = render_comparison_frame(all_data, topos, colors, i)
        frames.append(frame)
        print(f"    Frame {i+1}/{n_frames}")

    # Save GIF
    frames[0].save(RESULTS / "showcase_topology_is_mass.gif",
                   save_all=True, append_images=frames[1:],
                   duration=500, loop=0, optimize=True)

    # Save key frames
    frames[0].save(RESULTS / "showcase_topology_start.png")
    frames[-1].save(RESULTS / "showcase_topology_final.png")

    print(f"  Saved: showcase_topology_is_mass.gif ({n_frames} frames)")
    print("="*70)


if __name__ == "__main__":
    main()
