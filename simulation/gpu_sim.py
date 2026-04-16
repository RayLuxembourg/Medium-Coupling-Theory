"""
MCT GPU Simulation: Mass Spectrum + Two-Body
==============================================

Full GPU implementation using Taichi for Biot-Savart and CuPy for FFTs.

Key optimization: Biot-Savart is done as a single Taichi kernel that
processes ALL filament points in parallel on the GPU, avoiding the
Python loop entirely.
"""

import taichi as ti
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

ti.init(arch=ti.cuda, default_fp=ti.f64)

RESULTS = Path(__file__).parent / "results"
RESULTS.mkdir(exist_ok=True)

# ── Parameters ──
N = 128
L = 2.0 * np.pi
dx = L / N
dt_step = 0.002
nu_visc = 0.008
alpha_mct = 0.05
N_STEPS = 300
SAVE_EVERY = 30


# ── Taichi Biot-Savart kernel ──
# This runs the ENTIRE Biot-Savart sum on GPU in one kernel call

max_filament_pts = 500
filament_x = ti.field(dtype=ti.f64, shape=max_filament_pts)
filament_y = ti.field(dtype=ti.f64, shape=max_filament_pts)
filament_z = ti.field(dtype=ti.f64, shape=max_filament_pts)
filament_dlx = ti.field(dtype=ti.f64, shape=max_filament_pts)
filament_dly = ti.field(dtype=ti.f64, shape=max_filament_pts)
filament_dlz = ti.field(dtype=ti.f64, shape=max_filament_pts)

vel_x = ti.field(dtype=ti.f64, shape=(N, N, N))
vel_y = ti.field(dtype=ti.f64, shape=(N, N, N))
vel_z = ti.field(dtype=ti.f64, shape=(N, N, N))


@ti.kernel
def biot_savart_kernel(n_pts: ti.i32, Gamma: ti.f64, core_a: ti.f64,
                       box_L: ti.f64, grid_N: ti.i32):
    grid_dx = box_L / grid_N
    for i, j, k in ti.ndrange(grid_N, grid_N, grid_N):
        px = i * grid_dx
        py = j * grid_dx
        pz = k * grid_dx

        ux_sum = 0.0
        uy_sum = 0.0
        uz_sum = 0.0

        for p in range(n_pts):
            rx = px - filament_x[p]
            ry = py - filament_y[p]
            rz = pz - filament_z[p]

            # Periodic wrapping
            rx = rx - box_L * ti.round(rx / box_L)
            ry = ry - box_L * ti.round(ry / box_L)
            rz = rz - box_L * ti.round(rz / box_L)

            r2 = rx*rx + ry*ry + rz*rz + core_a*core_a
            r3_inv = 1.0 / (r2 * ti.sqrt(r2))

            # dl x r
            cx = filament_dly[p] * rz - filament_dlz[p] * ry
            cy = filament_dlz[p] * rx - filament_dlx[p] * rz
            cz = filament_dlx[p] * ry - filament_dly[p] * rx

            ux_sum += cx * r3_inv
            uy_sum += cy * r3_inv
            uz_sum += cz * r3_inv

        c = Gamma / (4.0 * 3.14159265358979323846)
        vel_x[i, j, k] = ux_sum * c
        vel_y[i, j, k] = uy_sum * c
        vel_z[i, j, k] = uz_sum * c


def init_biot_savart(curve_x, curve_y, curve_z, Gamma, core_a):
    """Initialize velocity field using GPU Biot-Savart kernel."""
    n = len(curve_x)
    assert n <= max_filament_pts

    # Tangent vectors
    dlx = np.roll(curve_x, -1) - curve_x
    dly = np.roll(curve_y, -1) - curve_y
    dlz = np.roll(curve_z, -1) - curve_z

    # Upload to Taichi fields
    filament_x.from_numpy(np.pad(curve_x, (0, max_filament_pts - n)))
    filament_y.from_numpy(np.pad(curve_y, (0, max_filament_pts - n)))
    filament_z.from_numpy(np.pad(curve_z, (0, max_filament_pts - n)))
    filament_dlx.from_numpy(np.pad(dlx, (0, max_filament_pts - n)))
    filament_dly.from_numpy(np.pad(dly, (0, max_filament_pts - n)))
    filament_dlz.from_numpy(np.pad(dlz, (0, max_filament_pts - n)))

    vel_x.fill(0); vel_y.fill(0); vel_z.fill(0)

    t0 = time.time()
    biot_savart_kernel(n, Gamma, core_a, L, N)
    ti.sync()
    dt = time.time() - t0

    ux = vel_x.to_numpy()
    uy = vel_y.to_numpy()
    uz = vel_z.to_numpy()

    return ux, uy, uz, dt


