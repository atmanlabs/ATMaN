# ATMAN Physical Relational Readout — Hostile Scaling & Baseline Brief
**Analyst stance:** hostile. The storage-density claim is dead and stays dead.
This brief attacks only the surviving claim: that transducers embodying relational
operations (A∩B, B∩C, A∩¬C, …) over one shared substrate can win on parallel
retrieval, latency, downstream logic, or energy per query.

## 0. Ground rules
- N physical state dimensions ⇒ at most N independent information degrees of
  freedom. Never confused with parallel correlated outputs.
- The ATMAN side carries **all** of its peripheral circuitry: sensor arrays,
  excitation, per-reader conditioning, comparators/ADCs, calibration hardware,
  selector/addressing for configurable predicates, wiring, shielding.
- "The sensor is the computer" is tested literally: if the relational operation
  occurs after digitization, the candidate is rejected as evidence.
- Numbers below are grounded in published measurements (sources at end);
  where extrapolation is used it is labeled as such.

## 1. Reference model
- N state variables (physical quantities: voltage, charge, magnetization…).
- P relational predicates (readers), average fan-in k variables per predicate.
- Average fan-out per variable: **d = P·k / N** readers hanging off one variable.
- The interesting regime for the claim is P ≫ N (many relations, few dims).

## 2. JOB 1 — Scaling laws

### 2.1 Latency vs P
- ATMAN: all readers run concurrently ⇒ latency ≈ T_transduce + T_settle +
  T_compare, **O(1) in P**. Mechanism-typical values:
  - capacitive overlap (CDC-class front-end): excitation + integration,
    20 µs (50 kS/s, 8 aF resolution, ams PCap04) down to ~50–500 ns for
    aggressive custom front-ends at degraded SNR;
  - coincidence/timing: coincidence window + discriminator, ~1–10 ns;
  - resistive crossbar column: RC settling, ~1–10 ns.
- Conventional: one parallel N-bit row read (SRAM random access ~0.2–2 ns;
  Renesas 65 nm record 1.8 ns) + combinational Boolean depth ⌈log₂k⌉ × ~5–15 ps
  FO4 stage ⇒ **~1–3 ns total, O(1) in P as well** (predicates evaluate in
  parallel combinational logic).
- **The "sequential reads" premise is false.** Nobody serializes bit-by-bit;
  conventional memory already reads the full N-bit state in one parallel row
  access. ATMAN's latency is O(1) in P — and so is the baseline's. On absolute
  numbers the baseline is typically 5×–10,000× faster because analog settling +
  comparison is slower than a row read + a few gate delays.

### 2.2 Energy per predicate
Per query, honest accounting:
- ATMAN: E_A = P·(E_xducer_fe + E_cmp) + N·E_drive(d)
  - E_xducer_fe (relational transducer front-end): PCap04-class ≈ 240 pJ/
    conversion/reader (12 µW @ 50 kS/s); optimistic integrated custom
    front-end ≈ 0.5–10 pJ/reader; coincidence discriminator+TDC ≈ 10s of pJ.
  - E_cmp (1-bit comparator): bounded below by ADC step energy; hero Walden
    0.4 fJ/conv-step ⇒ ~1–10 fJ realistic floor, typical 10–100 fJ.
  - E_drive(d): holding SNR under fan-out d (see 2.4).
- Conventional: E_C = N·E_read + P·(k−1)·E_and
  - E_read: 45 nm SRAM ≈ 0.1 pJ/bit (CACTI rule ≈ 6 pJ per 64-bit row read);
    7 nm ≈ 0.02–0.05 pJ/bit.
  - E_and: minimum inverter toggle in FO4 chain: 32 nm ≈ 0.13–0.45 fJ;
    extrapolated 7 nm ≈ 0.02–0.1 fJ per gate. A 2-input AND ≈ same order.
- **Crossover condition:** E_A < E_C ⟺
  **E_reader < (N/P)·E_read + k·E_and**
  - At P ≈ N: need E_reader ≲ E_read + k·E_and ≈ 10–50 fJ. Measured analog
    relational front-ends miss by 10²–10⁴× (0.5 pJ–240 pJ vs ~30 fJ budget).
  - At P ≫ N (the regime the claim needs): need E_reader < k·E_and ≈ 0.15 fJ
    — roughly the energy of *three digital gate toggles*. No measured analog
    transducer+front-end+comparator is within four orders of magnitude, and
    the gap **widens** as P/N grows. There is no crossover in any measured
    technology. The per-predicate energy "advantage" never exists after
    peripherals.

