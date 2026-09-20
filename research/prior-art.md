# PRIOR-ART HUNT — hostile brief against ATMAN's surviving claim

Claim under test: "A shared physical substrate may permit multiple relational predicates
over its state (e.g., A∩B, B∩C, A∩¬C) to be read directly and potentially in parallel,
because the physical transducers themselves embody the relational operation rather than
digitizing individual variables and computing the relation afterward."
Claimed advantages: parallel relational retrieval, fewer sequential reads, lower latency,
less downstream logic, possibly less energy per query. NOT capacity (already dead).

Method: searched the FUNCTION, not the name. For each hit: (a) what relation is computed
natively in physics vs after digitization; (b) whether multiple DIFFERENT predicates share
ONE substrate SIMULTANEOUSLY; (c) danger rating 1–5 (5 = the claim is already built and
published); (d) citation.

---

## KILL SHOT 1 — Ternary Content-Addressable Memory (TCAM) — danger 5/5

(a) Native physics op: each row's match line is precharged high; every cell compares its
stored bit (0/1/X) against the broadcast search bit using the cell's transistors; any
mismatch pulls the shared match line down. The match line stays high IFF all cells match —
a conjunction of literals (A ∧ ¬B ∧ C …) computed in charge physics, pre-digitization.
Sense amplifiers only threshold the already-computed answer.
(b) Simultaneous multi-predicate: YES. The search word (the "state") is broadcast on
search lines to ALL rows at once; every row — each a different stored predicate, including
masked/don't-care literals — evaluates simultaneously in one cycle. This is literally
"Reader 1 → A∩B, Reader 2 → B∩C, Reader 3 → A∩¬C" with the mask bit supplying the ¬.
(c) 5/5. The claim is not just published — it has shipped in routers for decades.
(d) Standard architecture: match-line precharge/evaluate, ML sense amplifiers, priority
encoder (see e.g. Al-Mansour J. 2015 FPGA TCAM survey; US patent app. 20210407595 —
parallel TCAM plane search).

Verdict: TCAM is the surviving claim, built, in the exact Boolean-conjunction form,
evaluating many different predicates against one shared state in parallel.

## KILL SHOT 2 — Analog CAM with memristors (HP Labs) — danger 5/5

(a) Native physics op: 6-transistor/2-memristor cell; the two memristor conductances encode
lower/upper voltage bounds of an analog range. Voltage dividers set pull-down transistor
gates; the match line discharges unless the analog input voltage falls inside the stored
range. Range-membership predicate computed in analog physics. Verified in the patent text:
"The match line remains at the high voltage (which indicates a match) if all of the aCAM
cells connected to the match line match their corresponding input values." Analog input
accepted directly — the Nature paper states this enables "processing of analog sensor
data without the need for an analog-to-digital conversion step."
(b) Simultaneous multi-predicate: YES. Array of rows × columns; one analog search word
drives all rows in parallel; each row is a different multi-variable range predicate;
analog match-degree output per row.
(c) 5/5. Published, patented, and strictly more general than the claim (continuous ranges,
not just Boolean literals).
(d) Li et al., "Analog content addressable memories with memristors," Nature Communications
2020, DOI 10.1038/s41467-020-15254-4; US 10,847,238; US 10,896,731; US 11,551,771;
US app. 20220351794 (analog input + analog output).

Verdict: aCAM is the claim with analog I/O and no ADC anywhere in the predicate path.
Nothing about "transducers embodying the relation" is unbuilt.

## HIT 3 — Memristor/SRAM/Flash compute-in-memory crossbars — danger 4/5

