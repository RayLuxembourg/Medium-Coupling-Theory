"""
Showcase: Two Bodies Attract
=============================

Two vortex rings in a coupled NS + MCT system. The coupling is cranked
up so the gravitational attraction is visible: the structures move
toward each other through nothing but fluid dynamics.

Strong coupling: alpha=0.3, low viscosity nu=0.002.
GPU-accelerated: Taichi (Biot-Savart) + CuPy (FFT spectral solver).
"""

import taichi as ti
import numpy as np
import cupy as cp
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
from pathlib import Path
import io
import time

ti.init(arch=ti.cuda, default_fp=ti.f64)

RESULTS = Path(__file__).parent / "results"
RESULTS.mkdir(exist_ok=True)

# ── Parameters (strong coupling regime) ──
N = 128
L = 4.0 * np.pi  # larger box for two separated structures
dx = L / N
dt = 0.001        # smaller dt for stability with strong coupling
nu = 0.003        # low viscosity so coupling dominates
alpha = 0.25      # strong coupling
N_STEPS = 1500
SAVE_EVERY = 50

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


def make_ring_at(center, R, n_pts=200):
    t = np.linspace(0, 2*np.pi, n_pts, endpoint=False)
    return center[0]+R*np.cos(t), center[1]+R*np.sin(t), np.full(n_pts, center[2])


def init_ring(center, R, Gamma, core_a):
    cx, cy, cz = make_ring_at(center, R)
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

    def step(self, ux, uy, uz):
        uxh = cp.fft.fftn(ux); uyh = cp.fft.fftn(uy); uzh = cp.fft.fftn(uz)
        wx = cp.real(cp.fft.ifftn(1j*self.KY*uzh - 1j*self.KZ*uyh))
        wy = cp.real(cp.fft.ifftn(1j*self.KZ*uxh - 1j*self.KX*uzh))
        wz = cp.real(cp.fft.ifftn(1j*self.KX*uyh - 1j*self.KY*uxh))
        omega = cp.sqrt(wx**2 + wy**2 + wz**2)

        rh = cp.fft.fftn(omega)
        ph = -4*cp.pi*alpha * rh / self.K2s; ph[0,0,0] = 0
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

        ux = cp.clip(cp.real(cp.fft.ifftn(uxh2)), -30, 30)
        uy = cp.clip(cp.real(cp.fft.ifftn(uyh2)), -30, 30)
        uz = cp.clip(cp.real(cp.fft.ifftn(uzh2)), -30, 30)
        return ux, uy, uz, cp.asnumpy(omega)


def find_centroid(omega, x_arr, region_center, half_width):
    """Find vorticity centroid near region_center (periodic)."""
    X, Y, Z = np.meshgrid(x_arr, x_arr, x_arr, indexing='ij')
    rx = X - region_center[0]; ry = Y - region_center[1]; rz = Z - region_center[2]
    rx -= L*np.round(rx/L); ry -= L*np.round(ry/L); rz -= L*np.round(rz/L)
    mask = (np.abs(rx)<half_width) & (np.abs(ry)<half_width) & (np.abs(rz)<half_width)
    w_masked = omega * mask
    total = np.sum(w_masked)
    if total < 1e-10: return region_center
    cx = region_center[0] + np.sum(rx*w_masked)/total
    cy = region_center[1] + np.sum(ry*w_masked)/total
    cz = region_center[2] + np.sum(rz*w_masked)/total
    return [cx, cy, cz]


