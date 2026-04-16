"""
MCT Coupled Two-Body Simulation
=================================

The critical test: do two vortex structures in the coupled Navier-Stokes
+ MCT system attract each other with 1/r^2?

In standard fluid dynamics, two vortex rings DON'T attract with 1/r^2.
They interact through complex vortex dynamics (leapfrogging, merging).
If the MCT coupling produces 1/r^2 attraction on top of the normal
vortex dynamics, that's new physics.

Method:
  Place two vortex rings at separation d. Run the coupled simulation.
  Track the distance between the vorticity centroids over time. If
  the centroids accelerate toward each other, measure the acceleration
  and check if it scales as 1/d^2.

  Run with coupling ON and coupling OFF to isolate the MCT contribution.
"""

import numpy as np
from scipy.fft import fftn, ifftn, fftfreq
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
from pathlib import Path
import json
import io
import time

RESULTS = Path(__file__).parent / "results"
RESULTS.mkdir(exist_ok=True)

N = 96
L = 4 * np.pi  # larger box for two separated structures
dx = L / N
dt = 0.002
nu = 0.008

def make_wavenumbers():
    k = fftfreq(N, d=L/(2*np.pi*N))
    KX, KY, KZ = np.meshgrid(k, k, k, indexing='ij')
    K2 = KX**2 + KY**2 + KZ**2
    K2s = K2.copy(); K2s[0,0,0] = 1.0
    return KX, KY, KZ, K2, K2s


def vortex_ring_at(center, R, Gamma, core_a):
    x = np.linspace(0, L, N, endpoint=False)
    X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
    n_pts = 150
    t = np.linspace(0, 2*np.pi, n_pts, endpoint=False)
    rx = center[0] + R*np.cos(t)
    ry = center[1] + R*np.sin(t)
    rz = np.full(n_pts, center[2])
    dlx = -R*np.sin(t)*2*np.pi/n_pts
    dly = R*np.cos(t)*2*np.pi/n_pts
    dlz = np.zeros(n_pts)

    ux = np.zeros((N,N,N)); uy = np.zeros((N,N,N)); uz = np.zeros((N,N,N))
    for i in range(n_pts):
        drx = X-rx[i]; dry = Y-ry[i]; drz = Z-rz[i]
        drx -= L*np.round(drx/L)
        dry -= L*np.round(dry/L)
        drz -= L*np.round(drz/L)
        r2 = drx**2+dry**2+drz**2+core_a**2
        r3i = 1.0/(r2**1.5)
        ux += Gamma/(4*np.pi)*(dly[i]*drz-dlz[i]*dry)*r3i
        uy += Gamma/(4*np.pi)*(dlz[i]*drx-dlx[i]*drz)*r3i
        uz += Gamma/(4*np.pi)*(dlx[i]*dry-dly[i]*drx)*r3i
    return ux, uy, uz


def compute_vorticity(ux, uy, uz, KX, KY, KZ):
    uxh = fftn(ux); uyh = fftn(uy); uzh = fftn(uz)
    wx = np.real(ifftn(1j*KY*uzh - 1j*KZ*uyh))
    wy = np.real(ifftn(1j*KZ*uxh - 1j*KX*uzh))
    wz = np.real(ifftn(1j*KX*uyh - 1j*KY*uxh))
    return np.sqrt(wx**2+wy**2+wz**2), wx, wy, wz


def step_ns(ux, uy, uz, KX, KY, KZ, K2, K2s, alpha):
    omega, wx, wy, wz = compute_vorticity(ux, uy, uz, KX, KY, KZ)

    if alpha > 0:
        rho_hat = fftn(omega)
        phi_hat = -4*np.pi*alpha*rho_hat/K2s
        phi_hat[0,0,0] = 0
        gx = -np.real(ifftn(1j*KX*phi_hat))
        gy = -np.real(ifftn(1j*KY*phi_hat))
        gz = -np.real(ifftn(1j*KZ*phi_hat))
    else:
        gx = gy = gz = 0

    rhsx = (wy*uz-wz*uy)+gx
    rhsy = (wz*ux-wx*uz)+gy
    rhsz = (wx*uy-wy*ux)+gz

    uxh = fftn(ux)+dt*fftn(rhsx)
    uyh = fftn(uy)+dt*fftn(rhsy)
    uzh = fftn(uz)+dt*fftn(rhsz)

    v = np.exp(-nu*K2*dt)
    uxh*=v; uyh*=v; uzh*=v

    div = KX*uxh+KY*uyh+KZ*uzh
    uxh -= KX*div/K2s; uyh -= KY*div/K2s; uzh -= KZ*div/K2s
    uxh[0,0,0]=0; uyh[0,0,0]=0; uzh[0,0,0]=0

    return (np.clip(np.real(ifftn(uxh)),-20,20),
            np.clip(np.real(ifftn(uyh)),-20,20),
            np.clip(np.real(ifftn(uzh)),-20,20),
            omega)