# ── Topology parametrizations ──

def make_ring(center, R, n_pts=200):
    t = np.linspace(0, 2*np.pi, n_pts, endpoint=False)
    return (center[0]+R*np.cos(t), center[1]+R*np.sin(t), np.full(n_pts, center[2]))

def make_trefoil(center, scale, n_pts=300):
    t = np.linspace(0, 2*np.pi, n_pts, endpoint=False)
    s = scale/3.0
    return (center[0]+s*(np.sin(t)+2*np.sin(2*t)),
            center[1]+s*(np.cos(t)-2*np.cos(2*t)),
            center[2]+s*(-np.sin(3*t)))

def make_figure_eight(center, scale, n_pts=300):
    t = np.linspace(0, 2*np.pi, n_pts, endpoint=False)
    s = scale/2.5
    return (center[0]+s*(2+np.cos(2*t))*np.cos(3*t),
            center[1]+s*(2+np.cos(2*t))*np.sin(3*t),
            center[2]+s*np.sin(4*t))

def make_torus_knot(center, scale, p, q, n_pts=300):
    t = np.linspace(0, 2*np.pi, n_pts, endpoint=False)
    rm = scale*0.6; rn = scale*0.3
    return (center[0]+(rm+rn*np.cos(q*t))*np.cos(p*t),
            center[1]+(rm+rn*np.cos(q*t))*np.sin(p*t),
            center[2]+rn*np.sin(q*t))

def make_hopf_link(center, scale, n_pts=150):
    t = np.linspace(0, 2*np.pi, n_pts, endpoint=False)
    R = scale*0.5
    x1=center[0]+R*np.cos(t); y1=center[1]+R*np.sin(t); z1=np.full(n_pts,center[2])
    x2=center[0]+R/2+R*np.cos(t); y2=np.full(n_pts,center[1]); z2=center[2]+R*np.sin(t)
    return (np.concatenate([x1,x2]), np.concatenate([y1,y2]), np.concatenate([z1,z2]))


# ── GPU Navier-Stokes + MCT coupling (CuPy) ──