(a) Native physics op: Ohm's law per cell (I = V·G) multiplies; Kirchhoff's current law sums
each column — full vector-matrix product in one analog step, at the storage site. Verified
in Nature Communications review: "all the currents in a column are instantaneously summed
(i.e., accumulation) by Kirchhoff's currents law." ADCs/TIAs at columns read out the
already-computed sums (readout, not relation-computation).
(b) Simultaneous multi-predicate: YES. Every column is a different weighted-sum predicate
sharing the same row inputs, evaluated in parallel in one step. Commercial: Mythic (Fick
et al., 1024×1024 NOR Flash analog matrix processor); IBM HERMES phase-change CIM.
(c) 4/5. Relations are linear (weighted sums), not arbitrary Boolean predicates — one step
narrower than the claim — but the "physics embodies the operation, parallel, shared
substrate" structure is identical.
(d) "Hardware implementation of memristor-based artificial neural networks," Nature
Communications 2024, s41467-024-45670-9; "A fully hardware-based memristive multilayer
neural network," Science Advances (abj4801).

Verdict: the parallel-shared-substrate readout half of the claim is commodity CIM.

## HIT 4 — In-sensor computing (Mennel et al.) — danger 4/5

(a) Native physics op: photodiode array where each pixel's photoresponsivity is a tunable
synaptic weight; photocurrents sum on row/column wires — the sensor IS the neural network,
classifying optically projected images "simultaneously sense and process optical images
without latency," 20M bins/s. No frame capture → digitize → compute pipeline.
(b) Simultaneous multi-predicate: YES — multiple output neurons (classes) share the same
photodiode substrate, read in parallel.
(c) 4/5. Transducer = computer, parallel relational (classification) readout, zero
digitize-then-compute. Predicates are learned linear classifiers rather than explicit
Boolean relations.
(d) Mennel et al., "Ultrafast machine vision with 2D material neural network image
sensors," Nature 2020, DOI 10.1038/s41586-020-2038-x.

Verdict: "the transducer embodies the relational operation" published in Nature, 2020.

## HIT 5 — Spin-wave majority gate with frequency-division multiplexing — danger 4/5

(a) Native physics op: spin-wave interference — output phase = majority of input phases;
MAJ(0,·,·) = AND, MAJ(π,·,·) = OR, computed by wave superposition in a magnetic waveguide.
(b) Simultaneous multi-predicate: YES — and this is the sharp one: "interference-based
computation allows for frequency-division multiplexing as well as the computation of
different logic functions in the same device." Different predicates, same substrate,
same time, separated by frequency.
(c) 4/5. Lab-demonstrated (imec, Kaiserslautern), nanoscale, reconfigurable — but still
research-stage, and transduction in/out of the magnetic domain is the weak point.
(d) Talmelli et al., "Reconfigurable nanoscale spin wave majority gate with
frequency-division multiplexing," arXiv:1908.02546 (2019); imec nanoscale majority-gate
program (Radu et al.).

Verdict: multiple different logic functions on one shared substrate simultaneously —
the claim's simultaneity requirement, demonstrated.

## HIT 6 — Optical correlators (Vander Lugt / Joint-Transform) — danger 3/5

(a) Native physics op: lens performs 2D Fourier transform passively; matched filter
multiplies in Fourier domain; second lens inverse-transforms — output plane IS the
correlation function over all shifts in parallel.
(b) Simultaneous multi-predicate: PARTIAL. One reference per filter; multiple references
need angular/wavelength multiplexing or sequential filters. All spatial shifts of one
predicate are parallel, but different predicates are not as cleanly simultaneous as CAM.
(c) 3/5. Parallel physical relational (similarity) readout since 1964, but single-predicate
at a time without multiplexing tricks.
(d) Vander Lugt, "Signal detection by complex spatial filtering," IEEE Trans. Inf. Theory
10, 1964; Weaver & Goodman, Appl. Opt. 5, 1966; US5883743A.

## HIT 7 — Race logic / temporal computing — danger 3/5

(a) Native physics op: information in arrival times; OR/AND = first/last arrival detectors;
tropical algebra primitives (MIN/MAX/ADD) computed by delay elements and gate physics.
NIST program; memristor-based temporal state machines (arXiv:2009.14243).
(b) Simultaneous multi-predicate: PARTIAL. Wavefront parallelism is real (e.g., DNA
alignment arrays), but distinct predicates are laid out as distinct circuits, not one
shared substrate queried many ways.
(c) 3/5. Physics-native relational ops, but the "shared substrate, many readers" geometry
is weaker.