### 2.3 Maximum simultaneous readers
Hard ceiling is not reader count — it is fan-out loading (2.4) and wiring
(2.7). Readers are cheap to draw; they are expensive to feed.

### 2.4 ★ THE DOMINANT SCALING KILLER: conservation-limited fan-out ★
Each of the N variables feeds d = P·k/N parallel readers. Every reader must
extract an independent, suprathreshold copy of each variable's signal. Signal
energy is conserved — it cannot be photocopied for free:
- **Current/charge-mode** (coincidence photons, crossbar currents, capacitive
  charge sharing): the signal itself divides. Per-reader amplitude ∝ 1/d ⇒
  amplitude-SNR ∝ 1/d ⇒ recovering the original SNR costs **×d² in integration
  time or ×d in drive energy**.
- **Voltage-mode with high-impedance buffers**: amplitude is preserved, but
  each reader adds input capacitance d·C_in loading the source. Settling time
  τ = R_src·d·C_in grows ×d; holding latency constant demands driver power ×d;
  alternatively each of the d buffers burns its own amplifier power — total
  analog power ∝ d regardless.
- **Universal form:** total signal-related cost (energy × time product) scales
  ≥ linearly with fan-out d. You choose whether to pay in power, latency, or
  SNR — conservation always collects.
- Consequence: the parallelism's gains are **exactly canceled by physics
  before peripherals are even counted**. At d ≈ 10–100 readers per variable
  (reached already at P ≈ 300–3000 for N = 64, k = 3), either SNR collapses
  below usable BER or drive/integration cost explodes past any plausible
  budget. This kills the *scaling* claim itself, not just the comparison.
- Per-reader peripheral energy (2.2) is then the executioner in the baseline
  comparison; interconnect (2.7) is the area executioner at large P.

### 2.5 SNR and noise accumulation
- Per-reader SNR degrades ≥ 1/d (amplitude) under fan-out; correlated
  excitation noise and substrate crosstalk add coherently across readers that
  share variables — the shared-variable architecture *correlates* the noise
  exactly where the predicates need independence of errors.
- Capacitive: measured noise floors 8 aF resolution (PCap04 @ 50 kHz),
  0.3 fF @ 100 S/s (FDC2214). Parasitic capacitance from d readers' wiring
  appears directly in the denominator of every reader's SNR.
- Coincidence: accidental coincidence rate scales as the product of singles
  rates × window — splitting one photon stream among d coincidence channels
  (beamsplitters) divides true coincidences per channel by d while dark-count
  accidentals stay fixed ⇒ per-reader SNR ∝ 1/d.

### 2.6 Error rate
- Analog predicate outputs near threshold ⇒ soft errors with no restoration.
  Getting digital-clean predicates requires per-reader regeneration
  (sense-amp-style latching) — which is precisely the "conventional"
  circuitry the claim was supposed to eliminate. Irony noted: the cleaner you
  want the predicate, the more conventional the reader becomes.
- Digital baseline BER after restoration is effectively zero; analog BER is
  set by SNR and drifts with temperature/aging (see 2.8).

### 2.7 Physical area and wiring/interconnect
- Wiring: each reader connects to its k variables ⇒ **P·k wires** routed over
  the substrate, plus shielding for capacitive/pickup-sensitive mechanisms.
  P = 10⁴, k = 4 ⇒ 40,000 analog wires; P = 10⁶ ⇒ 4×10⁶. Routing congestion
  scales superlinearly; analog wires cannot be minimum-pitch the way digital
  can (crosstalk, shielding).
- Area per reader: transducer electrodes + front-end + comparator ≈
  10²–10⁵ µm² depending on mechanism/node vs. a digital AND gate ≈ 0.05–0.2 µm².
  **Per-predicate silicon area is ~10³–10⁶× worse** before wiring.
- For configurable predicates, add selector multiplexers per reader input:
  series resistance/capacitance that further degrades 2.4/2.5.

### 2.8 Calibration burden
- P analog readers × (offset, gain, threshold) coefficients, all drifting with
  temperature, aging, supply. The capacitive-sensor industry ships per-channel
  auto-calibration (AD7147-class) precisely because uncalibrated analog
  readouts drift into uselessness — that calibration hardware and its
  background power are part of E_reader.
- Digital baseline: zero calibration. Burden scales strictly with P and is a
  system-level tax at P ≳ 10⁴.

### 2.9 Metadata/addressing overhead
- Fixed predicates: zero metadata, zero flexibility — at which point the fair
  comparison is a fixed-function digital ASIC (which just uses gates).
