# HOSTILE MECHANISM TRACE — where does the relational operation physically occur?

Role: hostile tracer. The storage-density claim is dead and stays dead (N physical
degrees of freedom ≤ N independent information degrees of freedom — assumed, not
re-litigated). The only question here: for each candidate mechanism, WHERE in the
chain

  physical state → transduction → signal conditioning → ADC (if any) → logic → result

does the relational operation (A∩B, B∩C, A∩¬C, …) actually happen?

## The boundary rule (applied uniformly)

- **SURVIVES** only if the relational *information* is created by physics before any
  digitization of individual variables. Downstream electronics may only
  threshold, record, or route.
- Thresholding / comparator-slicing / ADC-converting an **already-relational**
  analog quantity = legitimate readout, NOT relation-computation. A voltmeter
  reading is not "computing" the voltage. Defended explicitly per mechanism.
- 1-bit pulse logic (coincidence/veto units) on thresholded *events* = weak
  survive at best: no ADC, no stored program, no sequential evaluation — but the
  boundary is named and the weakness is priced.
- **REJECTED** if the physics yields independent per-variable values and the
  relation is assembled from those values downstream — in digital OR in analog.
  An analog multiplier fed by two already-digitized… no; fed by two per-variable
  analog voltages is borderline — traced case by case below.

Strength grades: STRONG (relation in primary transduction physics, no
per-variable values exist) / MODERATE (relation in dedicated pre-digitization
physics, some peripheral tax) / WEAK (relation split between physics and
readout threshold, or needs priced crutches). WEAK is still SURVIVES — barely.

---

## (a) Capacitive / geometric overlap sensing of patterned surfaces

**Chain.** State = voltage/charge pattern on patterned electrodes (or patterned
dielectric over electrodes). Transduction = electrostatic field solution between
drive pattern and sense-electrode geometry: the measured capacitance IS the
overlap integral of the two geometries. Conditioning = AC excitation +
capacitance-to-voltage / resonant-frequency readout (e.g., TI FDC-style LC-tank
shift). ADC/comparator → threshold → symbol.

**Where is the AND?** Two sub-cases, and they differ critically:

1. *Parallel (shunt) sensing* — sense electrode spans region A and region B;
   C_total = C_A + C_B. That is a SUM, not an AND. If this is followed by a
   threshold, the AND is completed at the comparator — the physics contributed
   only a sum. Verdict on this sub-case: the *jointness* is in the physics
   (one transducer, one quantity, both variables inseparable in it) but the
   *AND-decision* is at readout. Weakest survive; the relation is half-built
   by the field, half by the slicer.

2. *Series sensing* — patterns arranged so the signal path goes through C_A
   then C_B in series: C_total = (C_A·C_B)/(C_A+C_B). If either pattern is
   absent (open), C_total → 0; if both present, C_total ≈ min/2. This is a
   genuine soft-AND (product-like t-norm) and the multiplication-like combining
   happens in the electrostatic field solution — pre-digitization, inside the
   transducer, with no per-variable values anywhere. Thresholding the result is
   legitimate readout. **This is the version that survives.**

Digital calipers are the shipping existence proof that capacitance-between-
patterns is computed by geometry, not logic (0.01 mm resolution from patterned
electrodes, no per-feature digitization).

**Hostile notes.**
- The AND is graded/analog. Near-threshold states → bit errors from noise and
  mismatch (capacitor mismatch ~0.1–1% even on-chip; PCB-scale worse). SNR sets
  the usable predicate count, not wishful thinking.
- Negation (A∩¬C): there is no native "absent-pattern" capacitance. ¬C must be
  built as threshold-then-invert on a relational quantity, or as a
  complementary electrode geometry (a pattern that couples strongly only when
  the C-feature is missing — geometrically possible but it is a second,
  bespoke transducer, i.e., the ¬ is baked into hardware, priced in area).
