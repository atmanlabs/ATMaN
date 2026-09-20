# PROJECT ATMAN — HARDWARE RELATIONAL READOUT FALSIFICATION
Date: 2026-09-19. Stance: hostile. Method: three independent research briefs
(prior-art hunt, mechanism tracing, scaling+baseline) in `research/`.
The storage-density claim is dead and stays dead (assumed: N physical dims ≤ N
independent information dims). This report attacks only the surviving claim:
transducers embodying relational predicates (A∩B, B∩C, A∩¬C) read in parallel
from one shared substrate, winning on latency/energy/logic — not capacity.

## A. Strongest physical implementation candidate
Coincidence detection (n-fold AND in event-timing physics). The AND is the
physical fact of co-arrival within window τ; the unit merely registers it —
no per-variable values exist to digitize, no ADC, no stored program.
A∩¬C via veto/inhibit line is 1950s nuclear instrumentation. Cleanest
simultaneity story of any candidate: independent detectors, no crosstalk,
price paid openly as rate-halving per fan-out split (conservation, not a bug).
Honest grading: it is also the most thoroughly prior-art candidate — which is
why it survives the physics test and dies the novelty test in the same motion.
For the cylinder-embodied version of the idea, series-capacitive overlap
sensing is the honest transducer (soft-AND in the electrostatic field solution,
pre-digitization), graded WEAK: multi-reader field redistribution is
fundamental, and the industry's mature answer to capacitive crosstalk is
time-division scanning — i.e., serialization.

## B. Simplest buildable experiment
Three controllable event channels A, B, C (pulse generators driving LEDs +
photodiodes, or direct electrical pulses). Reader 1 = A∩B coincidence unit,
Reader 2 = B∩C coincidence unit, B shared via electrical fan-out — both live
simultaneously. Software ONLY timestamps/counts raw reader outputs; it may not
see A, B, C individually. Second phase: add Reader 3 = A∩¬C via C-driven veto
line on a third coincidence unit. Bench cost is trivial (discriminators +
coincidence units are textbook nuclear-instrumentation modules). The capacitive
variant (patterned copper electrodes, series geometry, FDC2214-class CDC
readout, two readers sharing one patterned region) tests the cylinder-relevant
crosstalk question instead — run it if the goal is killing the mechanical
embodiment rather than the abstract claim.

## C. Predicted measurements
- It will WORK for 2–3 readers — and that is the trap. Coincidence rates per
  reader halve per 2-way split of B (measured: R_true/d, accidentals fixed ⇒
  per-reader SNR ∝ 1/d).
- Capacitive variant: reader–reader crosstalk measurable as mutual
  capacitance same order as sense capacitance without guards; SNR degrades
  ≥1/√(readers); driven guards + frequency-division excitation recover
  simultaneity at area/power cost — the tax itemized, not wished away.
- Energy: no crossover exists. Crossover condition E_reader < (N/P)·E_read +
  k·E_and demands ≤ ~30 fJ/reader at P≈N and ≤ ~0.15 fJ (three gate toggles)
  at P≫N; measured front-ends: 0.5–240 pJ — missed by 10²–10⁴×, gap widening
  with P/N.
- Latency: conventional = one parallel N-bit row read (~1–3 ns) + ~10s of ps
  combinational logic. Relational front-end: capacitive 20 µs–500 ns,
  coincidence 1–10 ns. The "sequential reads" premise is false — nobody
  serializes bit-by-bit.
- Worked example (N=64, k=3, P=256): conventional ~1–3 pJ/query at ~2 ns;
  ATMAN optimistic ~130 pJ at 10–500 ns; realistic capacitive ~61 nJ at 20 µs.
- BER: analog predicates err near threshold with no restoration; digital
  baseline BER ≈ 0 after sense-amp latching. The cleaner you want the
  predicate, the more conventional the reader becomes.

## D. Conventional baseline
(i) Memory + Boolean: read all N variables once (one parallel row access),
evaluate all P predicates in parallel combinational CMOS (logic ~free next to
reads). Cost ≈ N reads. ATMAN cost ≈ P relational front-ends + P comparators
+ calibration. ATMAN wins only if P < N — few predicates, many variables —
or per-variable readout is unusually expensive (destructive, quantum,
cryogenic). (ii) Compute-in-memory (the stronger baseline): Ambit embodies
AND/OR/NOT in the DRAM sense amp via triple-row activation (<1% area,
32×/35× gains); TCAM evaluates masked predicates on matchlines in one cycle;
SRAM-CIM multi-row activation does wired-AND relational readout in published
silicon. CiM shares one sense amp per bitline; naive ATMAN needs one
front-end per predicate — strictly worse amortization. Against CiM there is
no remaining performance claim, only packaging — and the packaging loses.

