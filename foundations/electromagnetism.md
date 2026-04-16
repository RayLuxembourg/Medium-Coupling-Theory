# Electromagnetism: What Charge, Current, Light, and Sparks Actually Are

We established that the medium has a compact fifth dimension and that electromagnetic phenomena are flow in that dimension ([Kaluza-Klein connection](../extensions/kaluza-klein.md)). We showed that the vector potential $\mathbf{A}$ is the medium's compact-dimension flow state ([Section 8](../formalization/mathematical-framework.md#8-the-aharonov-bohm-effect-potentials-are-the-medium)).

This document takes those results and follows them to their mechanical conclusions. What is charge? What is an electric field? Why do opposite charges attract? What is a photon? Why does rubbing a balloon on your hair make sparks? Why does a current create a magnetic field? What is the Coulomb barrier and why does it take so much energy to overcome it?

All of these have the same answer: the medium has a compact dimension, and things can wind around it.

---

## 1. What Is Charge?

### 1.1 Winding in the compact dimension

From [kaluza-klein.md](../extensions/kaluza-klein.md#3-charge-quantization), a charged particle carries momentum in the compact fifth dimension. This momentum is quantized because the dimension is periodic (a circle of radius $R_5$):

$$
p_5 = \frac{n\hbar}{R_5}, \quad n = 0, \pm 1, \pm 2, \ldots
$$

From the perspective of the 3 extended dimensions, this quantized momentum appears as electric charge:

$$
q = n \cdot e
$$

where $e$ is the elementary charge (one unit of compact-dimension winding).

In plain language: **charge is angular momentum in a direction you cannot see.** The compact dimension is too small to perceive directly ($R_5 \sim 10^{-34}$ m), but the winding around it has consequences that are fully visible in our 3D world.

### 1.2 Positive vs. negative

Positive charge ($n > 0$) winds clockwise around the compact dimension. Negative charge ($n < 0$) winds counterclockwise. The direction is conventional, but the physical point is real: opposite charges wind in opposite directions.

An electron has $n = -1$. A proton has $n = +1$. They wind in opposite directions around the same compact circle.

### 1.3 Why charge is conserved

Charge conservation is momentum conservation in the compact dimension. The compact dimension is translationally symmetric (every point on the circle is equivalent). By Noether's theorem ([mct-action.md](mct-action.md#51-noethers-theorem-applied-to-mct)), this symmetry guarantees conservation of $p_5$, which is charge.

You cannot create charge from nothing for the same reason you cannot create momentum from nothing: the underlying symmetry forbids it. Charge is always created in equal and opposite pairs (electron + positron, both with $|n| = 1$ but opposite signs) because the total compact-dimension momentum must be conserved.

### 1.4 Why quarks have fractional charge

Quarks carry charges of $+2/3$ or $-1/3$ in units of $e$. In MCT, this means quarks wind fractionally around the compact dimension: they complete $1/3$ or $2/3$ of the circle per revolution.

This is possible because quarks are confined ([nuclear-forces.md](../extensions/nuclear-forces.md#4-color-confinement-detailed-mechanism)). A free particle must have integer winding (the wavefunction must be single-valued around the compact circle). But quarks are never free. Inside a hadron, the combined winding of the quarks is always an integer: in a proton ($u u d$), the charges are $+2/3 + 2/3 - 1/3 = +1$. The confinement mechanism ensures that only integer-wound states can exist as free particles.

---

## 2. What Is an Electric Field?

### 2.1 A flow gradient in the compact dimension

A mass creates a flow pattern in the extended dimensions (gravity). A charge creates a flow pattern in the compact dimension (the electric field).

Place a charge $q$ at the origin. It is winding around the compact dimension. This winding stirs the surrounding medium's compact-dimension flow, creating a pattern that falls off with distance:

$$
\mathbf{E}(r) = \frac{q}{4\pi\epsilon_0 r^2}\hat{\mathbf{r}}
$$

This is Coulomb's law. In MCT, it has the same origin as Newton's law of gravity ([Section 2](../formalization/mathematical-framework.md#2-derivation-newtonian-gravity-from-medium-flow)): a localized source in a 3D isotropic medium produces a $1/r^2$ field. Gravity is the $1/r^2$ field from a mass (extended-dimension winding). The electric field is the $1/r^2$ field from a charge (compact-dimension winding).

The $1/r^2$ comes from the same place in both cases: 3 extended spatial dimensions. The electric field goes as $1/r^2$ because the compact-dimension flow spreads over the surface of a 3D sphere, exactly like gravity.

### 2.2 Why the electric field is so much stronger than gravity

The ratio of the electromagnetic to gravitational force between two protons:

$$
\frac{F_\text{EM}}{F_\text{grav}} = \frac{e^2/(4\pi\epsilon_0)}{Gm_p^2} \approx 10^{36}
$$

This enormous ratio has never been explained. In MCT, it follows from the geometry.

The gravitational coupling depends on the angular momentum in the extended dimensions (spread over 3 large directions). The electromagnetic coupling depends on the angular momentum in the compact dimension (concentrated into a tiny circle of radius $R_5 \sim 10^{-34}$ m).

Think of water flowing through pipes. The same flow rate through a wide pipe (extended dimensions) produces low pressure. The same flow rate through a narrow pipe (compact dimension) produces high pressure. The compact dimension is roughly $10^{31}$ times smaller than a proton. The "pressure" (force per unit charge) in the compact dimension is correspondingly higher.

Quantitatively, from the [Kaluza-Klein analysis](../extensions/kaluza-klein.md#23-the-electromagnetic-coupling-constant):

$$
\frac{\alpha_\text{EM}}{G m_p^2 / (\hbar c)} = \frac{l_P^2 / R_5^2}{(m_p / m_P)^2} \approx \frac{(10^{-35})^2 / (10^{-34})^2}{(10^{-27} / 10^{-8})^2} \sim \frac{10^{-2}}{10^{-38}} \sim 10^{36}
$$

The hierarchy between gravity and electromagnetism is a ratio of length scales: the Planck length vs. the compact dimension radius vs. the proton size. There is no fine-tuning. It falls out of the geometry.

---

## 3. Why Opposite Charges Attract

### 3.1 The flow picture

A positive charge winds clockwise around the compact dimension, creating a compact-dimension flow pattern around itself. A negative charge winds counterclockwise, creating the opposite flow pattern.

When the two are brought near each other, their compact-dimension flows are complementary. The clockwise flow from the positive charge and the counterclockwise flow from the negative charge merge smoothly. The medium's compact-dimension flow between them is constructive: it flows from one charge through the intervening space and into the other.

This constructive merging reduces the total flow energy. The system moves toward the configuration that minimizes energy, which means the charges move together. This is attraction.

### 3.2 Why like charges repel

Two positive charges both wind clockwise. Their compact-dimension flows compete rather than complement. Between them, the flows point in opposite directions. This creates shear and increases the medium's energy. The system moves to reduce this energy, which means the charges push apart. This is repulsion.

### 3.3 The fluid analogy (exact)

Two vortices spinning in opposite directions in a fluid attract each other and eventually annihilate. Two vortices spinning in the same direction repel (they orbit around each other). This is the same physics in 2D that charges exhibit in 3D+compact. The compact dimension provides the "spin direction" (clockwise vs. counterclockwise winding), and the extended dimensions provide the space over which the flow patterns interact.

---

## 4. What Is a Magnetic Field?

### 4.1 Moving charge = tilted winding

A stationary charge winds around the compact dimension. When the charge moves through the extended dimensions, the winding axis tilts: it now has a component in both the compact direction and the direction of motion.

From the perspective of an observer in the extended dimensions, this tilted winding produces two effects:
- The compact-dimension component is the electric field (unchanged)
- The mixed compact/extended component is the magnetic field

$$
\mathbf{B} = \frac{\mu_0}{4\pi} \frac{q\mathbf{v} \times \hat{\mathbf{r}}}{r^2}
$$

The magnetic field IS the electric field seen by a frame-shifted observer. This is why special relativity unifies $\mathbf{E}$ and $\mathbf{B}$ into the electromagnetic field tensor $F_{\mu\nu}$. In MCT, the unification is geometric: $\mathbf{E}$ and $\mathbf{B}$ are different projections of the same compact-dimension flow, seen by observers in different states of motion through the medium.

### 4.2 Why current creates a magnetic field

A wire carrying current has moving charges (electrons drifting through the lattice). Each moving electron has a tilted winding. The collective tilted windings of many electrons add up to a macroscopic compact/extended mixed flow around the wire:

$$
\oint \mathbf{B} \cdot d\mathbf{l} = \mu_0 I
$$

This is Ampere's law. The current $I$ is a macroscopic flow of compact-dimension winding through the wire. The magnetic field $\mathbf{B}$ is the medium's response in the mixed compact/extended direction.

---

## 5. What Is Light?

### 5.1 A propagating disturbance in the compact dimension

Light is a wave in the medium, but not in the extended dimensions. A photon is an oscillation of the compact-dimension flow that propagates through the extended dimensions.

The electric field component: the compact-dimension flow oscillates back and forth (the flow direction in the compact circle alternates). The magnetic field component: the mixed compact/extended flow oscillates perpendicular to the electric component. The two oscillations are coupled and self-sustaining. Each one generates the other as it changes (Faraday induction: changing $\mathbf{B}$ creates $\mathbf{E}$; displacement current: changing $\mathbf{E}$ creates $\mathbf{B}$).

$$
\nabla \times \mathbf{E} = -\frac{\partial \mathbf{B}}{\partial t}, \quad \nabla \times \mathbf{B} = \mu_0\epsilon_0 \frac{\partial \mathbf{E}}{\partial t}
$$

These are Maxwell's equations. They describe how the compact-dimension flow sustains itself as a traveling wave. The wave speed is:

$$
c = \frac{1}{\sqrt{\mu_0 \epsilon_0}}
$$

which equals the medium's characteristic speed $c_0$. This is because both light and gravitational disturbances propagate at the medium's internal disturbance speed. The medium doesn't care whether the oscillation is in the compact or extended dimensions; the wave speed is a property of the medium itself.

### 5.2 Why light has no mass

A photon oscillates in the compact dimension but does not wind around it. It has no net $p_5$ (no charge) and no net poloidal angular momentum (no mass). It is a wave, not a knot. Waves propagate; knots persist. Massless particles are disturbances in the medium. Massive particles are structures in the medium.

### 5.3 Polarization

The compact-dimension flow can oscillate in different orientations relative to the propagation direction:
- **Linear polarization**: the oscillation plane is fixed.
- **Circular polarization**: the oscillation plane rotates as the wave propagates. This corresponds to the compact-dimension flow spiraling along the propagation axis.
- **Unpolarized light**: a mixture of orientations.

Circular polarization carries angular momentum ($\pm\hbar$ per photon). This is angular momentum in the compact dimension with a component along the propagation axis. This is why circularly polarized light can exert torque on absorbing objects (Beth's experiment, 1936).

---

## 6. What Is a Spark?

### 6.1 Dielectric breakdown

A spark is a rapid, self-amplifying cascade of compact-dimension flow reorganization.

Start with a large electric field (strong compact-dimension flow gradient) between two points, for example, a thundercloud and the ground. The field accelerates any free electron in the air. The electron gains kinetic energy from the compact-dimension flow gradient.

When the electron has enough energy ($\sim 12$ eV for nitrogen), it hits a neutral atom and knocks out another electron (ionization). The compact-dimension flow is strong enough to rip the winding out of a bound state and send it flying independently. Now there are two free electrons, both accelerating in the field. They hit more atoms, produce more free electrons. The cascade doubles every collision length.

In milliseconds, a channel of ionized gas connects the two points. The compact-dimension flow has found a low-resistance path. Current surges through. The medium's compact-dimension flow reorganizes violently, and the rapid flow changes radiate photons (light). The thermal energy heats the air to $\sim 30{,}000$ K, producing the white-hot glow.

A spark is the compact dimension having a seizure. The orderly flow gradient breaks down into chaotic, cascading discharge.

### 6.2 Why sparks produce light

Every accelerating charge radiates. In MCT: when a charged structure (compact-dimension winding) accelerates in the extended dimensions, the compact/extended mixed flow changes. This change propagates outward as a photon. The more violent the acceleration, the more energetic the photon (higher frequency light).

In a spark, billions of electrons accelerate abruptly. Each one radiates. The combined radiation is the visible flash. The spectrum is broadband (white light) because the accelerations span a wide range of energies.

---

## 7. What Is the Coulomb Barrier?

### 7.1 The barrier

Two atomic nuclei both carry positive charge (same winding direction in the compact dimension). Their compact-dimension flows repel. To fuse them, you must push them close enough ($\sim 10^{-15}$ m) that the strong nuclear force (a different compact dimension, the $SU(3)$ flow, see [nuclear-forces.md](../extensions/nuclear-forces.md)) takes over and binds them.

The energy required to overcome the electromagnetic repulsion at nuclear distances is the Coulomb barrier:

$$
E_C = \frac{Z_1 Z_2 e^2}{4\pi\epsilon_0 r_\text{nuclear}} \approx \frac{Z_1 Z_2 \times 1.44\;\text{MeV}\cdot\text{fm}}{r_\text{nuclear}}
$$

For two protons ($Z_1 = Z_2 = 1$, $r_\text{nuclear} \approx 1$ fm):

$$
E_C \approx 1.44\;\text{MeV} \approx 1.7 \times 10^{10}\;\text{K (thermal equivalent)}
$$

### 7.2 Why it is so hard to overcome

The Coulomb barrier is the cost of forcing two same-direction compact-dimension windings into close proximity. The compact-dimension flow between them becomes increasingly stressed as the nuclei approach. The energy stored in this compressed flow is the barrier.

This is why nuclear fusion requires extreme temperatures (millions of degrees in a tokamak, hundreds of millions in inertial confinement). You must give the nuclei enough kinetic energy to push through the zone of maximum compact-dimension flow stress and reach the distance where the $SU(3)$ compact-dimension flow takes over.

### 7.3 Quantum tunneling through the barrier

Nuclei can fuse even when their kinetic energy is below $E_C$. This is quantum tunneling, and it is essential for stellar fusion (the Sun's core is only $\sim 15$ million K, well below the classical barrier for proton-proton fusion).

In MCT, tunneling is the medium's stochastic micro-structure at work ([Section 9](../formalization/mathematical-framework.md#9-quantum-mechanics-from-medium-micro-structure)). The nuclei don't "tunnel" through a barrier. The medium's Planck-scale fluctuations occasionally push them through. The micro-structural noise provides momentary kicks that can carry a particle past the barrier. The probability is low (exponentially suppressed by the barrier height and width), but nonzero.

The tunneling probability is:

$$
P \sim \exp\left(-\frac{2}{\hbar}\int_{r_1}^{r_2}\sqrt{2m(V(r) - E)}\,dr\right)
$$

This is the standard Gamow factor. In MCT, the integral represents the "difficulty" of the medium's micro-structural fluctuations pushing the system through the region of high compact-dimension flow stress. Thicker or taller barriers need rarer fluctuations.

### 7.4 A coupling modulation angle

Here is where MCT suggests something new. If the compact-dimension coupling (charge) can be modulated ([coupling-modulation.md](coupling-modulation.md)), then the Coulomb barrier can be reduced.

A hypothetical device that partially screens the compact-dimension winding of two approaching nuclei would lower the barrier:

$$
E_C' = (1 - \delta)^2 E_C
$$

where $\delta$ is the fractional coupling reduction. Even a small reduction ($\delta = 0.1$) lowers the barrier by 19%, dramatically increasing the tunneling rate.

This is speculative, but it follows directly from MCT. If charge is compact-dimension winding and coupling can be modulated, then electrostatic repulsion can be reduced without physically removing charge. The charge is still there; its coupling to the compact-dimension flow is weakened. This would be relevant to fusion energy: lowering the Coulomb barrier makes fusion easier.

---

## 8. Electricity: What Flows and Why

### 8.1 Current as winding transport

Electric current in a wire is electrons (compact-dimension winding in the $n = -1$ direction) drifting through a lattice of nuclei (compact-dimension winding in the $n = +1$ direction, screened by inner-shell electrons).

The electrons drift slowly ($\sim 10^{-4}$ m/s, the drift velocity), but the compact-dimension flow pattern propagates at $c$. When you flip a light switch, you don't wait for an electron to traverse the wire. The compact-dimension flow change propagates along the wire at the speed of the medium's disturbances ($c$), and the electrons at the far end start moving almost immediately.

This is analogous to pushing one end of a long pipe full of water. The water at the far end starts flowing almost immediately, not because the first water molecule traveled the length of the pipe, but because the pressure wave propagated at the speed of sound.

### 8.2 Voltage as compact-dimension flow potential

Voltage is the difference in compact-dimension flow potential between two points. A battery maintains a chemical reaction that continuously creates a compact-dimension flow gradient between its terminals (by accumulating opposite windings at each terminal).

When a conductor connects the terminals, the compact-dimension flow gradient drives winding transport (current). The energy delivered to a load (light bulb, motor) comes from the compact-dimension flow: winding carriers moving "downhill" in the compact-dimension potential transfer their flow energy to the load.

### 8.3 Resistance as compact-dimension scattering

Resistance is the scattering of mobile windings (electrons) by the lattice. As electrons drift through the conductor, they collide with lattice imperfections, phonons (lattice vibrations), and impurities. Each collision deflects the electron, randomizing its compact-dimension flow direction momentarily. This costs energy, which appears as heat.

A superconductor has zero resistance because the Cooper pairs do not scatter off the lattice. Their coherent quantum state prevents individual scattering events. In MCT terms: the Cooper pair's linked topology (opposite compact-dimension windings) makes it invisible to the lattice's scattering potential. The pair glides through without disrupting or being disrupted by the lattice's compact-dimension flow.

---

## 9. Summary

| EM Concept | MCT Mechanical Picture |
|---|---|
| Electric charge | Winding in the compact 5th dimension |
| Positive/negative | Clockwise/counterclockwise winding |
| Electric field | Compact-dimension flow gradient from a charge |
| Magnetic field | Mixed compact/extended flow from a moving charge |
| Coulomb's law ($1/r^2$) | Same origin as Newton's law: 3D isotropic medium response |
| Attraction (opposite charges) | Complementary flows merge, lower energy |
| Repulsion (like charges) | Competing flows create shear, higher energy |
| Light (photon) | Propagating oscillation of compact-dimension flow |
| EM wave speed = $c$ | Same medium, same characteristic speed |
| Electric current | Transport of compact-dimension winding through a conductor |
| Voltage | Compact-dimension flow potential difference |
| Resistance | Scattering of winding carriers by lattice |
| Superconductivity | Cooper pair topology is invisible to lattice scattering |
| Spark/lightning | Cascading ionization from compact-dimension flow breakdown |
| Coulomb barrier | Repulsive compact-dimension flow stress at nuclear distances |
| Quantum tunneling | Medium micro-structural fluctuations push through the barrier |

Every electromagnetic phenomenon is compact-dimension flow dynamics. The "magic" of electromagnetism is the same physics as gravity, played out in a dimension too small to see directly but whose effects dominate the visible world because the compact dimension concentrates the flow into a tiny cross-section.