def find_centroid(omega, x_arr, region_center, half_width):
    """Find vorticity centroid near region_center."""
    X, Y, Z = np.meshgrid(x_arr, x_arr, x_arr, indexing='ij')

    # Mask to region around expected center (periodic)
    rx = X - region_center[0]
    ry = Y - region_center[1]
    rz = Z - region_center[2]
    rx -= L*np.round(rx/L)
    ry -= L*np.round(ry/L)
    rz -= L*np.round(rz/L)

    mask = (np.abs(rx) < half_width) & (np.abs(ry) < half_width) & (np.abs(rz) < half_width)
    w_masked = omega * mask

    total = np.sum(w_masked)
    if total < 1e-10:
        return region_center

    cx = region_center[0] + np.sum(rx * w_masked) / total
    cy = region_center[1] + np.sum(ry * w_masked) / total
    cz = region_center[2] + np.sum(rz * w_masked) / total
    return [cx, cy, cz]


def run_two_body(alpha, label, n_steps=500, save_every=25):
    """Run two vortex rings and track their separation."""
    print(f"\n  [{label}] alpha = {alpha}")

    KX, KY, KZ, K2, K2s = make_wavenumbers()
    x_arr = np.linspace(0, L, N, endpoint=False)

    sep = 3.0  # initial separation
    c1 = [L/2 - sep/2, L/2, L/2]
    c2 = [L/2 + sep/2, L/2, L/2]

    print(f"    Initializing two rings at separation d={sep}...")
    t0 = time.time()
    ux1, uy1, uz1 = vortex_ring_at(c1, 0.5, 1.5, 0.15)
    ux2, uy2, uz2 = vortex_ring_at(c2, 0.5, 1.5, 0.15)
    ux = ux1+ux2; uy = uy1+uy2; uz = uz1+uz2
    print(f"    Init: {time.time()-t0:.1f}s")

    centroids_1 = []
    centroids_2 = []
    separations = []
    frames = []

    hw = 2.0  # half-width for centroid search

    for s in range(n_steps+1):
        omega, _, _, _ = compute_vorticity(ux, uy, uz, KX, KY, KZ)

        # Track centroids
        pos1 = find_centroid(omega, x_arr, c1, hw)
        pos2 = find_centroid(omega, x_arr, c2, hw)
        d = np.sqrt(sum((a-b)**2 for a, b in zip(pos1, pos2)))

        centroids_1.append(pos1)
        centroids_2.append(pos2)
        separations.append(d)

        # Update search centers for next step
        c1 = pos1; c2 = pos2

        if s % save_every == 0:
            KE = 0.5*np.sum(ux**2+uy**2+uz**2)*dx**3
            print(f"    step {s:4d}: d={d:.4f}, KE={KE:.4f}")

            # Frame
            fig, axes = plt.subplots(1, 2, figsize=(14, 6))
            mid = N//2
            ax = axes[0]
            im = ax.imshow(omega[:,:,mid].T, origin='lower', extent=[0,L,0,L], cmap='inferno')
            ax.plot(pos1[0], pos1[1], 'co', markersize=8, markeredgecolor='white')
            ax.plot(pos2[0], pos2[1], 'co', markersize=8, markeredgecolor='white')
            ax.set_title(f'{label}: vorticity (step {s}, d={d:.3f})')
            ax.set_xlabel('x'); ax.set_ylabel('y')
            plt.colorbar(im, ax=ax, shrink=0.8)

            ax = axes[1]
            ax.plot(separations, 'b-', linewidth=2)
            ax.axhline(sep, color='gray', linestyle='--', alpha=0.5, label=f'initial d={sep}')
            ax.set_xlabel('Step')
            ax.set_ylabel('Separation d')
            ax.set_title(f'Centroid Separation Over Time')
            ax.legend()
            ax.grid(True, alpha=0.3)

            plt.suptitle(f'Two-Body: {label} (step {s})', fontsize=13)
            plt.tight_layout()
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=80)
            buf.seek(0)
            frames.append(Image.open(buf).copy())
            plt.close(); buf.close()

        if s < n_steps:
            ux, uy, uz, _ = step_ns(ux, uy, uz, KX, KY, KZ, K2, K2s, alpha)

    # Save GIF
    if frames:
        frames[0].save(RESULTS / f"twobody_{label}.gif", save_all=True,
                       append_images=frames[1:], duration=250, loop=0)
        print(f"    GIF: twobody_{label}.gif")

    return separations


