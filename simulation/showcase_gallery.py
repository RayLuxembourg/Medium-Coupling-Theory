"""
Showcase: 3D Knot Gallery
==========================

Publication-quality 3D renders of each knot topology with their
gravitational potential wells. Uses marching cubes for isosurfaces.
"""

import taichi as ti
import numpy as np
import cupy as cp
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from skimage.measure import marching_cubes
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


def compute_fields(curve_func, center, Gamma=2.0, core_a=0.2, n_steps=150):
    """Initialize and evolve for n_steps, return final vorticity and potential."""
    cx, cy, cz = curve_func(center)
    n = len(cx)
    dlx = np.roll(cx,-1)-cx; dly = np.roll(cy,-1)-cy; dlz = np.roll(cz,-1)-cz
    pad = lambda a: np.pad(a, (0, max_pts-n))
    fil_x.from_numpy(pad(cx)); fil_y.from_numpy(pad(cy)); fil_z.from_numpy(pad(cz))
    fil_dlx.from_numpy(pad(dlx)); fil_dly.from_numpy(pad(dly)); fil_dlz.from_numpy(pad(dlz))
    vel_x.fill(0); vel_y.fill(0); vel_z.fill(0)
    biot_savart_kernel(n, Gamma, core_a, L, N)
    ti.sync()

    ux_g = cp.asarray(vel_x.to_numpy())
    uy_g = cp.asarray(vel_y.to_numpy())
    uz_g = cp.asarray(vel_z.to_numpy())

    # Wavenumbers
    k = np.fft.fftfreq(N, d=L/(2*np.pi*N))
    KX, KY, KZ = np.meshgrid(k, k, k, indexing='ij')
    KX_g = cp.asarray(KX); KY_g = cp.asarray(KY); KZ_g = cp.asarray(KZ)
    K2_g = KX_g**2 + KY_g**2 + KZ_g**2
    K2s_g = K2_g.copy(); K2s_g[0,0,0] = 1.0
    visc = cp.exp(-nu * K2_g * dt)

    for s in range(n_steps):
        uxh = cp.fft.fftn(ux_g); uyh = cp.fft.fftn(uy_g); uzh = cp.fft.fftn(uz_g)
        wx = cp.real(cp.fft.ifftn(1j*KY_g*uzh - 1j*KZ_g*uyh))
        wy = cp.real(cp.fft.ifftn(1j*KZ_g*uxh - 1j*KX_g*uzh))
        wz = cp.real(cp.fft.ifftn(1j*KX_g*uyh - 1j*KY_g*uxh))
        omega = cp.sqrt(wx**2+wy**2+wz**2)
        rh = cp.fft.fftn(omega)
        ph = -4*cp.pi*alpha*rh/K2s_g; ph[0,0,0] = 0
        gx = -cp.real(cp.fft.ifftn(1j*KX_g*ph))
        gy = -cp.real(cp.fft.ifftn(1j*KY_g*ph))
        gz = -cp.real(cp.fft.ifftn(1j*KZ_g*ph))
        rhsx = (wy*uz_g-wz*uy_g)+gx
        rhsy = (wz*ux_g-wx*uz_g)+gy
        rhsz = (wx*uy_g-wy*ux_g)+gz
        uxh2 = cp.fft.fftn(ux_g)+dt*cp.fft.fftn(rhsx)
        uyh2 = cp.fft.fftn(uy_g)+dt*cp.fft.fftn(rhsy)
        uzh2 = cp.fft.fftn(uz_g)+dt*cp.fft.fftn(rhsz)
        uxh2 *= visc; uyh2 *= visc; uzh2 *= visc
        div = KX_g*uxh2+KY_g*uyh2+KZ_g*uzh2
        uxh2 -= KX_g*div/K2s_g; uyh2 -= KY_g*div/K2s_g; uzh2 -= KZ_g*div/K2s_g
        uxh2[0,0,0]=0; uyh2[0,0,0]=0; uzh2[0,0,0]=0
        ux_g = cp.clip(cp.real(cp.fft.ifftn(uxh2)),-20,20)
        uy_g = cp.clip(cp.real(cp.fft.ifftn(uyh2)),-20,20)
        uz_g = cp.clip(cp.real(cp.fft.ifftn(uzh2)),-20,20)

    # Final fields
    uxh = cp.fft.fftn(ux_g); uyh = cp.fft.fftn(uy_g); uzh = cp.fft.fftn(uz_g)
    wx = cp.real(cp.fft.ifftn(1j*KY_g*uzh - 1j*KZ_g*uyh))
    wy = cp.real(cp.fft.ifftn(1j*KZ_g*uxh - 1j*KX_g*uzh))
    wz = cp.real(cp.fft.ifftn(1j*KX_g*uyh - 1j*KY_g*uxh))
    omega = cp.sqrt(wx**2+wy**2+wz**2)
    rh = cp.fft.fftn(omega)
    ph = -4*cp.pi*alpha*rh/K2s_g; ph[0,0,0] = 0
    phi = cp.real(cp.fft.ifftn(ph))

    return cp.asnumpy(omega), cp.asnumpy(phi), (cx, cy, cz)