class GPUSolver:
    def __init__(self):
        k = np.fft.fftfreq(N, d=L/(2*np.pi*N))
        KX, KY, KZ = np.meshgrid(k, k, k, indexing='ij')
        self.KX = cp.asarray(KX)
        self.KY = cp.asarray(KY)
        self.KZ = cp.asarray(KZ)
        self.K2 = self.KX**2 + self.KY**2 + self.KZ**2
        self.K2s = self.K2.copy()
        self.K2s[0,0,0] = 1.0
        self.visc = cp.exp(-nu_visc * self.K2 * dt_step)

    def to_gpu(self, ux, uy, uz):
        return cp.asarray(ux), cp.asarray(uy), cp.asarray(uz)

    def to_cpu(self, ux, uy, uz):
        return cp.asnumpy(ux), cp.asnumpy(uy), cp.asnumpy(uz)

    def vorticity(self, ux, uy, uz):
        uxh = cp.fft.fftn(ux); uyh = cp.fft.fftn(uy); uzh = cp.fft.fftn(uz)
        wx = cp.real(cp.fft.ifftn(1j*self.KY*uzh - 1j*self.KZ*uyh))
        wy = cp.real(cp.fft.ifftn(1j*self.KZ*uxh - 1j*self.KX*uzh))
        wz = cp.real(cp.fft.ifftn(1j*self.KX*uyh - 1j*self.KY*uxh))
        omega = cp.sqrt(wx**2 + wy**2 + wz**2)
        return omega, wx, wy, wz

    def coupling_potential(self, omega):
        rh = cp.fft.fftn(omega)
        ph = -4*cp.pi*alpha_mct * rh / self.K2s
        ph[0,0,0] = 0
        return cp.real(cp.fft.ifftn(ph)), ph

    def step(self, ux, uy, uz):
        omega, wx, wy, wz = self.vorticity(ux, uy, uz)
        phi, ph = self.coupling_potential(omega)

        gx = -cp.real(cp.fft.ifftn(1j*self.KX*ph))
        gy = -cp.real(cp.fft.ifftn(1j*self.KY*ph))
        gz = -cp.real(cp.fft.ifftn(1j*self.KZ*ph))

        rhsx = (wy*uz - wz*uy) + gx
        rhsy = (wz*ux - wx*uz) + gy
        rhsz = (wx*uy - wy*ux) + gz

        uxh = cp.fft.fftn(ux) + dt_step*cp.fft.fftn(rhsx)
        uyh = cp.fft.fftn(uy) + dt_step*cp.fft.fftn(rhsy)
        uzh = cp.fft.fftn(uz) + dt_step*cp.fft.fftn(rhsz)

        uxh *= self.visc; uyh *= self.visc; uzh *= self.visc

        div = self.KX*uxh + self.KY*uyh + self.KZ*uzh
        uxh -= self.KX*div/self.K2s
        uyh -= self.KY*div/self.K2s
        uzh -= self.KZ*div/self.K2s
        uxh[0,0,0]=0; uyh[0,0,0]=0; uzh[0,0,0]=0

        ux = cp.clip(cp.real(cp.fft.ifftn(uxh)), -20, 20)
        uy = cp.clip(cp.real(cp.fft.ifftn(uyh)), -20, 20)
        uz = cp.clip(cp.real(cp.fft.ifftn(uzh)), -20, 20)

        return ux, uy, uz, phi, omega


# ── Analysis ──

def radial_profile_gpu(phi_cpu, center):
    x = np.linspace(0, L, N, endpoint=False)
    X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
    rx = X-center[0]; ry = Y-center[1]; rz = Z-center[2]
    rx -= L*np.round(rx/L); ry -= L*np.round(ry/L); rz -= L*np.round(rz/L)
    R = np.sqrt(rx**2+ry**2+rz**2)
    n_bins = N//3
    edges = np.linspace(dx, L/3, n_bins+1)
    ctrs = 0.5*(edges[:-1]+edges[1:])
    avg = np.zeros(n_bins)
    Rf = R.ravel(); pf = phi_cpu.ravel()
    for i in range(n_bins):
        m = (Rf >= edges[i]) & (Rf < edges[i+1])
        if np.any(m): avg[i] = np.mean(pf[m])
    v = avg != 0
    return ctrs[v], avg[v]

def fit_power(r, phi, r_min, r_max):
    m = (r>=r_min)&(r<=r_max)&(np.abs(phi)>1e-30)
    if np.sum(m)<5: return 0,0,0
    lr=np.log(r[m]); lp=np.log(np.abs(phi[m]))
    c=np.polyfit(lr,lp,1)
    p=c[0]*lr+c[1]; sr=np.sum((lp-p)**2); st=np.sum((lp-np.mean(lp))**2)
    return c[0], np.exp(c[1]), (1-sr/st if st>0 else 0)


# ── Visualization ──

