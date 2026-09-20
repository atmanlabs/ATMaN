# PUNIT physical-readout survey — can the transducer be the computer?

Question: can N physical state dimensions support multiple simultaneous relational
readouts without serializing them, corrupting the state, or requiring conventional
computation equivalent to calculating those relationships afterward?

Short answer: YES for specific relations — with existence proofs below. But each
mechanism natively computes *its own* relation, reconfigurability reintroduces the
gate-metadata cost through the physics door, and the N-independent-bits bound
(data-processing inequality) survives in every mechanism. Parallel native readout
buys latency/energy, never capacity.

Collapse condition (non-negotiable): if any stage digitizes the dimensions and
computes the relation in logic, the device is a conventional computer with extra
steps. The sensor output must *already be* the relational quantity. Thresholding
an analog relational output (reading a voltmeter) is legitimate readout, not
computation of the relation.

## 1. Coincidence detection — native n-fold AND
N-fold coincidence logic: a count registers only when all channels fire inside
the coincidence window. That IS A∩B∩... computed by timing physics, no CPU.
Parallel across channel sets; false coincidences suppressed as the *product* of
dark-count rates. Destroys the detected photons, but a steady source regenerates
the state continuously — the "memory" is the source statistics, not one photon.
Honest limits: needs event-based dimensions (not static charge patterns without
re-emission); timing resolution bounds the window; accidental coincidences rise
with rate.

## 2. Capacitive overlap sensing — native overlap integral (the cylinder design)
Capacitance between two patterned conductive surfaces IS the geometric overlap
integral of the patterns — computed by electrostatics, not logic. Digital
calipers ship this: a patterned scale + sensing head resolves 0.01 mm from
capacitance alone, non-contact, non-destructive, continuous re-read. Multiple
sensor geometries at different positions/orientations = multiple simultaneous
relational readouts of one state. This is the honest physical embodiment of
PUNIT STATE + GATE PATTERN (sensor geometry) + CONTEXT (which sensors are
engaged) → INTERPRETED INFORMATION. Honest limits: analog — SNR, parasitic
capacitance, crosstalk between adjacent sensors; needs ADC + threshold to
symbolize, which is readout, not relation-computation.

## 3. Resistive crossbar (memristors) — native parallel dot product
Apply voltages to rows; by Kirchhoff's current law each column current IS the
sum over rows of V×G — a full matrix-vector product in one physical step, no
sequencing, no ALU. Low-voltage reads don't disturb resistive states. Closest
thing to a shipping "sensor is the computer" technology (in-memory computing
demos from IBM, Mythic, academia). Honest limits: natively computes *linear*
relations (weighted sums), not arbitrary Boolean gates; sneak paths and device
variability need calibration; column ADCs required (readout, not computation).

## 4. Fourier optical correlator — native 2D correlation at light speed
A lens computes the 2D Fourier transform of the input plane passively; a matched
filter multiplies in the Fourier domain; a second lens inverse-transforms. The
output plane IS the full correlation function — every shift evaluated in
parallel. Static hologram is undisturbed by readout photons. Honest limits:
computes correlation specifically; bulky, alignment- and vibration-sensitive;
needs coherent illumination; rewritable photorefractive media are slow.

## 5. Spin-wave interference — native majority via wave physics
Interfering spin waves in magnonic waveguides compute majority/inversion
directly in the wave superposition. Honest limits: research-stage; damping
limits propagation; the transduction in and out of the magnetic domain
(electrical→spin→electrical) is where the collapse condition lurks — if I/O
costs more than the saved compute, the advantage dies at the boundary.

## What survives, stated as falsifiable claims
1. A physical reader CAN output a relational quantity with no digitize-compute
   stage (mechanisms 1–4 are existence proofs, 5 is a candidate).
2. Parallel native readouts give latency/energy wins, never more than N
   independent bits from N dimensions. The stress-test bounds (T1–T4) are
   mechanism-independent.
3. Reconfigurability is the tax: a universal relational reader needs selectable
   gate patterns, and the software metadata cost (K²log3 gate store, 1.58N
   address width from stress.py T4) has a physical twin in selector
   area/wiring/power. Count it in hardware too.
4. Benchmark that decides it: ONE physical channel whose output equals the
   target relation with no logic stage between state and answer. Measure area,
   energy/query, latency, BER/crosstalk vs. conventional read-plus-AND at the
   same N. Predefine pass/fail before building. Do not rescue the model after.