def render_knot_3d(omega, phi, knot_curve, name, mass_ratio, color, elev=25, azim=45):
    """Render a single 3D knot with potential well."""
    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(111, projection='3d')

    omega_max = np.max(omega)
    phi_min = np.min(phi)

    # Potential isosurfaces (blue, outer shells)
    if abs(phi_min) > 1e-6:
        for frac, c, a in [(0.1, '#6688cc', 0.06), (0.25, '#4466aa', 0.12), (0.5, '#223388', 0.2)]:
            level = phi_min * frac
            try:
                verts, faces, _, _ = marching_cubes(-phi, level=-level, spacing=(dx,dx,dx))
                mesh = Poly3DCollection(verts[faces], alpha=a, facecolor=c, edgecolor='none')
                ax.add_collection3d(mesh)
            except (ValueError, RuntimeError):
                pass

    # Vorticity isosurfaces (orange/red, inner structure)
    if omega_max > 0.1:
        for frac, c, a in [(0.2, '#ffaa44', 0.2), (0.4, '#ff6600', 0.5), (0.65, '#cc2200', 0.8)]:
            level = omega_max * frac
            try:
                verts, faces, _, _ = marching_cubes(omega, level=level, spacing=(dx,dx,dx))
                mesh = Poly3DCollection(verts[faces], alpha=a, facecolor=c, edgecolor='none')
                ax.add_collection3d(mesh)
            except (ValueError, RuntimeError):
                pass

    # Knot curve
    cx, cy, cz = knot_curve
    ax.plot(cx, cy, cz, '-', color='white', linewidth=1.5, alpha=0.6)

    ax.set_xlim(0, L); ax.set_ylim(0, L); ax.set_zlim(0, L)
    ax.set_xlabel('x', fontsize=10); ax.set_ylabel('y', fontsize=10); ax.set_zlabel('z', fontsize=10)
    ax.view_init(elev=elev, azim=azim)
    ax.set_facecolor('#050510')
    ax.xaxis.pane.fill = False; ax.yaxis.pane.fill = False; ax.zaxis.pane.fill = False

    ax.set_title(f'{name}\nMass ratio: {mass_ratio:.2f}',
                fontsize=16, fontweight='bold', color=color, pad=15)

    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, facecolor='#080818', bbox_inches='tight')
    buf.seek(0)
    img = Image.open(buf).copy()
    plt.close(fig); buf.close()
    return img


def main():
    print("="*70)
    print("SHOWCASE: 3D Knot Gallery")
    print(f"Grid: {N}^3, GPU, 150 steps each for field development")
    print("="*70)

    center = [L/2, L/2, L/2]

    topologies = [
        ("Vortex Ring",   lambda c: make_ring(c),                    '#ff6600', 1.00),
        ("Hopf Link",     lambda c: make_hopf_link(c),               '#22aa44', 1.16),
        ("Trefoil Knot",  lambda c: make_trefoil(c),                 '#4444ff', 1.81),
        ("Torus T(2,5)",  lambda c: make_torus_knot(c, p=2, q=5),   '#aa22aa', 2.17),
        ("Torus T(2,7)",  lambda c: make_torus_knot(c, p=2, q=7),   '#cc8800', 2.73),
        ("Figure-Eight",  lambda c: make_figure_eight(c),            '#cc2222', 2.92),
    ]

    images = []
    for name, curve_func, color, mass_ratio in topologies:
        print(f"\n  [{name}]", end="", flush=True)
        t0 = time.time()
        omega, phi, knot_curve = compute_fields(curve_func, center, n_steps=150)
        print(f" computed ({time.time()-t0:.1f}s)", end="", flush=True)

        img = render_knot_3d(omega, phi, knot_curve, name, mass_ratio, color)
        img.save(RESULTS / f"gallery_{name.lower().replace(' ', '_').replace('(', '').replace(')', '').replace(',', '')}.png")
        images.append((img, name, mass_ratio, color))
        print(f" rendered")

    # Combined gallery: 2x3 grid
    print("\n  Compositing gallery...")
    fig, axes = plt.subplots(2, 3, figsize=(24, 16))

    for idx, (img, name, mass_ratio, color) in enumerate(images):
        row = idx // 3; col = idx % 3
        ax = axes[row][col]
        ax.imshow(np.array(img))
        ax.axis('off')

    fig.suptitle('MCT Mass Spectrum: Topology Determines Gravitational Mass',
                fontsize=22, fontweight='bold', y=0.98, color='white')
    fig.text(0.5, 0.01,
             'Orange: vorticity (the "particle"). Blue: gravitational potential well. '
             'Same equations, same energy. Only the knot shape differs.',
             ha='center', fontsize=14, color='#cccccc')

    plt.tight_layout(rect=[0, 0.03, 1, 0.96])
    fig.patch.set_facecolor('#080818')
    fig.savefig(RESULTS / "gallery_combined.png", dpi=120, facecolor='#080818',
               bbox_inches='tight')
    plt.close(fig)

    print(f"  Saved: gallery_combined.png + 6 individual renders")
    print("="*70)


if __name__ == "__main__":
    main()