## HIT 8 — SAW convolvers / acoustic correlators — danger 3/5

(a) Native physics op: counter-propagating surface acoustic waves multiply in a nonlinear
piezoelectric interaction region; output transducer emits the correlation/convolution —
computed in wave physics (US4556949A).
(b) Simultaneous multi-predicate: WEAK. One reference waveform at a time; programmable
via external reference, not parallel multi-predicate.
(c) 3/5 for the transducer-computes-it principle; 1/5 for the simultaneity claim.

## HIT 9 — Hopfield / optical associative memories — danger 3/5

(a) Native physics op: attractor dynamics — partial cue relaxes to nearest stored pattern
in parallel across all neurons (Farhat & Psaltis optical Hopfield, 1980s; photonic
Hopfield PRL 2026; Stanford atom-photon spin glass, Science 2026).
(b) Simultaneous multi-predicate: NO — one recall at a time; the substrate converges to a
single attractor. Parallel within one query, not across queries.
(c) 3/5 for associative parallel readout; fails the multi-predicate simultaneity test.

## HIT 10 — Coupled-oscillator Ising machines — danger 2/5

(a) Native physics op: coupled phases minimize an Ising energy — optimization by physics
(1440-oscillator CMOS chip, Communications Engineering 2024; VO2 oscillators, Nat. Commun.
2024; coherent Ising machines).
(b) NO — solves one embedded problem per run; not relational predicates over a state.
(c) 2/5. Physics-as-computer, but wrong function.

## HONEST REJECTIONS (look close, fail the criterion)

- Particle-physics coincidence triggers (LHCb muon 5-fold coincidence, NIM coincidence
units): the AND happens AFTER discriminator thresholding = 1-bit digitization. Fails the
"no digitize-then-compute" test. Useful as latency/parallelism precedent only.
- Capacitive fingerprint sensors: digitize the ridge image, match in software. Fails.
- Conventional digital ALUs obviously fail by definition.

---

## MAPPING TO THE PREDEFINED KILL CRITERIA

- "Relational operation actually occurs in downstream logic" — FALSE for TCAM/aCAM/
spin-wave/in-sensor: the relation is resolved in charge/current/wave physics before any
thresholding. The criterion does not fire; the prior art does.
- "Conventional compute-in-memory already performs the same operation equivalently" —
CONFIRMED. aCAM rows are stored relational predicates evaluated in parallel against a
shared input state. This is the claim, in CMOS + memristors.
- "Known prior art already implements the architecture" — CONFIRMED, twice over
(TCAM digital, aCAM analog), plus in-sensor and spin-wave variants of the simultaneity.

## WHAT REMAINS GENUINELY NOVEL, IF ANYTHING

Functionally: nothing. Every functional element of the surviving claim — transducers that
embody relational predicates, many different predicates sharing one substrate
simultaneously, no digitize-then-compute — is built and published (TCAM/aCAM) or
lab-demonstrated (spin-wave FDM, in-sensor).
What is new is only the MECHANICAL FORM FACTOR: counter-rotating patterned cylinders with
non-contact readers. That is a packaging choice, not a functional claim — and a form
factor without a functional advantage is not a surviving hypothesis. (If anything, the
cylinder inherits every weakness — calibration, crosstalk, wiring — with none of CMOS's
density.)

## WHAT CLAIM SURVIVES AFTER ALL FALSIFICATION

None of the novelty claim survives. The narrowed hypothesis — parallel physical
relational readout with the transducer embodying the operation — is prior art under the
names content-addressable memory, analog CAM, compute-in-memory, in-sensor computing,
and interference logic. The honest remaining statement is not a claim but a design note:
"a mechanically embodied CAM is buildable" — which is true, uninteresting, and already
implied by the existence of TCAM.