## E. Kill criteria (predefined — evaluated)
1. Relation actually in downstream logic → FIRES on any digitize-then-compute
   implementation (most "analog AI" demos, MTJ+TMR+CMOS, stateful
   IMPLY/MAGIC). An ATMAN demo with per-reader ADC + digital AND is
   self-falsifying by this criterion.
2. Serialization → THREATENS capacitive (industry practice IS
   scan-serialization); FIRES on stateful memristor logic. Demo must show
   true simultaneity or die here.
3. Reader–reader disturbance → substantial by d≈10–100 readers/variable
   (charge/current division, parasitics, crosstalk, accidentals, sneak
   paths). Quantified, not hand-waved.
4. Peripherals erase the advantage → CONFIRMED by crossover math (§C). No
   feasible E_reader in any measured technology.
5. Interconnect scaling → P·k analog wires; 10³–10⁶× area per predicate vs
   digital gates. Conservation-limited fan-out (2.4 of scaling brief) kills
   the scaling claim before peripherals are counted.
6. CiM equivalence → CONFIRMED (Ambit, TCAM, SRAM-CIM — §D).
7. Prior art → CONFIRMED, twice over at 5/5 (§F).

## F. Relevant prior art (function-searched)
- TCAM — parallel masked-compare relational readout, matchline = predicate
  output. Shipping in routers for decades. 5/5.
- Analog CAM, HP Labs (Li et al., Nature Commun. 2020, DOI
  10.1038/s41467-020-15254-4; US 10,847,238 / 10,896,731 / 11,551,771) —
  analog range predicates, no ADC in the predicate path. 5/5.
- Ambit (Seshadri et al., MICRO 2017) — AND/OR/NOT in the DRAM sense amp.
- SRAM CIM multi-row bitline logic (Jeloka et al., JSSC 2016+; US10777259B1).
- Memristor/Flash crossbar VMM (Mythic; IBM HERMES) — Kirchhoff-native
  parallel relational readout, linear class.
- In-sensor computing (Mennel et al., Nature 2020) — transducer IS the
  classifier, zero digitize-then-compute pipeline.
- Spin-wave majority + frequency-division multiplexing (Talmelli et al.,
  arXiv:1908.02546) — different logic functions, same substrate, same time.
- SAW convolvers (1970s), Vander Lugt optical correlator (1964),
  wired-AND/wired-OR/domino logic (ancient).
Honest rejections logged: particle-physics coincidence triggers and
fingerprint sensors fail the no-digitize-then-compute test — the kills above
are the real ones.

## G. What remains genuinely novel, if anything
Nothing functional. Every element — transducers embodying predicates, many
different predicates sharing one substrate simultaneously, no
digitize-then-compute — is built and published (TCAM/aCAM) or
lab-demonstrated (spin-wave FDM, in-sensor). What is new is only the
mechanical form factor: counter-rotating patterned cylinders with
non-contact readers. That is packaging, not a hypothesis — and it inherits
every weakness (calibration, crosstalk, wiring) with none of CMOS's density.
Genuinely Michael's own and untouched by this report: the ATMAN cognitive
architecture (TSC/PSC/WFC, the Judge, Capture→…→Memory-Update loop) —
software/architecture, which this falsification does not attack.

## H. What claim survives after all falsification
One narrow, honest statement: **for a fixed set of predicates evaluated
continuously at the sensor edge, where digitization is infeasible or
prohibitively expensive, a dedicated analog relational transducer can beat
digitize-then-compute.** That is in-sensor computing — a known, legitimate
niche, and the reason coincidence counters and correlators exist. It confers
no capacity, no general energy/latency advantage over memory+logic or CiM,
and it scales only to small P before fan-out conservation kills it.
**As an architecture for general relational readout, the hypothesis does not
survive.** Recommended disposition: close the PUNIT hardware-readout line as
falsified; keep the ATMAN cognitive architecture work, which was never
implicated.