def make_frame(omega_cpu, phi_cpu, name, step_num, n_exp, GM, KE, ens):
    fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))
    mid = N//2

    ax = axes[0]
    im = ax.imshow(omega_cpu[:,:,mid].T, origin='lower', extent=[0,L,0,L], cmap='inferno')
    ax.set_title(f'{name}: vorticity (step {step_num})', fontsize=11)
    ax.set_xlabel('x'); ax.set_ylabel('y')
    plt.colorbar(im, ax=ax, shrink=0.8)

    ax = axes[1]
    vmax = max(np.max(np.abs(phi_cpu[:,:,mid]))*0.7, 1e-6)
    im = ax.imshow(phi_cpu[:,:,mid].T, origin='lower', extent=[0,L,0,L],
                  cmap='RdBu_r', vmin=-vmax, vmax=vmax)
    ax.set_title(f'MCT potential (n={n_exp:+.3f}, GM={GM:.4f})', fontsize=11)
    ax.set_xlabel('x'); ax.set_ylabel('y')
    plt.colorbar(im, ax=ax, shrink=0.8)

    ax = axes[2]
    center = [L/2, L/2, L/2]
    r, phi_avg = radial_profile_gpu(phi_cpu, center)
    if len(r) > 3:
        v = np.abs(phi_avg) > 1e-30
        if np.any(v):
            ax.loglog(r[v], np.abs(phi_avg[v]), 'b-', lw=2, label='Simulation')
            if GM > 0:
                ax.loglog(r[v], GM/r[v], 'r--', alpha=0.5, label='$1/r$')
            ax.legend(fontsize=9)
    ax.set_title(f'KE={KE:.3f}, ens={ens:.1f}', fontsize=11)
    ax.set_xlabel('r'); ax.set_ylabel('$|\\phi|$')
    ax.grid(True, alpha=0.3)

    plt.suptitle(f'{name} (step {step_num}/{N_STEPS})', fontsize=13)
    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=80)
    buf.seek(0)
    img = Image.open(buf).copy()
    plt.close(); buf.close()
    return img


# ── Run one topology ──

def run_topology(name, curve_func, curve_args, Gamma=2.0, core_a=0.2):
    center = [L/2, L/2, L/2]
    print(f"\n  [{name}]", end="", flush=True)

    cx, cy, cz = curve_func(*curve_args)
    ux, uy, uz, bs_time = init_biot_savart(cx, cy, cz, Gamma, core_a)
    print(f" Biot-Savart: {bs_time:.2f}s", end="", flush=True)

    solver = GPUSolver()
    ux_g, uy_g, uz_g = solver.to_gpu(ux, uy, uz)

    frames = []
    exponents = []
    amplitudes = []

    t_total = time.time()
    for s in range(N_STEPS + 1):
        if s % SAVE_EVERY == 0 or s == N_STEPS:
            omega_g, _, _, _ = solver.vorticity(ux_g, uy_g, uz_g)
            phi_g, _ = solver.coupling_potential(omega_g)
            omega_cpu = cp.asnumpy(omega_g)
            phi_cpu = cp.asnumpy(phi_g)

            r, phi_avg = radial_profile_gpu(phi_cpu, center)
            n_exp, A, r2 = fit_power(r, phi_avg, 0.4, L/3)
            exponents.append(n_exp)
            amplitudes.append(A)

            KE = float(0.5*cp.sum(ux_g**2+uy_g**2+uz_g**2).get()) * dx**3
            ens = float(0.5*cp.sum(omega_g**2).get()) * dx**3

            if s % SAVE_EVERY == 0:
                print(f"\n    step {s:4d}: KE={KE:.3f} ens={ens:.1f} n={n_exp:+.3f} GM={A:.4f}", end="", flush=True)
                frames.append(make_frame(omega_cpu, phi_cpu, name, s, n_exp, A, KE, ens))

        if s < N_STEPS:
            ux_g, uy_g, uz_g, _, _ = solver.step(ux_g, uy_g, uz_g)

    elapsed = time.time() - t_total
    print(f"\n    Total: {elapsed:.1f}s ({elapsed/N_STEPS*1000:.0f}ms/step)")

    # Save GIF
    if frames:
        frames[0].save(RESULTS / f"gpu_{name}.gif", save_all=True,
                       append_images=frames[1:], duration=300, loop=0)
        frames[0].save(RESULTS / f"gpu_{name}_start.png")
        frames[-1].save(RESULTS / f"gpu_{name}_final.png")

    n_avg = min(30, len(exponents))
    return {
        "name": name,
        "final_exponent": float(np.mean(exponents[-n_avg:])),
        "final_GM": float(np.mean(amplitudes[-n_avg:])),
        "time_seconds": float(elapsed),
    }


def get_crossing(name):
    return {"ring":0,"trefoil":3,"figure_eight":4,"T25":5,"T27":7,"hopf_link":0}.get(name,-1)