- **Simultaneity (the kill zone):** two sense electrodes over the same shared
  region B *redistribute each other's fields*. Reader 1's measurement changes
  when Reader 2's electrode is present — mutual capacitance between sense
  electrodes is the same order as the sense capacitance unless guarded. The
  industry's standard answer to capacitive crosstalk is **time-division
  scanning** (activate one Tx–Rx pair, ground the rest — EDN/Azoteq design
  practice): i.e., the field's own solution to this problem is
  SERIALIZATION. Simultaneous operation is possible with driven shields/guards
  and frequency-division excitation, but guarding costs area and never reaches
  zero coupling; residual crosstalk must be calibrated out per reader-pair =
  metadata, the physical twin of the gate-metadata cost. Non-destructive: yes
  (fA–pA displacement currents, non-contact). Loading: each added reader adds
  parasitic C to the shared node → SNR degradation ~1/√(readers) at best.
- Verdict: **WEAK SURVIVE** — the relation genuinely lives in the field
  solution (series case), but multi-reader simultaneity is where this
  mechanism bleeds: crosstalk is fundamental, and the mature engineering
  answer is serialization.

## (b1) Optical / electronic coincidence detection (n-fold AND)

**Chain.** State = event streams (photon arrivals, detector pulses) on channels
A, B, C. Transduction = the events themselves (photodetection is the
transducer). "Conditioning" = discrimination (threshold to logic pulse) +
coincidence unit (output fires iff all inputs fire within window τ).
No ADC. No software.

**Where is the AND?** In the *temporal overlap of physical events*. The
coincidence unit does not know or store values of A and B; there are no
variables to digitize — only arrival times, and the AND is the physical fact
of co-arrival within τ. The unit merely registers it. **Survives cleanly.**
(Note: the discriminator threshold is per-channel, but it thresholds
*event presence*, not a variable value — the relational content,
simultaneity, is untouched by it.)

**Negation (A∩¬C):** anti-coincidence with veto input — standard nuclear
instrumentation since the 1950s (cosmic-ray vetoes). Chain: C's discriminated
pulses drive an inhibit line; output = A AND (no C within τ). The ¬ is
implemented as *absence of a physical event* gating the output — pulse-level,
no ADC, no stored program. Graded WEAK SURVIVE: the veto is dedicated
combinatorial pulse logic, one step downstream of pure physics, but it never
sees digitized variables.

**Simultaneity:** Reader 1 (A∩B) and Reader 2 (B∩C) share stream B → split it
(beamsplitter / electrical fan-out). Price is fundamental: each split halves
the event rate per reader (3 dB per 2-way split; no-cloning for photons,
charge-sharing/jitter for electrical fan-out buffers). No destruction of the
*source* (it keeps emitting; the "state" is the stream statistics). No
reader–reader crosstalk (independent detectors). No serialization (both units
run continuously). **YES — at the price of rate halving per split.** This is
the cleanest simultaneity story in the survey, and the price is a law, not an
engineering detail.

**Hostile notes.** Coincidence needs *event-based* dimensions. A static stored
state (charge pattern, magnetization) does not spontaneously emit event
streams; you must *drive* re-emission (pump the source), and the drive is an
active energy cost per query. Accidental coincidences scale as
R_A·R_B·τ — the window τ sets a noise floor. Timing jitter in fan-out buffers
widens τ → more accidentals. For a *memory* (static state, repeated queries),
coincidence is an awkward fit: it is a streaming/comms primitive, not a
storage-readout primitive.

Verdict: **SURVIVE (MODERATE)** — the AND is unambiguously in the physics;
simultaneity works with a fundamental rate-splitting tax; weak point is
negation (veto logic) and the mismatch to static-state storage.

## (b2) Fourier / holographic optical correlation

**Chain.** State = input light field (SLM / transparency) encoding the
substrate pattern. Transduction = free-space propagation through a lens
*is* the 2D Fourier transform (no computation — diffraction); matched filter
(hologram) multiplies in the Fourier domain; second lens inverse-transforms.
Output plane intensity IS the correlation function: every shift evaluated
simultaneously, in parallel, at light speed. Detection = photodiode/CCD array
(threshold = legitimate readout).

**Where is the relation?** Entirely in wave propagation + the recorded
interference pattern. Vander Lugt matched filter (1964). No variables are
digitized at any point before the output plane exists. **Survives.**
Negation: correlate against a complement template — the ¬ is baked into the
reader's physical structure (like a gate pattern), priced in filter
fabrication, not computed per query.

