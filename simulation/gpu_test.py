"""Quick GPU benchmark: compare CPU vs GPU for our key operations."""

import numpy as np
import cupy as cp
import time

N = 128
print(f"Grid: {N}^3 = {N**3:,} points")
print(f"GPU: {cp.cuda.runtime.getDeviceProperties(0)['name'].decode()}")
print()

# Test 1: FFT
print("--- FFT Benchmark ---")
data_cpu = np.random.randn(N, N, N).astype(np.float64)
data_gpu = cp.asarray(data_cpu)

# CPU
from scipy.fft import fftn as cpu_fftn
t0 = time.time()
for _ in range(10):
    _ = cpu_fftn(data_cpu)
cpu_time = (time.time() - t0) / 10
print(f"  CPU scipy FFT:  {cpu_time*1000:.1f} ms")

# GPU
cp.fft.fftn(data_gpu)  # warmup
cp.cuda.Stream.null.synchronize()
t0 = time.time()
for _ in range(10):
    _ = cp.fft.fftn(data_gpu)
cp.cuda.Stream.null.synchronize()
gpu_time = (time.time() - t0) / 10
print(f"  GPU cupy FFT:   {gpu_time*1000:.1f} ms")
print(f"  Speedup: {cpu_time/gpu_time:.1f}x")

# Test 2: Poisson solve (FFT + division + IFFT)
print("\n--- Poisson Solve Benchmark ---")
rho_cpu = np.random.randn(N, N, N)
rho_gpu = cp.asarray(rho_cpu)

from scipy.fft import fftfreq
k = fftfreq(N, d=1.0/(2*np.pi*N))
KX, KY, KZ = np.meshgrid(k, k, k, indexing='ij')
K2 = KX**2 + KY**2 + KZ**2
K2[0,0,0] = 1.0
K2_gpu = cp.asarray(K2)

# CPU
from scipy.fft import fftn, ifftn
t0 = time.time()
for _ in range(10):
    rh = fftn(rho_cpu)
    ph = -4*np.pi*rh / K2
    ph[0,0,0] = 0
    phi = np.real(ifftn(ph))
cpu_time = (time.time() - t0) / 10
print(f"  CPU Poisson:  {cpu_time*1000:.1f} ms")

# GPU
cp.fft.fftn(rho_gpu)  # warmup
cp.cuda.Stream.null.synchronize()
t0 = time.time()
for _ in range(10):
    rh = cp.fft.fftn(rho_gpu)
    ph = -4*np.pi*rh / K2_gpu
    ph[0,0,0] = 0
    phi = cp.real(cp.fft.ifftn(ph))
cp.cuda.Stream.null.synchronize()
gpu_time = (time.time() - t0) / 10
print(f"  GPU Poisson:  {gpu_time*1000:.1f} ms")
print(f"  Speedup: {cpu_time/gpu_time:.1f}x")

# Test 3: Biot-Savart (the big bottleneck)
print("\n--- Biot-Savart Benchmark (single filament point) ---")
x = np.linspace(0, 2*np.pi, N, endpoint=False)
X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
X_gpu = cp.asarray(X); Y_gpu = cp.asarray(Y); Z_gpu = cp.asarray(Z)

# CPU: one filament point
t0 = time.time()
for _ in range(5):
    rx = X - 1.0; ry = Y - 2.0; rz = Z - 3.0
    r2 = rx**2 + ry**2 + rz**2 + 0.01
    r3i = 1.0 / (r2**1.5)
    ux = (0.1*rz - 0.2*ry) * r3i
cpu_time = (time.time() - t0) / 5
print(f"  CPU (1 point): {cpu_time*1000:.1f} ms")

# GPU
t0 = time.time()
for _ in range(5):
    rx = X_gpu - 1.0; ry = Y_gpu - 2.0; rz = Z_gpu - 3.0
    r2 = rx**2 + ry**2 + rz**2 + 0.01
    r3i = 1.0 / (r2**1.5)
    ux = (0.1*rz - 0.2*ry) * r3i
cp.cuda.Stream.null.synchronize()
gpu_time = (time.time() - t0) / 5
print(f"  GPU (1 point): {gpu_time*1000:.1f} ms")
print(f"  Speedup: {cpu_time/gpu_time:.1f}x")

# Estimate full Biot-Savart time
n_filament = 200
print(f"\n  Estimated full Biot-Savart ({n_filament} points):")
print(f"    CPU: {n_filament * cpu_time:.1f}s")
print(f"    GPU: {n_filament * gpu_time:.1f}s")

# Test 4: Full NS step estimate
print("\n--- Full NS Step (vorticity + coupling + projection) ---")
ux_gpu = cp.random.randn(N,N,N)
uy_gpu = cp.random.randn(N,N,N)
uz_gpu = cp.random.randn(N,N,N)
KX_gpu = cp.asarray(KX); KY_gpu = cp.asarray(KY); KZ_gpu = cp.asarray(KZ)

cp.cuda.Stream.null.synchronize()
t0 = time.time()
for _ in range(10):
    # Vorticity
    uxh = cp.fft.fftn(ux_gpu); uyh = cp.fft.fftn(uy_gpu); uzh = cp.fft.fftn(uz_gpu)
    wx = cp.real(cp.fft.ifftn(1j*KY_gpu*uzh - 1j*KZ_gpu*uyh))
    wy = cp.real(cp.fft.ifftn(1j*KZ_gpu*uxh - 1j*KX_gpu*uzh))
    wz = cp.real(cp.fft.ifftn(1j*KX_gpu*uyh - 1j*KY_gpu*uxh))
    omega = cp.sqrt(wx**2 + wy**2 + wz**2)
    # Coupling potential
    rh = cp.fft.fftn(omega)
    ph = -4*cp.pi*0.05*rh / K2_gpu
    ph[0,0,0] = 0
    gx = -cp.real(cp.fft.ifftn(1j*KX_gpu*ph))
    gy = -cp.real(cp.fft.ifftn(1j*KY_gpu*ph))
    gz = -cp.real(cp.fft.ifftn(1j*KZ_gpu*ph))
    # Nonlinear + coupling
    rhsx = (wy*uz_gpu - wz*uy_gpu) + gx
    # Advance
    uxh_new = uxh + 0.002*cp.fft.fftn(rhsx)
cp.cuda.Stream.null.synchronize()
gpu_step = (time.time() - t0) / 10
print(f"  GPU NS step: {gpu_step*1000:.1f} ms")
print(f"  300 steps: {300*gpu_step:.1f}s")

print("\n=== SUMMARY ===")
print(f"Full simulation (Biot-Savart init + 300 NS steps) estimated:")
print(f"  GPU: {n_filament*gpu_time + 300*gpu_step:.1f}s")
print(f"  CPU: {n_filament*cpu_time + 300*0.8:.0f}s (0.8s/step estimated)")