def main():
    print("="*70)
    print("MCT GPU SIMULATION: Mass Spectrum from Topology")
    print(f"Grid: {N}^3, steps: {N_STEPS}, GPU: RTX 4070 Ti Super")
    print("="*70)

    center = [L/2, L/2, L/2]
    Gamma = 2.0
    core = 0.2
    scale = 1.0

    topologies = [
        ("ring",         make_ring,         (center, 0.8)),
        ("trefoil",      make_trefoil,      (center, scale)),
        ("figure_eight", make_figure_eight, (center, scale)),
        ("T25",          make_torus_knot,   (center, scale, 2, 5)),
        ("T27",          make_torus_knot,   (center, scale, 2, 7)),
        ("hopf_link",    make_hopf_link,    (center, scale)),
    ]

    results = []
    for name, func, args in topologies:
        res = run_topology(name, func, args, Gamma=Gamma, core_a=core)
        res["crossing_number"] = get_crossing(name)
        results.append(res)

    # Normalize to ring
    ring_GM = [r['final_GM'] for r in results if r['name']=='ring'][0]
    for r in results:
        r['mass_ratio'] = float(r['final_GM']/ring_GM) if ring_GM > 0 else 0

    # ── Summary ──
    print("\n\n" + "="*70)
    print("MASS SPECTRUM RESULTS")
    print("="*70)
    print(f"  {'Topology':<16s} {'Cross':>5s} {'n':>8s} {'GM':>8s} {'Ratio':>8s} {'Time':>6s}")
    print("  "+"-"*55)
    for r in results:
        print(f"  {r['name']:<16s} {r['crossing_number']:>5d} {r['final_exponent']:>+8.3f} "
              f"{r['final_GM']:>8.4f} {r['mass_ratio']:>8.3f} {r['time_seconds']:>5.0f}s")

    # ── Plots ──
    fig, axes = plt.subplots(1, 3, figsize=(20, 6))

    # Mass vs crossing number
    ax = axes[0]
    cn = [r['crossing_number'] for r in results]
    mr = [r['mass_ratio'] for r in results]
    names = [r['name'] for r in results]
    ax.scatter(cn, mr, s=120, c='blue', zorder=5)
    for i in range(len(names)):
        ax.annotate(names[i], (cn[i], mr[i]), textcoords="offset points", xytext=(5,8), fontsize=9)
    ax.set_xlabel('Crossing number', fontsize=13)
    ax.set_ylabel('Effective mass (ring = 1)', fontsize=13)
    ax.set_title('MCT Mass Spectrum', fontsize=14)
    ax.grid(True, alpha=0.3)

    # Bar chart
    ax = axes[1]
    sr = sorted(results, key=lambda r: r['mass_ratio'])
    ns = [r['name'] for r in sr]
    mrs = [r['mass_ratio'] for r in sr]
    colors = plt.cm.plasma(np.linspace(0.2, 0.9, len(sr)))
    ax.barh(range(len(sr)), mrs, color=colors)
    ax.set_yticks(range(len(sr)))
    ax.set_yticklabels(ns, fontsize=10)
    ax.set_xlabel('Effective mass (ring = 1)', fontsize=13)
    ax.set_title('Mass Ranking by Topology', fontsize=14)
    ax.grid(True, alpha=0.3, axis='x')

    # Exponents
    ax = axes[2]
    exps = [r['final_exponent'] for r in results]
    colors2 = ['green' if abs(e+1)<0.1 else 'orange' if abs(e+1)<0.3 else 'red' for e in exps]
    ax.barh(range(len(names)), exps, color=colors2, alpha=0.7)
    ax.axvline(-1.0, color='black', lw=2, ls='--', label='$n=-1$')
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=10)
    ax.set_xlabel('Potential exponent', fontsize=13)
    ax.set_title('Far-field Exponent', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3, axis='x')

    plt.tight_layout()
    plt.savefig(RESULTS / "gpu_mass_spectrum.png", dpi=150)
    plt.close()
    print(f"\n  Saved: gpu_mass_spectrum.png")

    with open(RESULTS / "gpu_mass_spectrum_data.json", 'w') as f:
        json.dump({"params": {"N":N,"L":L,"dt":dt_step,"nu":nu_visc,
                              "alpha":alpha_mct,"Gamma":Gamma,"steps":N_STEPS},
                   "results": results}, f, indent=2)
    print(f"  Saved: gpu_mass_spectrum_data.json")
    print("="*70)


if __name__ == "__main__":
    main()