**Simultaneity:** volume holograms multiplex hundreds of gratings
(angular/wavelength multiplexing) — many matched filters interrogate the same
input beam simultaneously. Price: beamsplitting divides optical power per
filter; inter-grating crosstalk grows with multiplex count (a known,
measured limit); diffraction efficiency per hologram ~1/M. Non-destructive:
yes (readout photons don't disturb a fixed hologram; the SLM input is the
write path). No serialization. **YES, with crosstalk/power taxes that scale
with reader count.**

**Hostile notes.** It computes *correlation*, specifically. Mapping correlation
→ Boolean AND needs a threshold (fine) but also a correctly designed template
per predicate (fabrication/calibration metadata per reader). Table-sized
optics, vibration/alignment sensitivity, coherent source required.
Rewritable (photorefractive) media are slow — the "shared substrate" had
better be static or slowly varying, or the write path dominates.

Verdict: **SURVIVE (MODERATE)** — genuinely native relational readout, genuinely
parallel across multiplexed filters; taxed by power-division, crosstalk, and
bulk.

## (c) Resistive / conductance networks — Kirchhoff summation as native dot product

**Chain.** State = conductance matrix G_ij (programmed resistors/memristors)
× input voltages V_i on rows. Transduction = Ohm's law per cell (I = V·G)
*and* Kirchhoff's current law per column (I_col = Σ_i V_i·G_ij) — the column
wire *is* the summer; the summation exists in the physics of the node, with
no sequential accumulation. Conditioning = transimpedance amp. ADC (often
multi-bit) or comparator → result.

**Where is the AND?** Split, and this is the hostile point: KCL computes a
*sum*, not an AND. With binary V and programmed G, thresholding the column
current at ~1.5 unit-current yields AND-like behavior — but the AND-decision
is completed at the comparator/ADC. The physics contributed jointness (all
variables inseparably summed in one wire) but the *relational decision* is at
readout. The sum is "already-relational" (it is the linear relation), so
thresholding it is legitimate readout per the boundary rule — but this is the
weakest form of survival: the transducer computes Σ, the predicate needs a
decision on Σ. **WEAK SURVIVE**, and only for predicates reducible to
thresholded sums (AND, OR, MAJ, threshold functions — not XOR/XNOR without
differential tricks).

**Simultaneity:** this is the mechanism's best feature — multiple columns are
independent wires; reading all columns simultaneously IS the standard operating
mode (parallel VMM). Shared row B driving two columns: standard; price is IR
drop along the row (loading), managed by driver strength and wire sizing.
Negation: differential row pairs (C, ¬C) — standard practice; the inversion
is a single-bit driver-level operation, not digitize-then-compute. Sneak
paths: unselected cells leak current into column sums → *reader-reader
crosstalk through the substrate itself*; the fix is selectors (1T1R/1S1R),
taxed in area and power. **YES — best simultaneity story here; crosstalk is
real and the selector tax is mandatory, not optional.**

**Hostile notes (the kill criteria bite here).**
- *Energy advantage disappears after peripheral circuitry:* in real
  in-memory-computing chips the column ADCs dominate system energy (compute
  ~10 fJ; data conversion/transport 10–50× higher — cf. the MDPI SRAM-IMC
  result in the search). If each predicate needs a multi-bit ADC, the
  peripheral energy can exceed the conventional baseline's N-ADC + CMOS-logic
  cost. The honest version uses 1-bit comparators per predicate (~fJ), not
  ADCs — but then you only get threshold predicates.
- *Conventional compute-in-memory already does this:* SRAM CIM with
  multi-row activation computes bitline AND/NOR/XOR natively (Jeloka et al.
  2016 and a decade of follow-ups; also US10777259B1-class patents). Wired-AND
  across simultaneously-activated rows IS parallel relational readout of a
  shared substrate, in CMOS, in published silicon. The architecture is prior
  art; what differs is only the substrate material.

Verdict: **WEAK SURVIVE** for thresholded-sum predicates with comparator
readout; the simultaneity is real but the novelty is already owned by SRAM
compute-in-memory.

## (d) Magnetic / spintronic mechanisms

### (d1) Spin-wave interference majority gates
**Chain.** State = input spin-wave phases (0/π) launched by transducers.
Transduction = wave propagation + superposition in a magnonic waveguide: the
output phase IS the majority of input phases — the vote is counted by
interference, in the physics, with no per-variable values existing anywhere.
Detection = inductive antenna / magnetoelectric cell latching the output
phase (threshold-like, legitimate readout). NOT is native (π phase shift /
inverting port position).