- Configurable predicates: P·k·⌈log₂N⌉ configuration bits + selector
  transistors + configuration SRAM + its own read energy. This is the T4
  gate-metadata cost (K²log3-class) re-entering through the physics door, in
  silicon instead of in the model.

### 2.10 Which cost kills first — summary
| Scaling regime | First killer |
|---|---|
| P/N growing, physics level | **Fan-out loading (2.4)** — SNR collapse or ×d² time / ×d power by d≈10–100 |
| vs. conventional baseline, any P | **Per-reader peripheral energy (2.2)** — no crossover exists; gap widens with P/N |
| Large P, physical build | **Interconnect/wiring (2.7)** — P·k analog wires + shielding; area 10³–10⁶× per predicate |
| Long-lived deployment | **Calibration drift (2.8)** — P coefficient sets, background recal power |

## 3. JOB 2 — Strongest conventional baselines

### 3.1 Baseline (i): conventional memory + Boolean logic — worked example
N = 64 state bits, k = 3 avg fan-in, P = 256 predicates, 7 nm-class numbers:
- **Conventional:** one 64-bit row read ≈ 1–3 pJ (0.02–0.05 pJ/bit) +
  256 × 2 AND gates × 0.05 fJ ≈ 0.03 pJ ⇒ **≈ 1–3 pJ/query, ~1–3 ns.**
  Addressing/decode included in the access energy. Predicates evaluate in
  parallel combinational logic — nothing is serialized.
- **ATMAN optimistic** (hero comparator 10 fJ + minimal 0.5 pJ front-end,
  ignoring fan-out drive): 256 × 0.51 pJ ≈ **130 pJ/query, ~10–500 ns**
  ⇒ ~40–130× worse energy, ~5–250× worse latency.
- **ATMAN realistic capacitive** (PCap04-class 240 pJ/reader): ≈ **61 nJ/query,
  ~20 µs** ⇒ ~20,000× worse energy, ~10,000× worse latency.
- Adding fan-out drive (d = 12): conventional unchanged (read once, fan out
  digitally for free); ATMAN pays ×d in drive power or ×d² in integration.
- **Verdict on (i): the baseline wins on energy by 10¹–10⁴× and on latency by
  10⁰–10⁴× depending on mechanism optimism. The claimed advantages
  (parallel retrieval, fewer sequential reads, less latency, less logic, less
  energy) are all false against a real baseline — because the baseline
  already reads in parallel and its "downstream logic" costs ~10⁻¹⁶ J/gate.**

### 3.2 Baseline (ii): compute-in-memory — the claim, already industrialized
The surviving hypothesis — "the transducer embodies the relation, no
post-digitization logic" — is the textbook operating principle of
compute-in-memory, published and shipping-adjacent for years:
- **Ambit (Seshadri et al., MICRO 2017):** triple-row activation in commodity
  DRAM; three cells share charge on the bitline and the **sense amplifier
  itself embodies MAJ/AND/OR**; NOT via the sense amp's inverters. <1% chip
  area overhead, no interface change, 32× performance / 35× energy vs. the
  conventional baseline on bulk bitwise ops. This is Reader→A∩B with the
  transducer as the computer, in a shipping memory technology, nine years ago.
- **SRAM CiM (multi-wordline):** activating multiple wordlines computes
  wired-AND/wired-NOR directly on the bitline; 7 nm macros at 351 TOPS/W
  (≈ 2.85 fJ per binary op); full CiM macros with ADCs still fJ–pJ per op.
- **TCAM:** P masked-equality predicates over N shared search lines evaluated
  **simultaneously**; the matchline *is* the relational output — predicate-
  parallel relational readout over a shared substrate, shipping for decades.
  This is the closest architectural match to the ATMAN reader array, and it
  predates it by ~30 years.
- **Crossbar VMM:** the column current *is* the dot product (linear relation);
  core ~189–316 fJ/MAC **excluding** DAC/ADC/peripherals — the literature's
  own warning that peripherals dominate analog compute.
- Crucial amortization difference: CiM shares **one sense amp per bitline**
  across the whole array; naive ATMAN needs **one front-end per predicate**.
  CiM's peripheral amortization is strictly better. ATMAN-as-drawn is a
  worse-packaged rediscovery of CiM with inferior amortization.
- **Verdict on (ii): the hypothesis is already implemented, with better
  peripheral economics, in Ambit/SRAM-CiM/TCAM. There is no remaining
  performance claim against this baseline — only a packaging difference, and
  the packaging loses.**

