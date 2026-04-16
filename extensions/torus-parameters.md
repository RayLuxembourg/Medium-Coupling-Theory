# Torus Parameters: Determining the Medium's Geometry from Observation

This document addresses Open Problem 5 from the [main framework](../formalization/mathematical-framework.md#15-summary). MCT has four fundamental cosmological parameters: $R_T$ (major radius), $a_T$ (minor radius), $\Gamma_p$ (poloidal circulation), and $\Gamma_t$ (toroidal circulation). Here we constrain them from observational data.

---

## 1. The Parameters

### 1.1 What they mean

| Parameter | Symbol | Physical meaning |
|---|---|---|
| Major radius | $R_T$ | Distance from torus center to tube center |
| Minor radius | $a_T$ | Tube cross-section radius |
| Poloidal circulation | $\Gamma_p$ | Inside-out rolling speed |
| Toroidal circulation | $\Gamma_t$ | Rotation around the central loop |
| Aspect ratio | $R_T / a_T$ | Shape of the torus |

These replace the standard cosmological parameters ($H_0$, $\Omega_m$, $\Omega_\Lambda$, etc.) in MCT. The standard parameters are derived quantities:

$$
H_0 = \frac{\Gamma_p}{a_T} \cdot f(\theta_\text{obs})
$$

$$
\Omega_\Lambda \leftrightarrow \text{differential poloidal circulation (not a substance)}
$$

### 1.2 Derived medium parameters

In addition to the torus geometry, MCT has two medium-property parameters:

- $\alpha$: the coupling constant (angular momentum to coupling strength)
- $\rho_m$: the medium impedance

These determine $G = \alpha^2/(4\pi\rho_m)$ and are constrained by laboratory measurements of gravity. The torus parameters are constrained by cosmological observations.

---

## 2. Constraint from the Hubble Constant

### 2.1 Hubble's law in MCT

From [Section 10.3](../formalization/mathematical-framework.md#103-expansion-from-toroidal-geometry), the local Hubble parameter is:

$$
H(\theta) = \frac{\Gamma_p}{a_T} \cdot f(\theta)
$$

where $\theta$ is the observer's angular position within the torus cross-section and $f(\theta)$ is a geometric factor.

For an observer on the outer equatorial surface ($\theta = 0$, where the poloidal flow is directed outward), $f(0) = 1$ to leading order. This gives:

$$
H_0 \approx \frac{\Gamma_p}{a_T}
$$

With $H_0 \approx 70$ km/s/Mpc $\approx 2.27 \times 10^{-18}\;\text{s}^{-1}$, this constrains the ratio:

$$
\frac{\Gamma_p}{a_T} \approx 2.27 \times 10^{-18}\;\text{s}^{-1}
$$

### 2.2 What this tells us

This constrains the ratio $\Gamma_p / a_T$, not the individual values. A small torus with fast circulation and a large torus with slow circulation both produce the same Hubble constant.

Additional constraints are needed to separate $\Gamma_p$ and $a_T$.

---

## 3. Constraint from the Observable Universe

### 3.1 The observable horizon

The radius of the observable universe is $r_\text{obs} \approx 46.5$ Gly $\approx 4.4 \times 10^{26}$ m (comoving distance). In MCT, this must be less than or equal to $a_T$ (the tube radius), because objects separated by more than $a_T$ would be on opposite sides of the torus tube.

This gives a lower bound:

$$
a_T \geq 4.4 \times 10^{26}\;\text{m}
$$

If $a_T$ is only slightly larger than $r_\text{obs}$, the torus topology should be detectable in the CMB (matched circles, see [Prediction 2](../formalization/mathematical-framework.md#143-prediction-2-cmb-toroidal-topology-signatures)). If $a_T \gg r_\text{obs}$, the topology is undetectable.

### 3.2 Combined constraint

Using $\Gamma_p / a_T = H_0$ and $a_T \geq r_\text{obs}$:

$$
\Gamma_p \geq H_0 \cdot r_\text{obs} \approx 2.27 \times 10^{-18} \times 4.4 \times 10^{26} \approx 10^{9}\;\text{m/s}
$$

This is about $3c$. The poloidal circulation speed is several times the speed of light. This is not a contradiction: $c$ is the medium's internal disturbance speed, not a limit on the medium's own bulk flow. The medium itself can flow at any speed; $c$ limits only the propagation of signals through the medium (and hence the motion of coupled structures within it).

---

## 4. Constraint from CMB Topology

### 4.1 Matched circles

If the universe has toroidal topology with $a_T$ not much larger than $r_\text{obs}$, then the last scattering surface (the CMB sphere) wraps around the torus. This produces pairs of circles on the CMB sky with correlated temperature patterns.

The angular radius of matched circles depends on $a_T / r_\text{obs}$:

$$
\theta_\text{match} = \arccos\left(\frac{a_T}{2 r_\text{obs}}\right)
$$

For $a_T \approx r_\text{obs}$: $\theta_\text{match} \approx 60°$ (large circles, easy to detect).
For $a_T \approx 2 r_\text{obs}$: $\theta_\text{match} \approx 0°$ (circles shrink to points, undetectable).

Current CMB searches have not found matched circles above angular radii of ~10°. This gives:

$$
\frac{a_T}{r_\text{obs}} \gtrsim 1.97 \quad \Rightarrow \quad a_T \gtrsim 8.7 \times 10^{26}\;\text{m}
$$

roughly $2 r_\text{obs}$, so the torus tube is at least twice the observable universe radius.

### 4.2 Suppressed quadrupole

The CMB quadrupole ($\ell = 2$) is observed to be anomalously low compared to the $\Lambda$CDM prediction. In a toroidal universe, the largest wavelength modes that fit inside the torus are limited by $a_T$. If $a_T$ is not much larger than $r_\text{obs}$, the quadrupole is suppressed.

The observed suppression is consistent with $a_T / r_\text{obs} \sim 1.5$-$3$. Combined with the matched circles bound, this suggests:

$$
2 \lesssim \frac{a_T}{r_\text{obs}} \lesssim 3
$$

### 4.3 Axis of evil

The low CMB multipoles ($\ell = 2, 3$) are aligned along a preferred direction. In a toroidal universe, this direction is the torus symmetry axis. The alignment provides a measurement of the torus axis orientation but not its size.

---

## 5. Constraint from the Hubble Tension

### 5.1 The tension

From [Prediction 6](../formalization/mathematical-framework.md#147-prediction-6-hubble-tension-resolution):

- Planck CMB: $H_0 = 67.4 \pm 0.5$ km/s/Mpc
- SH0ES: $H_0 = 73.0 \pm 1.0$ km/s/Mpc

In MCT, $H$ depends on $\theta$ (position in the torus cross-section). The tension resolves if the CMB and local measurements probe different effective $\theta$ values.

### 5.2 Constraint on geometry

The fractional difference is:

$$
\frac{\Delta H}{H} = \frac{73.0 - 67.4}{70.2} \approx 0.08
$$

This requires:

$$
\frac{f(\theta_\text{local}) - f(\theta_\text{CMB})}{f(\bar\theta)} \approx 0.08
$$

For a simple model where $f(\theta) = 1 + \epsilon \cos\theta$, the 8% variation requires $\epsilon \approx 0.08$. This constrains the shape of the poloidal velocity profile within the torus cross-section. A nearly uniform profile ($\epsilon \ll 1$) would not produce enough variation; a strongly varying profile ($\epsilon \sim 0.1$) would.

---

## 6. Constraint from Acceleration (Dark Energy)

### 6.1 The effective $\Lambda$

From [Section 10.4](../formalization/mathematical-framework.md#104-accelerating-expansion):

$$
\Lambda_\text{eff} = \frac{1}{c_0^2}\left(\frac{dH}{dt} + H^2\right)
$$

The observed $\Lambda_\text{eff} \approx 1.1 \times 10^{-52}\;\text{m}^{-2}$ constrains the time derivative of the Hubble parameter, which in MCT is:

$$
\frac{dH}{dt} = \frac{d}{dt}\left(\frac{\Gamma_p}{a_T}\right) = \frac{1}{a_T}\frac{d\Gamma_p}{dt} - \frac{\Gamma_p}{a_T^2}\frac{da_T}{dt}
$$

This constrains the rate at which the torus circulation and size are evolving. A static torus ($d\Gamma_p/dt = 0$, $da_T/dt = 0$) gives $\Lambda_\text{eff} = H^2/c_0^2$, which is the right order of magnitude. The acceleration (positive $\Lambda_\text{eff}$) requires either increasing $\Gamma_p$ or decreasing $a_T$ (or both).

---

## 7. Summary of Constraints

| Observable | Constrains | Current bound |
|---|---|---|
| Hubble constant $H_0$ | $\Gamma_p / a_T$ | $\approx 2.3 \times 10^{-18}\;\text{s}^{-1}$ |
| Observable universe radius | $a_T$ (lower bound) | $\geq 4.4 \times 10^{26}$ m |
| CMB matched circles (null) | $a_T / r_\text{obs}$ | $\gtrsim 2$ |
| CMB quadrupole suppression | $a_T / r_\text{obs}$ | $\sim 2$-$3$ |
| Hubble tension | Poloidal velocity profile | $\epsilon \sim 0.08$ |
| Accelerating expansion | $d\Gamma_p/dt$, $da_T/dt$ | Consistent with evolving torus |
| $G$ (laboratory) | $\alpha^2 / \rho_m$ | $6.674 \times 10^{-11}\;\text{m}^3\text{kg}^{-1}\text{s}^{-2}$ |

### Best current estimates

Combining all constraints:

$$
a_T \sim (1\text{-}1.5) \times 10^{27}\;\text{m} \quad (\sim 2\text{-}3 \times r_\text{obs})
$$

$$
\Gamma_p \sim (2\text{-}3) \times 10^{9}\;\text{m/s} \quad (\sim 7\text{-}10 \times c)
$$

The aspect ratio $R_T / a_T$ is unconstrained by current data. It affects the toroidal circulation and the large-scale topology, but observations have not yet probed scales comparable to $R_T$.

---

## 8. Future Measurements

1. **CMB-S4 and LiteBIRD** will improve constraints on matched circles and multipole alignment. If $a_T / r_\text{obs} \lesssim 3$, these experiments should detect the toroidal topology.

2. **DESI and Euclid** will measure the expansion history to high precision, constraining $dH/dt$ and testing the MCT prediction that $w \neq -1$ (evolving "dark energy").

3. **Hubble tension resolution** from next-generation distance ladder measurements (JWST Cepheids, tip of the red giant branch) will test whether the tension persists and is consistent with the geometric interpretation.

4. **Gravitational wave standard sirens** (bright sirens with EM counterparts, dark sirens with galaxy catalogs) provide an independent $H_0$ measurement that can test directional dependence.