**Where is the relation?** In the superposition. MAJ3 in ~1 ns over ~100s of
nm (Fischbacher et al., AIP Adv.). **Survives on the computation-location
test.**

**Simultaneity — attacked:** fan-out of 2 demonstrated in the inline majority
gate with +4F² area overhead and no microwave-domain reconversion
(Klingler/Fischbacher line); FO4 is *proposed, explicitly future work*.
Fan-out physics: splitting a spin wave divides amplitude; metallic
ferromagnets damp waves within micrometers (YIG reaches mm but is a
hard-to-integrate insulator grown at high temperature on GGG). Amplitude
division + damping = fan-out is the fundamental limiter, not an engineering
detail. Adjacent waveguides couple dipolarly → reader-reader crosstalk.
Multi-reader *simultaneous relational readout from one shared substrate* is
undemonstrated. **PROBABLY NOT at scale; in-principle for 2 readers.**

**Hostile notes.** Transduction I/O (microwave→spin→microwave, or
magnetoelectric) is where the collapse condition lurks: if getting signals
into and out of the magnetic domain costs more energy/latency than the
interference saves, the advantage dies at the boundary — and published
devices are still characterized with lab microwave gear, not integrated
peripherals. Research-stage; no dense array demo.

Verdict: **WEAK SURVIVE** — the MAJ/NOT is genuinely in the wave physics, but
fan-out physics caps multi-reader simultaneity and the I/O boundary is
unproven.

### (d2) Domain-wall logic — REJECTED (as relational-readout evidence)
DW gates (NOT via cusp, AND/MAJ via junction interactions) do compute in
DW-motion physics in principle. But: simultaneous multi-predicate readout
from a shared substrate is undemonstrated, and DW *readout* is per-variable
(MTJ/TMR sensing of wall position) — the moment you need the predicate
*values*, you are back to sensing individual variables. Nothing here
evidences the surviving claim beyond what (d1) already covers weakly.
**REJECTED** — computes in principle, but no multi-reader relational-readout
path; readout collapses to per-variable sensing.

### (d3) MTJ + TMR sensing + CMOS logic — REJECTED
This is textbook digitize-then-compute: MTJ resistance → sense amp → bit →
CMOS Boolean. The relation is assembled from digitized variables afterward.
**REJECTED** — it is the conventional baseline wearing a spintronic hat.

## (e) Memristor crossbars for relational readout

**Chain.** Identical to (c): programmed conductances × row voltages → KCL
column sums → TIA → ADC/comparator. The memristor adds non-volatility and
density, not a new computational primitive.

**Where is the relation?** Same split verdict as (c): Σ in physics,
predicate-decision at threshold. **WEAK SURVIVE** under the same conditions
(comparator readout, threshold predicates).

**Additional hostile point — serialization trap:** the memristor literature's
*stateful logic* families (IMPLY, MAGIC) perform logic by sequential
voltage pulses (V_cond then V_set, …) — they are explicitly SERIAL in time,
often multiple cycles per gate, and destructive to inputs in some variants.
Any ATMAN reading built on stateful memristor logic inherits serialization
and input destruction, directly violating the hypothesis. **Stateful
memristor logic: REJECTED for the simultaneity claim.** Only the parallel
analog VMM readout mode survives (weakly).

**Hostile notes.** Memristor variability (device-to-device, cycle-to-cycle)
and drift inject analog noise into every column sum → BER floor that must be
measured, not assumed; write endurance/energy is irrelevant for a
read-mostly relational substrate but read-disturb at high row counts is not
zero. Selector tax (sneak paths) same as (c).

Verdict: **WEAK SURVIVE** (parallel analog readout mode only);
**REJECTED** for stateful/IMPLY/MAGIC sequential logic variants.

## (f) Analog interference / correlation — mixers, Gilbert cells, SAW, matched filters

### (f1) Gilbert-cell / analog multiplier as AND
**Chain.** State = two analog voltages (each from its own front-end sensing
one variable). Transduction-of-relation = transistor nonlinearity: the
differential pair's output current ∝ product of inputs. For unipolar binary,
product = AND. No digitization anywhere before the product exists.