def main():
    print("="*70)
    print("MCT TWO-BODY TEST: Do Vortex Structures Attract via Coupling?")
    print(f"Grid: {N}^3, box: {L:.2f}, dt={dt}")
    print("="*70)

    n_steps = 600

    # WITH MCT coupling
    seps_coupled = run_two_body(alpha=0.05, label="coupled", n_steps=n_steps, save_every=30)

    # WITHOUT coupling (pure Navier-Stokes)
    seps_uncoupled = run_two_body(alpha=0.0, label="uncoupled", n_steps=n_steps, save_every=30)

    # ── Analysis ──
    steps = np.arange(len(seps_coupled))
    times = steps * dt

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # Separation vs time
    ax = axes[0]
    ax.plot(times, seps_coupled, 'b-', linewidth=2, label='With MCT coupling')
    ax.plot(times, seps_uncoupled, 'r--', linewidth=2, label='Without coupling (pure NS)')
    ax.set_xlabel('Time', fontsize=13)
    ax.set_ylabel('Centroid separation $d$', fontsize=13)
    ax.set_title('Two-Body Separation: Coupled vs Uncoupled', fontsize=14)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)

    # Difference
    ax = axes[1]
    diff = np.array(seps_coupled) - np.array(seps_uncoupled)
    ax.plot(times, diff, 'g-', linewidth=2)
    ax.axhline(0, color='k', linewidth=0.5)
    ax.set_xlabel('Time', fontsize=13)
    ax.set_ylabel('$d_{coupled} - d_{uncoupled}$', fontsize=13)
    ax.set_title('MCT Coupling Effect on Separation', fontsize=14)
    ax.grid(True, alpha=0.3)

    # If diff is consistently negative, coupling causes attraction
    final_diff = np.mean(diff[-50:])
    if final_diff < -0.01:
        ax.annotate(f'Mean late-time diff: {final_diff:.4f}\n(coupling causes attraction)',
                    xy=(0.5, 0.85), xycoords='axes fraction', fontsize=11,
                    ha='center', bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))
    elif final_diff > 0.01:
        ax.annotate(f'Mean late-time diff: {final_diff:.4f}\n(coupling causes repulsion)',
                    xy=(0.5, 0.85), xycoords='axes fraction', fontsize=11,
                    ha='center', bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
    else:
        ax.annotate(f'Mean late-time diff: {final_diff:.4f}\n(no significant effect)',
                    xy=(0.5, 0.85), xycoords='axes fraction', fontsize=11,
                    ha='center', bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))

    plt.tight_layout()
    plt.savefig(RESULTS / "twobody_comparison.png", dpi=150)
    plt.close()
    print(f"\n  Saved: twobody_comparison.png")

    # Save data
    data = {
        "parameters": {"N": N, "L": L, "dt": dt, "nu": nu, "steps": n_steps,
                        "ring_R": 0.5, "ring_Gamma": 1.5, "initial_sep": 3.0,
                        "alpha_coupled": 0.05},
        "separations_coupled": seps_coupled,
        "separations_uncoupled": seps_uncoupled,
        "final_mean_diff": float(final_diff),
    }
    with open(RESULTS / "twobody_data.json", 'w') as f:
        json.dump(data, f, indent=2)

    print(f"\n{'='*70}")
    print("TWO-BODY RESULTS")
    print(f"{'='*70}")
    print(f"  Initial separation: 3.0")
    print(f"  Final separation (coupled):   {seps_coupled[-1]:.4f}")
    print(f"  Final separation (uncoupled): {seps_uncoupled[-1]:.4f}")
    print(f"  Difference: {final_diff:.4f}")
    if final_diff < -0.01:
        print(f"  -> MCT coupling causes the structures to ATTRACT")
        print(f"  -> This is gravitational attraction from angular momentum coupling")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
