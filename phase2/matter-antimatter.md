# Matter-Antimatter Asymmetry (Baryogenesis) in MCT

The observable universe contains roughly $10^{80}$ baryons and almost no antibaryons. Sakharov (1967) identified three conditions necessary to produce this asymmetry from a symmetric initial state: baryon number violation, C and CP violation, and departure from thermal equilibrium. The Standard Model satisfies all three in principle, but the quantitative asymmetry it produces is too small by many orders of magnitude.

MCT offers a structural explanation.

---

## 1. The Puzzle

### 1.1 The numbers

The baryon asymmetry is quantified by:

$$
\eta = \frac{n_B - n_{\bar{B}}}{n_\gamma} \approx 6.1 \times 10^{-10}
$$

About one excess baryon per billion photons. The Standard Model predicts $\eta \sim 10^{-18}$, roughly $10^9$ times too small.

### 1.2 What happened

At early times (temperatures above $\sim 1$ GeV), the universe contained roughly equal amounts of matter and antimatter, constantly annihilating and recreating in thermal equilibrium. As the universe cooled below the QCD transition (~150 MeV), annihilation continued but pair creation stopped. If the asymmetry were zero, all matter and antimatter would annihilate, leaving a universe of pure radiation. Instead, a tiny excess of matter survived.

Something had to break the symmetry. In MCT, the medium's topology provides the mechanism.

---

## 2. MCT Mechanism

### 2.1 Antimatter as mirror topology