**Where is the relation?** In the device physics, pre-digitization —
survives the letter of the test. But note the weakness honestly: the two
input voltages each represent *single variables* produced by their own
transducers; the multiplier is a *second* stage that combines per-variable
signals. It is not digitize-then-compute, but it is also not "the primary
transducer embodying the relation" — it is a dedicated analog compute stage.
**WEAK SURVIVE**, and the simultaneity math is unforgiving: sharing variable
B across two multipliers needs analog fan-out → buffers (power, noise,
kickback) or degraded bandwidth; each reader needs its own multiplier +
front-ends, so area/power scale with predicate count, and there is no
substrate-sharing win at all — this is just analog logic, i.e., conventional
computation in continuous time. It survives the computation-location test and
contributes nothing to the architectural claim.

### (f2) SAW convolver / acoustic matched filter
**Chain.** State = two counter-propagating surface acoustic waves (signal ×
reference). Transduction = nonlinear elastic interaction in the substrate:
the output IS the convolution/correlation, computed by wave physics as they
pass through each other (1970s spread-spectrum prior art — D. P. Morgan
review; JPH0629947A-class patents). Taps along the propagation path read
multiple correlation lags **simultaneously by construction**.

**Where is the relation?** In the nonlinear wave interaction — no variables,
no digitization, predates the hypothesis by 50 years. **SURVIVE (MODERATE)**
for correlation-type relations. Sharing: multiple taps = multiple readers on
the same waves with no splitting loss (taps sample the field). **YES.**

**Hostile notes.** Computes convolution/correlation, not Boolean AND (needs
threshold + template design, same as (b2)). It is a *streaming signal*
primitive, not a static-memory readout — the "substrate" is two live waves,
so a stored state must be continuously re-launched. Prior art is
decisive (military spread-spectrum, 1970s).

### (f3) Analog matched filter (delay–multiply–integrate)
Same class as (f2), lumped-element version: correlation via tapped delay
line, multipliers, integrating capacitor. Relation in the physics;
simultaneity across taps natural. **WEAK–MODERATE SURVIVE**; same
streaming-not-storage caveat.

## (g) Other mechanisms

### (g1) Quantum joint / parity measurement — the strongest in-principle fit
**Chain.** State = entangled qubits. Transduction = projective measurement of
a joint observable (e.g., X⊗X): the outcome IS the parity/correlation, and —
crucially — the individual variable values *provably do not exist* to be
digitized (single-qubit marginals are maximally mixed). There is no
classical chain in which the relation could "actually" be computed afterward;
the computation-location test is passed structurally, not marginally.
Repeated QND parity measurement exists (stabilizer readout in QEC):
non-destructive, repeatable. Multiple *commuting* parity operators measurable
simultaneously. Fan-out = ancilla overhead.

**Where is the relation?** In the measurement postulate applied to an
entangled state. **STRONG SURVIVE** — the only candidate that passes
hostilely rather than barely.

**What kills it (practicality, not the location test):** entanglement is a
consumable resource requiring cryogenics, coherence times, and error
correction whose overhead dwarfs the readout; scaling to many predicates
needs many ancillas/qubits; and the Holevo bound preserves the N-bits limit
(the density claim stays dead). It proves the hypothesis is *physical*, not
that it is *buildable*.

### (g2) Neuromorphic LIF coincidence (electronic cousin of (b1))
Leaky integrate-and-fire neuron: membrane potential integrates coincident
input spikes; threshold crossing = AND in membrane physics. Spikes are 1-bit
events, not digitized values; fan-out via synapses is designed-in
(Loihi/TrueNorth do exactly this). **WEAK SURVIVE** — adds nothing beyond
(b1) except silicon integrability; the "neuron" is a coincidence detector
with a membrane.

### (g3) Photonic MZI meshes — REJECTED (for relational readout)
Mach–Zehnder meshes compute *linear* transforms natively (optical VMM) —
same class as (c), no new relational primitive, and Boolean predicates still
need thresholding. No independent survival. **REJECTED** as a distinct
candidate (fold into (c)).

---

## Simultaneity matrix: A∩B, B∩C, A∩¬C on ONE substrate, AT THE SAME TIME