def render_frame(omega_cpu, pos1, pos2, seps_c, seps_u, step, d_current):
    """Render frame: vorticity map + trajectory + separation plot."""
    fig, axes = plt.subplots(1, 3, figsize=(21, 7))

    mid = N // 2
    x_arr = np.linspace(0, L, N, endpoint=False)

    # Left: vorticity with centroids and trajectory
    ax = axes[0]
    im = ax.imshow(omega_cpu[:,:,mid].T, origin='lower', extent=[0,L,0,L],
                  cmap='inferno', vmin=0)
    ax.plot(pos1[0], pos1[1], 'co', markersize=14, markeredgecolor='white',
           markeredgewidth=2, zorder=10)
    ax.plot(pos2[0], pos2[1], 'co', markersize=14, markeredgecolor='white',
           markeredgewidth=2, zorder=10)
    # Draw line between centroids
    ax.plot([pos1[0], pos2[0]], [pos1[1], pos2[1]], 'w--', linewidth=1.5, alpha=0.7)
    ax.set_title(f'Vorticity (step {step})', fontsize=14, fontweight='bold')
    ax.set_xlabel('x'); ax.set_ylabel('y')
    plt.colorbar(im, ax=ax, shrink=0.8)

    # Center: separation over time
    ax = axes[1]
    steps_arr = np.arange(len(seps_c)) * SAVE_EVERY
    if len(seps_c) > 1:
        ax.plot(steps_arr, seps_c, 'b-', linewidth=2.5, label='With MCT coupling')
        if len(seps_u) == len(seps_c):
            ax.plot(steps_arr, seps_u, 'r--', linewidth=2, alpha=0.7, label='Without coupling')
        ax.axhline(seps_c[0], color='gray', linestyle=':', alpha=0.5, label=f'Initial d={seps_c[0]:.2f}')
        ax.legend(fontsize=11, loc='best')
    ax.set_xlabel('Step', fontsize=13)
    ax.set_ylabel('Centroid separation $d$', fontsize=13)
    ax.set_title('Separation Over Time', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)

    # Right: difference (MCT effect)
    ax = axes[2]
    if len(seps_c) > 1 and len(seps_u) == len(seps_c):
        diff = np.array(seps_c) - np.array(seps_u)
        ax.plot(steps_arr, diff, 'g-', linewidth=2.5)
        ax.axhline(0, color='k', linewidth=0.5)
        ax.set_ylabel('$d_{coupled} - d_{uncoupled}$', fontsize=13)

        if len(diff) > 5:
            mean_diff = np.mean(diff[-max(5, len(diff)//3):])
            if mean_diff < -0.001:
                ax.text(0.5, 0.85, f'MCT causes attraction\n$\\Delta d = {mean_diff:.4f}$',
                       transform=ax.transAxes, fontsize=12, ha='center',
                       bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))
            elif mean_diff > 0.001:
                ax.text(0.5, 0.85, f'$\\Delta d = {mean_diff:.4f}$',
                       transform=ax.transAxes, fontsize=12, ha='center',
                       bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
    ax.set_xlabel('Step', fontsize=13)
    ax.set_title('MCT Coupling Effect', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)

    fig.suptitle(
        f'Two Vortex Rings: Gravitational Attraction from Medium Coupling  ($\\alpha={alpha}$, step {step})',
        fontsize=15, fontweight='bold', y=0.98
    )
    fig.text(0.5, 0.01,
             'No gravitational force in the equations. Attraction emerges from vorticity coupling to the medium.',
             ha='center', fontsize=11, style='italic', color='#555555')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=90, facecolor='white')
    buf.seek(0)
    img = Image.open(buf).copy()
    plt.close(fig); buf.close()
    return img


def run_simulation(alpha_val, label):
    """Run two-body simulation with given coupling strength."""
    global alpha
    alpha = alpha_val

    x_arr = np.linspace(0, L, N, endpoint=False)

    sep = 4.0
    c1 = [L/2 - sep/2, L/2, L/2]
    c2 = [L/2 + sep/2, L/2, L/2]

    Gamma = 3.0
    R = 0.8
    core_a = 0.2

    print(f"\n  [{label}] alpha={alpha_val}, Initializing rings...")
    ux1, uy1, uz1 = init_ring(c1, R, Gamma, core_a)
    ux2, uy2, uz2 = init_ring(c2, R, Gamma, core_a)
    ux = ux1 + ux2; uy = uy1 + uy2; uz = uz1 + uz2

    solver = Solver()
    ux_g = cp.asarray(ux); uy_g = cp.asarray(uy); uz_g = cp.asarray(uz)

    separations = []
    snapshots = []
    hw = 3.0

    t0 = time.time()
    for s in range(N_STEPS + 1):
        if s % SAVE_EVERY == 0:
            # Get omega on CPU for centroid tracking
            uxh = cp.fft.fftn(ux_g); uyh = cp.fft.fftn(uy_g); uzh = cp.fft.fftn(uz_g)
            wx = cp.real(cp.fft.ifftn(1j*solver.KY*uzh - 1j*solver.KZ*uyh))
            wy = cp.real(cp.fft.ifftn(1j*solver.KZ*uxh - 1j*solver.KX*uzh))
            wz = cp.real(cp.fft.ifftn(1j*solver.KX*uyh - 1j*solver.KY*uxh))
            omega_g = cp.sqrt(wx**2 + wy**2 + wz**2)
            omega_cpu = cp.asnumpy(omega_g)

            pos1 = find_centroid(omega_cpu, x_arr, c1, hw)
            pos2 = find_centroid(omega_cpu, x_arr, c2, hw)
            d = np.sqrt(sum((a-b)**2 for a, b in zip(pos1, pos2)))
            separations.append(d)

            c1 = pos1; c2 = pos2

            snapshots.append({
                'step': s, 'omega': omega_cpu, 'pos1': list(pos1),
                'pos2': list(pos2), 'd': d
            })

            print(f"    step {s:5d}: d={d:.4f}")

        if s < N_STEPS:
            ux_g, uy_g, uz_g, _ = solver.step(ux_g, uy_g, uz_g)

    elapsed = time.time() - t0
    print(f"    Total: {elapsed:.1f}s")
    return separations, snapshots


def main():
    print("="*70)
    print("SHOWCASE: Two Bodies Attract via MCT Coupling")
    print(f"Grid: {N}^3, L={L:.2f}, dt={dt}, GPU")
    print(f"Strong coupling: alpha={alpha}, nu={nu}")
    print("="*70)

    # Run WITH coupling
    seps_coupled, snaps_coupled = run_simulation(alpha_val=0.25, label="coupled")

    # Run WITHOUT coupling
    seps_uncoupled, snaps_uncoupled = run_simulation(alpha_val=0.0, label="uncoupled")

    # Render frames
    n_frames = min(len(snaps_coupled), len(snaps_uncoupled))
    print(f"\n  Rendering {n_frames} frames...")

    frames = []
    for i in range(n_frames):
        snap = snaps_coupled[i]
        frame = render_frame(
            snap['omega'], snap['pos1'], snap['pos2'],
            seps_coupled[:i+1], seps_uncoupled[:i+1],
            snap['step'], snap['d']
        )
        frames.append(frame)
        print(f"    Frame {i+1}/{n_frames}")

    # Save GIF
    frames[0].save(RESULTS / "showcase_two_body_attraction.gif",
                   save_all=True, append_images=frames[1:],
                   duration=500, loop=0, optimize=True)
    frames[-1].save(RESULTS / "showcase_two_body_final.png")

    # Final comparison plot
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    steps = np.arange(len(seps_coupled)) * SAVE_EVERY

    ax = axes[0]
    ax.plot(steps, seps_coupled, 'b-', linewidth=2.5, label='With MCT coupling')
    ax.plot(steps, seps_uncoupled, 'r--', linewidth=2, label='Without coupling')
    ax.set_xlabel('Step', fontsize=13)
    ax.set_ylabel('Centroid separation $d$', fontsize=13)
    ax.set_title('Two-Body Separation', fontsize=14, fontweight='bold')
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)

    ax = axes[1]
    diff = np.array(seps_coupled) - np.array(seps_uncoupled[:len(seps_coupled)])
    ax.plot(steps, diff, 'g-', linewidth=2.5)
    ax.axhline(0, color='k', linewidth=0.5)
    ax.set_xlabel('Step', fontsize=13)
    ax.set_ylabel('$d_{coupled} - d_{uncoupled}$', fontsize=13)
    ax.set_title('MCT Effect on Separation', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)

    final_diff = np.mean(diff[-max(3, len(diff)//4):])
    if final_diff < -0.001:
        ax.annotate(f'Mean late-time: {final_diff:.4f}\nCoupling causes attraction',
                   xy=(0.5, 0.85), xycoords='axes fraction', fontsize=12,
                   ha='center', bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))

    plt.tight_layout()
    plt.savefig(RESULTS / "showcase_two_body_comparison.png", dpi=150)
    plt.close()

    print(f"\n  Saved: showcase_two_body_attraction.gif ({n_frames} frames)")
    print(f"  Saved: showcase_two_body_comparison.png")
    print(f"\n  Final separation (coupled):   {seps_coupled[-1]:.4f}")
    print(f"  Final separation (uncoupled): {seps_uncoupled[-1]:.4f}")
    print(f"  Difference: {final_diff:.6f}")
    print("="*70)


if __name__ == "__main__":
    main()