From [fermions-and-spin-statistics.md](fermions-and-spin-statistics.md#5-antimatter), an antiparticle is the mirror image of the corresponding particle's topological structure. Matter and antimatter correspond to left-handed and right-handed knots in the medium.

### 2.2 The medium is not mirror-symmetric

The toroidal medium flow has a definite handedness. The poloidal circulation has a direction: it rolls one way, not both. This breaks parity (P) at the cosmological level.

Combined with the compact dimension structure: the $SU(2)$ weak sector couples preferentially to left-handed structures ([nuclear-forces.md](nuclear-forces.md#23-weak-force-as-su2-flow)). This breaks C (charge conjugation) and CP (the combination of charge and parity).

### 2.3 The three Sakharov conditions in MCT

**Baryon number violation.** In the Standard Model, baryon number is violated by sphaleron processes (non-perturbative electroweak transitions). In MCT, sphalerons are topological transitions in the medium's compact dimensions: the $SU(2)$ flow undergoes a winding number change, converting baryons to leptons and vice versa. These transitions are unsuppressed at temperatures above the electroweak scale ($T > 100$ GeV).

**C and CP violation.** The medium's toroidal flow has a definite handedness (poloidal direction). The compact $SU(2)$ manifold has a preferred orientation. Together, these break both C and CP. The CP violation observed in kaon and B-meson systems is a low-energy manifestation of the medium's fundamental chirality.

**Departure from thermal equilibrium.** As the medium's toroidal flow expands (cosmological expansion from [Section 10](mathematical-framework.md#10-the-cosmological-constant-problem)), regions fall out of causal contact. The expansion rate exceeds the interaction rate at certain epoch, producing departure from equilibrium. In MCT, this is kinematic: the poloidal flow carries regions apart faster than they can equilibrate.

### 2.4 Why the excess is matter, not antimatter

The key MCT-specific content: the medium's poloidal flow direction selects matter over antimatter.

Consider the medium flowing in the poloidal direction with angular velocity $\Omega_p$. Topological structures whose angular momentum aligns with $\Omega_p$ couple more efficiently to the flow. Structures whose angular momentum opposes $\Omega_p$ couple less efficiently.

Particles (matter) have angular momentum aligned with the flow. Antiparticles (antimatter) have angular momentum opposed. During the epoch when baryon number violation is active (sphaleron processes at $T > 100$ GeV), the aligned structures are slightly more stable: they sit in deeper energy minima of the medium coupling potential, by an amount:

$$
\Delta E \sim \kappa \cdot \Omega_p \cdot l_P
$$

where $\kappa$ is the coupling strength and $l_P$ is the Planck length. This energy splitting biases sphaleron transitions toward producing baryons over antibaryons.

### 2.5 Estimating $\eta$

The asymmetry is proportional to the energy splitting relative to the temperature at which sphalerons freeze out ($T_\text{EW} \sim 100$ GeV):

$$
\eta \sim \frac{\Delta E}{k_B T_\text{EW}} \sim \frac{\kappa \cdot \Omega_p \cdot l_P}{k_B T_\text{EW}}
$$

With $\kappa \sim m_p c$ (proton coupling), $\Omega_p \sim H_0 \cdot (T_\text{EW}/T_0)^2$ (poloidal rate at electroweak epoch, extrapolated from today's Hubble rate), and $l_P \sim 10^{-35}$ m:

$$
\Omega_p(T_\text{EW}) \sim 2 \times 10^{-18} \times \left(\frac{100\;\text{GeV}}{2.7 \times 10^{-4}\;\text{eV}}\right)^2 \sim 2 \times 10^{-18} \times 1.4 \times 10^{29} \sim 3 \times 10^{11}\;\text{s}^{-1}
$$

$$
\Delta E \sim (1.7 \times 10^{-27}\;\text{kg} \times 3\times 10^8\;\text{m/s}) \times 3 \times 10^{11}\;\text{s}^{-1} \times 10^{-35}\;\text{m} \sim 1.5 \times 10^{-42}\;\text{J} \sim 10^{-23}\;\text{eV}
$$

$$
\eta \sim \frac{10^{-23}\;\text{eV}}{10^{11}\;\text{eV}} \sim 10^{-34}
$$

This is far too small. The naive estimate fails by 24 orders of magnitude, worse than the Standard Model.

### 2.6 Enhancement mechanisms

The naive estimate misses several potentially large factors:

1. **Resonant enhancement.** If the medium's toroidal flow has a resonance near the electroweak scale (a feature in the poloidal circulation spectrum at wavelengths $\sim 1/T_\text{EW}$), the effective $\Omega_p$ at that scale could be much larger than the simple extrapolation suggests.

2. **Topological amplification.** The sphaleron transition is itself a topological process. The medium's chirality does not just split energies; it could bias the topology of the transition itself, selecting one winding direction over the other. This is a non-perturbative effect that the energy splitting estimate does not capture.

3. **Phase transition dynamics.** If the electroweak transition in MCT is first-order (bubble nucleation rather than smooth crossover), the asymmetry can be generated at bubble walls where the medium's compact-dimension flow changes rapidly. This is the electroweak baryogenesis mechanism, which in the Standard Model requires BSM physics but in MCT may be natural if the dilaton potential produces a first-order transition.

The quantitative calculation requires solving the medium's compact-dimension dynamics through the electroweak epoch, which is a problem for the [simulation program](simulation.md).

---

## 3. Predictions

1. **CP violation is cosmological in origin.** The CP violation observed in meson systems is a local manifestation of the medium's global chirality. MCT predicts that CP violation parameters should be calculable from the medium's toroidal geometry.

2. **No new CP violation beyond the Standard Model.** If all CP violation comes from the medium's handedness, and the Standard Model correctly parametrizes the low-energy effects through the CKM and PMNS matrices, then searches for new sources of CP violation (e.g., electric dipole moments of fundamental particles) should find nothing beyond Standard Model predictions. Current bounds on the electron EDM ($|d_e| < 4.1 \times 10^{-30}$ e$\cdot$cm) are consistent with this.

3. **The baryon asymmetry encodes the medium's chirality.** The value of $\eta$ is not a random initial condition but a calculable consequence of the medium's geometry. The same parameters that determine the torus shape ([torus-parameters.md](torus-parameters.md)) should predict $\eta$.

---

## 4. Connection to Other Problems

- The medium's chirality connects to [fermions-and-spin-statistics.md](fermions-and-spin-statistics.md): left-handed and right-handed fermions are distinguished by their alignment with the medium's flow.
- The electroweak transition dynamics connect to the [dilaton/Higgs potential](kaluza-klein.md#4-the-dilaton-field): whether the transition is first-order determines the baryogenesis mechanism.
- The quantitative calculation requires the [simulation program](simulation.md) at Level 3 (cosmological simulation through the electroweak epoch).