| Mechanism | Destructive? | Loading / fan-out | Reader–reader crosstalk | Serialization? | Hidden compute? | Simultaneous? |
|---|---|---|---|---|---|---|
| (a) capacitive series-AND | No | Parasitic C per reader; SNR ↓ | **YES — field redistribution**; industry answer is scan-serialization | Avoidable w/ guards+FDM, taxed | Threshold+invert for ¬ | **Marginal** — physics allows, crosstalk is the tax |
| (b1) coincidence | No (source persists) | Rate halves per split (law) | No (independent detectors) | No | Veto pulse logic for ¬ (named) | **YES — cleanest** |
| (b2) holographic | No | Power ÷ M filters | Inter-grating crosstalk ↑ with M | No | Complement template (in reader HW) | **YES — taxed** |
| (c)/(e) KCL crossbar | No (low-V read) | IR drop on shared rows | Sneak paths (selectors mandatory) | No | Comparator completes predicate | **YES — best-understood** |
| (d1) spin-wave | No | Amplitude ÷ fan-out + damping | Dipolar coupling | No | — | **~2 readers max demonstrated** |
| (d2) DW | n/a | n/a | n/a | n/a | per-variable MTJ readout | **NO (rejected)** |
| (f1) Gilbert | No | Buffers needed per fan-out | Kickback | No | — | YES, but no substrate-sharing win |
| (f2) SAW | No | Taps sample field, ~lossless | Minimal | No | — | **YES (taps)** |
| (g1) quantum parity | No (QND) | Ancilla overhead | Commuting only | No | None possible | **YES in principle** |

**The shared-variable contention, stated bluntly:** B feeding two readers
always costs *something* — rate (b1), power (b2), IR drop (c/e), amplitude
(d1), buffer power (f1), field distortion (a). Nothing shares for free. The
question is never "is there a cost" but "does the cost kill the advantage" —
and the answer depends on predicate count (next section).

## Scaling laws (the hostile arithmetic)

- **Latency vs #predicates P:** native-parallel mechanisms are O(1) in P —
  but so is the conventional baseline *after* its N reads (combinational CMOS
  evaluates all P predicates in parallel in ~10s of ps). The honest race is
  not "serial vs parallel predicates"; it is **N full variable reads + free
  logic vs P relational front-end reads**. Latency advantage exists only if
  one relational read is faster than N variable reads.
- **Energy per predicate:** front-end drive + sensing + 1-bit comparator
  (~fJ) can beat N ADC conversions — *if* you use comparators. The moment a
  mechanism needs multi-bit ADCs per predicate (real IMC chips do), peripheral
  energy dominates and the advantage inverts. Comparator-only operation
  restricts you to threshold predicates. This is a hard tradeoff, not a
  tunable: precision per predicate vs energy per predicate.
- **# simultaneous readers:** capped by fan-out physics per mechanism (rate,
  power, amplitude, field distortion). No mechanism shows P ≫ 10 simultaneous
  relational readers on one substrate without the tax dominating.
- **Area / wiring:** each predicate needs its reader hardware near its
  variables; wiring scales ~Σ arities in the worst case. The crossbar is the
  best case (N+P wires for N×P coverage) — which is exactly why SRAM CIM
  already owns this scaling story.
- **Calibration/metadata:** every analog reader needs offset/gain/crosstalk
  coefficients; every template/filter needs fabrication; every veto needs
  timing alignment. This is the physical twin of the K²log3 gate-metadata
  cost from the software accounting — it does not disappear in hardware, it
  changes units (bits → trim registers, guard rings, calibration time).
- **Noise/SNR/BER:** analog relational quantities have finite SNR; graded
  ANDs (a, c, e) err near threshold; accidentals (b1: R_A·R_B·τ); crosstalk
  (a, b2, c/e, d1); device mismatch/drift (c/e). No mechanism was found with
  a BER story better than "comparable to a sense amp + comparator," i.e.,
  the conventional baseline's readout fidelity, because most of them *end*
  in a sense amp + comparator.

## Conventional baseline (the one to beat)

Read each of the N variables once (N sense-amp/ADC operations), then evaluate
all P predicates in parallel combinational CMOS (gate delay ~10–50 ps,
~fJ/gate — effectively free next to the reads). Baseline cost ≈ **N reads**.
ATMAN cost ≈ **P relational front-ends + P comparators + calibration**.
ATMAN wins on energy/latency **iff P relational reads < N full reads** —
i.e., few predicates over many variables, or per-variable readout unusually
expensive (destructive, quantum, cryogenic). If P ≥ N, ATMAN needs *more*
converters than the baseline and loses on the converter count alone. The
"reduced downstream logic" claim is nearly empty: downstream CMOS logic was
already ~free; the expensive part was always the reads, and ATMAN does not
reduce the number of reads unless P < N.