## 4. Prior art dangerously close (functional search, not name search)
1. TCAM — parallel masked-compare relational readout, matchline as predicate.
   Shipping for decades.
2. Ambit (MICRO 2017) — sense amplifier embodies AND/OR/NOT via charge
   sharing. <1% area. 32×/35× gains.
3. SRAM compute-in-memory, multi-WL bitline logic (Jeloka et al. JSSC 2016+).
4. Memristor crossbar VMM — transducer-computed relation (linear).
5. Wired-AND / wired-OR, domino dynamic logic — relation embodied in the wire.
   Ancient.
6. Coincidence counting (quantum optics, PicoQuant-class) — native n-fold AND
   via timing.
7. Vander Lugt optical correlator (1964) — native 2D correlation at light speed.
8. Holographic associative memory — parallel correlation readout.
9. In-sensor / focal-plane processing — sensor embodies computation at the edge.

## 5. Kill criteria check (Michael's list)
1. **Relational op after digitization → reject as evidence.** Most "analog AI"
   demos fail this; honest passers: Ambit, TCAM, coincidence, wired logic.
   Any ATMAN demo using per-reader ADC + digital AND is self-falsifying.
2. **Serialization.** Capacitive excitation/integration windows are time-shared
   across readers unless each reader carries its own excitation source
   (power ×P) — hidden serialization or hidden power, pick one. Coincidence
   needs accumulation windows. Only fully continuous transducers (wired
   logic, matchlines) are truly parallel.
3. **Reader-reader interference.** Quantified in 2.4/2.5: charge/current
   division, parasitic loading, crosstalk, accidental coincidences, sneak
   paths. Substantial by d ≈ 10–100.
4. **Peripherals erase the advantage.** Yes — 2.2 crossover math: no feasible
   E_reader exists; gap widens with P/N.
5. **Interconnect scaling.** P·k analog wires; 10³–10⁶× area per predicate
   vs. digital gates.
6. **CiM equivalence.** Yes — 3.2. Ambit/TCAM/SRAM-CiM embody relations in
   transducers with better amortization.
7. **Prior art.** Yes — section 4, some of it decades old.

## 6. What remains genuinely novel, if anything
Nothing in the readout mechanism. Every transducer class in the survey is
prior art; the predicate-parallel reader array is a TCAM; the
transducer-embodies-relation principle is Ambit/SRAM-CiM. The only novelty is
the specific mechanical packaging (non-contact multi-reader over patterned
substrate) — and it loses to existing packaging on every metric. What is
genuinely Michael's own is the ATMAN cognitive architecture (TSC/PSC/WFC,
the Judge, the processing loop) — software/architecture, untouched by this
brief.

## 7. What survives after all falsification
One narrow, honest statement: **for a fixed set of predicates evaluated
continuously at the sensor edge, where digitization is infeasible or
prohibitively expensive, a dedicated analog relational transducer can beat
digitize-then-compute.** That is in-sensor computing — a known, legitimate
niche (it is why coincidence counters and correlators exist). It confers no
capacity, no general energy/latency advantage over memory+logic or CiM, and
it scales only to small P before fan-out physics (2.4) kills it. As an
architecture for general relational readout, the hypothesis does not survive.

---
### Grounded numbers (sources)
- ADC Walden FOM: hero 0.4 fJ/conv-step (2019 survey, ASU); competitive designs
  6–42 fJ/conv-step ⇒ realistic 8-bit SAR ≈ 0.1–10 pJ/conversion.
- SRAM: 45 nm CACTI rule ≈ 6 pJ per 64-bit row read (~0.1 pJ/bit); Renesas
  65 nm record 1.8 ns access.
- Logic: min inverter toggle, FO4: 32 nm 0.13–0.45 fJ ⇒ ~0.02–0.1 fJ at 7 nm
  (extrapolated, labeled).
- Memristor crossbar: 189–316 fJ/MAC **core only, excl. DAC/ADC/peripherals**
  (MDPI 2026); memristor read ~50 fJ; analog op-amp stage 270 fJ/computation.
- 7 nm SRAM CIM: 351 TOPS/W ⇒ ~2.85 fJ/binary-op.
- Capacitive CDC: 8 aF resolution @ 50 kS/s, 4 µA low-power (ams PCap04);
  0.3 fF noise floor @ 100 S/s, 2.1 mA active (TI FDC2214).
- Ambit: MICRO 2017 (Seshadri et al.) — triple-row activation, sense-amp
  MAJ/AND/OR/NOT, <1% area, 32× perf / 35× energy vs baseline.
