# Gravitational Waves: Post-Newtonian Waveforms in MCT

This document addresses Open Problem 2 from the [main framework](../formalization/mathematical-framework.md#15-summary). Section 13 of the main document established that MCT reproduces GR's gravitational wave predictions at leading order. Here we go further: compute post-Newtonian corrections and identify where MCT might deviate from GR.

---

## 1. Review: GW Basics in MCT

Gravitational waves in MCT are propagating disturbances in the medium's flow field ([Section 13](../formalization/mathematical-framework.md#13-gravitational-waves-as-medium-propagation)). The linearized wave equation:

$$
\frac{\partial^2 \mathbf{h}}{\partial t^2} - c_0^2 \nabla^2 \mathbf{h} = 0
$$

gives propagation speed $c_0 = c$ (confirmed by GW170817 to $10^{-15}$) and two tensor polarization modes ($h_+$, $h_\times$).

The leading-order waveform for a circular binary with chirp mass $\mathcal{M}$:

$$
h(t) = \frac{4G\mathcal{M}}{c_0^4 d}\left(\frac{\pi f_\text{GW} \mathcal{M} G}{c_0^3}\right)^{2/3} \cos(2\pi f_\text{GW} t + \phi_0)
$$

This is identical to GR. Deviations enter at higher post-Newtonian (PN) order.

---

## 2. Post-Newtonian Expansion in MCT

### 2.1 The PN framework

The post-Newtonian expansion organizes corrections in powers of $v/c$, where $v$ is the orbital velocity. At $n$-th PN order, corrections scale as $(v/c)^{2n}$ relative to the leading term.

In GR, the PN expansion has been computed to high order (4.5PN for the phase, 3.5PN for the amplitude). LIGO/Virgo analyses use these templates to extract binary parameters from observed signals.

In MCT, the PN expansion proceeds identically to GR through several orders because the medium equations reduce to Einstein's equations in the continuum limit ([Section 6.3](../formalization/mathematical-framework.md#63-the-nonlinear-flow-equation)). Deviations appear only where the medium's micro-structure matters.

### 2.2 Where MCT deviates from GR

The medium's micro-structure introduces corrections at scales comparable to $l_P$. For a binary system with separation $r$, the corrections enter as powers of $l_P/r$.

At $n$-th PN order, the medium micro-structure contributes a correction:

$$
\delta\phi_n^\text{MCT} \sim \left(\frac{l_P}{r}\right)^{2} \left(\frac{v}{c}\right)^{2n}
$$

to the GW phase. Since $l_P \sim 10^{-35}$ m and typical binary separations are $r \sim 10^{4}$-$10^{6}$ m (for merging compact objects), the ratio $l_P/r \sim 10^{-39}$-$10^{-41}$. The corrections are extraordinarily small.

### 2.3 Dispersion

In a medium with micro-structure, waves at different frequencies can propagate at slightly different speeds (dispersion). If the medium's micro-structure introduces a dispersion relation:

$$
\omega^2 = c_0^2 k^2 \left(1 + \xi \frac{k^2}{k_P^2} + \cdots\right)
$$

where $k_P = 2\pi/l_P$ is the Planck wave number and $\xi$ is a dimensionless coefficient of order unity, then high-frequency gravitational waves travel at a slightly different speed than low-frequency ones.

The phase shift accumulated over a distance $d$ by a GW with frequency $f$ is:

$$
\Delta\phi_\text{disp} \approx \xi \pi \frac{f^2 d}{c_0 f_P^2}
$$

where $f_P = c_0/l_P \sim 10^{43}$ Hz.

For GW170817 ($f \sim 100$ Hz, $d \sim 4 \times 10^{25}$ m):

$$
\Delta\phi_\text{disp} \sim \xi \times 10^{-63}\;\text{rad}
$$

This is completely unmeasurable with any foreseeable detector. The medium's micro-structure leaves no detectable imprint on gravitational wave propagation.

---

## 3. Where MCT Might Be Testable in GW Physics

### 3.1 Near the merger

The PN approximation breaks down when $v \to c$, i.e., during the final few orbits before merger. In this regime, both GR and MCT require full numerical solutions.

If the merging objects are compact enough (neutron stars or black holes), the separation approaches $r_s = 2GM/c^2$. At $r \sim r_s$, the medium flow is relativistic (Section 6.4 of [the main framework](../formalization/mathematical-framework.md#64-schwarzschild-solution)) and the full nonlinear medium equations apply.

MCT predicts the merger waveform is identical to GR until the objects approach separations where the medium's micro-structure becomes relevant, i.e., $r \sim l_P$. This occurs only inside the merged object, not in the observable waveform. There is no measurable deviation during merger.

### 3.2 Ringdown and echoes

After merger, the remnant black hole settles into a steady state through quasinormal mode ringing. In GR, the ringdown frequencies are determined by the final black hole's mass and spin. In MCT, the same calculation applies because the medium equations and GR agree at scales $r \gg l_P$.

However, if the medium's micro-structure modifies the interior of the black hole (replacing the singularity with a finite core, see [Section 11](../formalization/mathematical-framework.md#11-the-black-hole-information-paradox)), then reflections from the core could produce **gravitational wave echoes**: repeated, attenuated copies of the ringdown signal arriving at late times.

The echo time delay is:

$$
\Delta t_\text{echo} \approx \frac{2r_s}{c_0} \ln\left(\frac{r_s}{r_\text{core}}\right)
$$

For a stellar-mass black hole ($r_s \sim 10$ km) with $r_\text{core} \sim l_P$:

$$
\Delta t_\text{echo} \approx \frac{2 \times 10^4\;\text{m}}{3 \times 10^8\;\text{m/s}} \times \ln(10^{39}) \approx 6 \times 10^{-3}\;\text{s}
$$

This is roughly 6 milliseconds, which is within the sensitivity band of LIGO/Virgo. Several searches for post-merger echoes have been performed, with tentative (2-3$\sigma$) detections reported. Confirmation of echoes would strongly support MCT's prediction that the black hole interior has structure.

### 3.3 Stochastic gravitational wave background

The medium itself, being a dynamical entity, should have thermal fluctuations at the Planck scale. These fluctuations produce a stochastic gravitational wave background with a characteristic spectrum:

$$
\Omega_\text{GW}(f) \sim \left(\frac{f}{f_P}\right)^3
$$

This spectrum is a prediction of MCT. It peaks at $f_P \sim 10^{43}$ Hz (far beyond any detector) but extends to lower frequencies with a steeply falling power law. At LIGO frequencies ($\sim 100$ Hz), the amplitude is negligible. At pulsar timing array frequencies ($\sim 10^{-8}$ Hz), it is also negligible.

The only regime where this background might be detectable is if the medium underwent a phase transition in the early universe (analogous to the cosmological QCD transition), producing a bump in the spectrum at a characteristic frequency. This connects to the torus parameters problem ([torus-parameters.md](torus-parameters.md)).

---

## 4. Testable Signatures

| Signature | MCT Prediction | GR Prediction | Measurable? |
|---|---|---|---|
| GW speed | $= c$ exactly | $= c$ exactly | Confirmed (GW170817) |
| Polarization modes | 2 (tensor only) | 2 (tensor only) | Testable with LISA, PTAs |
| Dispersion | $\sim (f/f_P)^2$, unmeasurable | None | No |
| Post-merger echoes | Yes, $\Delta t \sim$ ms | No | Possibly (LIGO O5+) |
| PN waveform deviations | $\sim (l_P/r)^2$, unmeasurable | N/A | No |
| Stochastic background shape | $(f/f_P)^3$ | Not predicted | No (too faint) |

The most promising observational target is **post-merger echoes**. A confirmed detection of echoes at the predicted time delay would support MCT's picture of a structured black hole interior.

---

## 5. Relation to Other Problems

- The echo time delay depends on $r_\text{core}$, which connects to the medium's micro-structure and the [simulation program](../simulation/simulation.md).
- The dispersion relation depends on the micro-structure's detailed form, which connects to [quantum mechanics from medium micro-structure](../formalization/mathematical-framework.md#9-quantum-mechanics-from-medium-micro-structure).
- A stochastic background from medium phase transitions connects to the [torus parameters](torus-parameters.md) and cosmological history.