## Kill criteria — which ones fire

1. *Relation actually in downstream logic* → FIRES on (d3), (g3),
   stateful-memristor-logic (e-variant), and would fire on any
   digitize-then-compute implementation. The survivors pass only by keeping
   the relation in pre-digitization physics.
2. *Readers require serialization* → FIRES on stateful memristor logic;
   THREATENS (a) (industry practice is scan-serialization for exactly the
   crosstalk reason); does not fire on (b1), (b2), (c/e), (f2), (g1).
3. *Simultaneous readers substantially disturb one another* → THREATENS (a)
   (field redistribution), (b2) at high M, (c/e) without selectors, (d1)
   beyond fan-out 2. Managed, never zero.
4. *Energy/latency advantage disappears after peripherals* → THREATENS every
   analog survivor the moment multi-bit ADCs or active fan-out buffers enter;
   the comparator-only restriction is the defense, and it narrows the
   predicate class.
5. *Interconnect/calibration cost eliminates the advantage* → THREATENS (a)
   (guards, FDM), (b2) (bulk optics), (d1) (transduction I/O); least bad in
   (c/e) crossbar — which is prior art.
6. *Compute-in-memory already performs the same operation equivalently* →
   **FIRES on (c)/(e)**: SRAM CIM multi-row wired-AND is parallel relational
   readout of a shared substrate in published silicon (Jeloka et al. 2016;
   US10777259B1 family). The substrate differs; the architecture does not.
7. *Known prior art already implements the architecture* → FIRES on (b1)
   (nuclear coincidence/anti-coincidence, 1950s), (b2) (Vander Lugt 1964),
   (f2) (SAW convolvers, 1970s), (a) (capacitive encoders), (c/e) (SRAM CIM,
   memristor VMM — Yao et al., Nature 2020).

## What remains genuinely novel, if anything

Almost every *component* has prior art. What has no single prior-art
embodiment is the *combination*: a passive/shared memory substrate whose
transducer geometry *is* the gate pattern, interrogated by multiple
simultaneous relational readers as the normal read path (not as an
accelerator attached to a memory). But "no single prior-art embodiment"
is a thin novelty: SRAM compute-in-memory is that combination with the
substrate made of SRAM cells, and the only remaining distinction is the
substrate material and the claim that relational readout is the *primary*
(rather than accelerated) access mode. That is a packaging/architectural
distinction, not a physics distinction. A patent examiner would cite
Jeloka + a capacitive-encoder reference and reject.

## What claim survives after all falsification

1. **Physics permits it.** (g1) proves it structurally; (b1), (b2), (f2)
   prove it practically for their native relations. The hypothesis is not
   unphysical.
2. **The advantage window is narrow and specific:** P predicates ≪ N
   variables, threshold-class predicates, comparator-only readout, and a
   substrate whose per-variable readout is expensive. Inside that window:
   fewer conversions, O(1) predicate latency, near-zero downstream logic.
   Outside it (P ≥ N, arbitrary Boolean, ADC-grade precision), the
   conventional baseline (N reads + free CMOS logic) wins, and SRAM
   compute-in-memory already occupies the most favorable territory.
3. **Everything else is dead or taxed:** no capacity gain (assumed dead,
   confirmed by every mechanism — Holevo, DPI, and fan-out laws all agree);
   no universality (each mechanism natively computes *its* relation;
   reconfigurability reintroduces the metadata cost in trim registers,
   templates, and guard structures); no scaling story better than the
   crossbar's, which is prior art.
4. The surviving claim is therefore: **a niche physical-readout energy/
   latency advantage for few simultaneous threshold-relational queries over
   a shared substrate whose individual variables are costly to read** —
   falsifiable by the single-channel benchmark (one physical reader whose
   output *is* the predicate, no logic stage, measured against read-plus-
   AND), and already partially anticipated by compute-in-memory prior art.

That is what survives physics. It is real, small, and mostly already
invented in pieces.
