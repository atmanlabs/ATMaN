# PROJECT ATMAN — PATENT ARCHAEOLOGY DIG
Date: 2026-09-19. Method: three parallel research briefs, all patent numbers,
dates, and assignees verified against Google Patents documents fetched today.
Expiry rule: utility patents issued before June 8, 1995 → 17 years from issue;
filed on/after → 20 years from filing. Every find below is confirmed
"Expired - Lifetime" and long public domain. Nothing claimed expired without
dates checking out.

---

## RANKED TOP 10

### 1. US3303494A — "Magnetically operated signs" (flip-dot display)
- **Year:** filed 1966, issued 1967 · **Holder:** Ferranti Packard Ltd (Toronto — the Ferrographics flip-dot sign company)
- **Status:** EXPIRED Feb 7, 1984 (17 yrs from 1967 issue). Google Patents: "Expired - Lifetime."
- **Stealable mechanism:** Each pixel is a swingably-mounted disc, black/white on opposite faces, carrying a permanent magnet. A matrix of U-shaped pole pieces energized by brief pulses flips only the addressed disc via a saturable X-Y coincidence gate; residual magnetism holds it with **zero holding power** — bistable, power-off state retention.
- **ATMAN fit:** The moving-parts pixel display — the soft *thock* of flipping discs is the audible signature the 80s-future core wants. Bistability means the readout holds state with power off, exactly like the immutable TSC layer should behave.
- **Source:** https://patents.google.com/patent/US3303494
- (Also cites Taylor's even earlier US3,140,553, filed 1961 — the original flip-dot patent, likewise long expired.)

### 2. US3501761A — "Remote-controlled display device for selectively displaying signs or words" (split-flap)
- **Year:** filed 1966, issued 1970 · **Holder:** Enrico Boselli SpA (Italian railway-display maker; the specific patent Wikipedia's split-flap article lists)
- **Status:** EXPIRED Mar 17, 1987 (17 yrs from 1970 issue). Google Patents: "Expired - Lifetime."
- **Stealable mechanism:** Forty character-bearing blades hinge-pin-mounted on disks along a motor-driven shaft; a spring holds the topmost blade vertical while the roll rotates them past the window. A coded rotary control drum with stationary brush contacts cuts motor power exactly when the brushes land on the right segments — position feedback with **zero electronics**, just a drum.
- **ATMAN fit:** The iconic clacking cascade is the most tactile readout ever built. The coded-drum indexer is a mechanical "read head" — a rotating cylinder deciding state by contact pattern — rhyming perfectly with a whirring rotating core.
- **Source:** https://patents.google.com/patent/US3501761

### 3. US3419855 — "Coincident Current Wired Core Memory for Computers" (core rope memory)
- **Year:** filed 1964, issued 1968 · **Holder:** General Motors Corporation (inventor Hayden A. Nelson)
- **Status:** EXPIRED Dec 31, 1985 (17 yrs from 1968 issue). Google Patents: "Expired - Lifetime."
- **Stealable mechanism:** Cores used as fixed transformers, not rewritable bits. Sense wires woven through or around toroidal cores in "rope fashion" — a wire threading a core encodes 1, bypassing it encodes 0. The *geometry of the wiring itself* is the stored data, unrewritable by design; address selection radically simplified (2N drive lines for a whole word plane).
- **ATMAN fit:** The TSC immutable layer, physically realized: firmware literally woven into a visible loom. Core truth that is *incapable* of being overwritten — hardware-enforced immutability with maximum retro-future weave theater.
- **Source:** https://patentimages.storage.googleapis.com/91/30/6b/e33a04be975637/US3419855.pdf
- **Honesty note:** no specific MIT Instrumentation Lab / AC Spark Plug patent for the *Apollo* rope modules could be verified (AGC hardware may have been built without a cleanly documented patent). This GM patent covers the same mechanism and is the verified, expired, literally-named "core rope memory" patent.

### 4. US2629827A — "Memory system" (Eckert & Mauchly's circulating memory)
- **Year:** filed 1947, issued 1953 · **Holder:** Eckert-Mauchly Computer Corporation (inventors J. Presper Eckert Jr. & John W. Mauchly)
- **Status:** EXPIRED Feb 24, 1970 (17 yrs from 1953 issue). Long public domain.
- **Stealable mechanism:** Pulses fired through a medium (mercury tank, LC delay line, magnetostrictive wire) are caught by transducers at the far end and fed back to the input — a train of bits **circulates endlessly** like a racetrack. The patent explicitly covers mechanical equivalents: an endless disc or band with spots carried by rotation past a read station, and even phosphorescent dots imprinted by modulated light and read by photocell — **rotating-disc non-contact optical readout, all in one 1947 filing**.
- **ATMAN fit:** The literal circulating-memory lineage — memory that lives *in motion*, kept alive by a feedback loop. A slow phosphor-disc loop could be the WFC (fast everyday layer), visually and mechanically honest.
- **Source:** https://patents.google.com/patent/US2629827

### 5. US3460116A — "Magnetic Domain Propagation Circuit" (bubble memory)
- **Year:** filed 1966, issued 1969 · **Holder:** Bell Telephone Laboratories (Bobeck, Gianola, Sherwood, Shockley)
- **Status:** EXPIRED Aug 5, 1986 (17 yrs from 1969 issue). Google Patents: "Expired - Lifetime" (anticipated expiration 1986-08-05).
- **Stealable mechanism:** Tiny cylindrical magnetic domains ("bubbles") in a thin garnet film are shoved step-by-step along tracks defined by permalloy T-bar/chevron propagation elements using a **rotating external magnetic field**; bits circulate in closed loops until brought to the edge for read/write. Nonvolatile via permanent bias magnets — kill the field and the memory erases.
- **ATMAN fit:** Bits *visibly circulating* in loops is the most "alive" mechanism of the lot, and the rotating-field drive gives literal spinning motion to match the whirring-machine aesthetic. WFC material. Failure history is a feature — we get to do what Intel couldn't.
- **Source:** https://patents.google.com/patent/US3460116A/en
- **The kill:** Bell Labs invented it; Intel bet big (the 7110 1-megabit bubble chip, 1979), ended up "the lone producer in the United States," market collapsed as semiconductor memory and hard drives undercut it — Intel Magnetics sold to MemTech, bubbles "disappeared entirely by the late 1980s." Sources: https://en.wikipedia.org/wiki/Bubble_memory, https://hackaday.com/2020/04/19/magnetic-bubble-memory-farewell-tour/
- (Sibling: US3534347, Bobeck, issued Oct 13, 1970 — the commercially-used field-access propagation mode; expired Oct 13, 1987 by the same rule.)

### 6. US3430966 — "Transparent recording disc" (optical non-contact readout)
- **Year:** filed 1967, issued 1969 · **Holder:** Gauss Electrophysics Inc (inventor David Paul Gregg)
- **Status:** EXPIRED Mar 4, 1986 (17 yrs from 1969 issue). Google Patents: "Expired - Lifetime."
- **Stealable mechanism:** A transparent plastic disc carries a spiral track as opaque metallic deposits; it spins at ~1800–3600 RPM while a light source shines **through** the disc from one side and a transducer head on the other side reads the modulated light — pure optical, non-contact pickup, read *through* the medium. Ferromagnetic hub ring couples to the spindle magnetically (no clamp); recording layer buried under protective coating.
- **ATMAN fit:** The "scanners over a rotating shaft" endgame — readout by light, nothing touching anything, the disc's own rotation doing the sequencing.
- **Source:** https://patents.google.com/patent/US3430966
- **The kill:** MCA bought Gregg's patents **and his company** (Gauss Electrophysics) in the early 1960s; assignment trail runs MCA Discovision → Discovision Associates (1981). The lineage led to LaserDisc — which flopped as a consumer product. Giant-company money buried a read-through-light spinning disc; the mechanism is free now.

### 7. US3140474A — "Magnetic memory drum" (air-bearing spinning drum)
- **Year:** filed 1960, issued 1964 · **Holder:** Burroughs Corporation (inventor Ervin Leshner)
- **Status:** EXPIRED Jul 7, 1981 (17 yrs from 1964 issue). Public domain.
- **Stealable mechanism:** A magnetic drum spins on a **fluid/air bearing**; differential air pressure slides the frusto-conical rotor laterally to fine-tune the head-to-surface gap. Heads never touch the recording surface — the air film does the spacing. Rotor runs on mechanical bearings at startup, then lifts onto the air bearing at speed: a self-levitating spinning memory.
- **ATMAN fit:** The closest 1960s cousin to "scanners over a rotating shaft" — a drum that audibly spins up, lifts off its bearings, and gets read without contact. Whirring rotation with a real mechanical reason, plus a satisfyingly physical air-pressure gap adjustment that could be a literal knob on the front panel.
- **Source:** https://patents.google.com/patent/US3140474A/en

### 8. US3187321A — "Operator-computer communication console" (lit-key front panel)
- **Year:** filed 1961, issued 1965 · **Holder:** Bunker Ramo Corporation (inventor Stanley L. Kameny; Bunker Ramo built BUIC air-defense systems)
- **Status:** EXPIRED Jun 1, 1982 (17 yrs from 1965 issue). Google Patents: "Expired - Lifetime."
- **Stealable mechanism:** A console front panel with translucent request keys, each over its own lamp so the computer can light the key itself (bidirectional illuminated pushbuttons), plus perforated overlay cards that physically encode a routine ID via pin-and-hole plugs, auto-loading the right "program" when laid on the keyboard.
- **ATMAN fit:** A working 1961 blueprint for the hand-operated console: illuminated keys plus interchangeable physical "program cards" — the overlay-card concept maps straight onto the three memory layers (immovable card = TSC, swappable card = PSC, live keys = WFC).
- **Source:** https://patents.google.com/patent/US3187321
- **The kill:** Bunker Ramo was bought by Allied Chemical in 1981 and its mainframe-console product line vanished with the minicomputer era — the console wars were settled by the glass terminal, not the lit-key panel.

### 9. US4118611A — "Buckling spring torsional snap actuator" (the click itself)
- **Year:** filed 1977, issued 1978 · **Holder:** IBM (inventor Richard Hunter Harris)
- **Status:** EXPIRED (17 yrs from 1978 issue → Oct 1995; Google lists anticipated expiration 1997-08-30 on the 20-year-from-filing basis — expired either way, decades ago). Google Patents: "Expired - Lifetime." Sibling Model M patent US4,528,431 likewise expired.
- **Stealable mechanism:** A helical compression spring between keycap and rocker "catastrophically buckles" sideways at a precise travel point, slamming the rocker over-center in one snap — tactile break, audible click, and contact closure from a single event, with deliberate hysteresis so it never chatters. Extreme mechanical simplicity.
- **ATMAN fit:** The patent's own words promise "tactile feedback" and "an audible click." Scaled up from keyswitch size, this mechanism gives every core-layer control a Model M-grade thunk.
- **Source:** https://patents.google.com/patent/US4118611
- **The kill:** the patent record shows the 1991 reassignment from IBM to IBM Information Products Corp (the Lexmark spin-off, with a Morgan Bank security interest) — IBM sold off the entire keyboard business; Lexmark wound the line down and the IP lapsed into the public domain. **Nobody owns the click anymore.**

### 10. US2632058A — "Pulse code communication" (the Gray code)
- **Year:** filed 1947, issued 1953 · **Holder:** Bell Telephone Laboratories (inventor Frank Gray)
- **Status:** EXPIRED Mar 17, 1970 (17 yrs from 1953 issue). Google Patents: "Expired - Lifetime," anticipated expiration 1970-03-17.
- **Stealable mechanism:** A binary code where every consecutive value differs by exactly one digit (the "reflected binary code"), so a spinning code wheel with etched aperture patterns never produces a garbage reading when the sensor straddles a boundary — only one track ever changes at a time. The patent describes the physical coding *mask*: a rectangular array of apertures where each column's pattern is the Gray code table.
- **ATMAN fit:** The tactile-dial lineage in one document — a hand-turned code wheel whose angular position reads out unambiguously as an LED-friendly digit, with chunky mechanical detents and zero glitch states. TSC selector, PSC bank switch, WFC jog dial: each click a Gray-code position, no bounce ambiguity.
- **Source:** https://patents.google.com/patent/US2632058A/en

---

## HONORABLE MENTIONS (verified, just missed the cut)

- **US3083353A — "Magnetic Memory Devices"** (twistor memory). Filed 1957, issued 1963, Bell Labs (Bobeck). Expired Mar 26, 1980. The wire itself is memory: helical flux path in a magnetic conductor, bits read nondestructively by passing current through the wire — the wire doubles as its own drive/sense line. PSC-layer candidate; wire-that-is-memory is physically gorgeous. **Kill:** AT&T "had great hopes for twistor memory" until DRAM arrived in the early 1970s and "rapidly replaced all previous random-access memory systems." https://patents.google.com/patent/US3083353A/en
- **US3487380 — "Nondestructive Transfer, Plated Wire Memory Arrangement."** Filed 1965, issued 1969, Sperry Rand (Woo F. Chow). Expired Dec 30, 1986. Thin permalloy film electroplated on wire; bits = direction of circumferential magnetization (clockwise vs counterclockwise) at bit stations along the wire — "bits live in the skin of the wire." Fast, rugged, aerospace standard; spool-of-wire form factor gives moving parts (reels turning). WFC candidate. https://patentimages-storage-googleapis-com.proxy.c9w.net/b5/ce/54/1b87929f8d08c5/US3487380.pdf
- **US4004120A — "Switch bezel with visual indicator."** Filed 1975, issued 1977, C&K Components (Ivan A. Lee). Expired Jan 18, 1994. Panel bezel with snap-in fingers accepting both the switch assembly and a separate press-fit LED indicator — the exact hardware grammar of the 70s/80s console panel (switch + discrete status lamp per bezel, no glass). Ganged multi-switch/multi-lamp bezels are literally an Altair-style front panel, stealable part for part. https://patents.google.com/patent/US4004120

## BIG-COMPANY KILL STORIES (bonus, sourced)
1. **Intel × bubble memory** — Intel's 7110 1-Mb bubble chip (1979); Intel ended up "the lone producer in the United States"; market collapsed; Intel Magnetics sold to MemTech; bubbles gone by the late 1980s.
2. **MCA × Gregg's optical disc** — MCA bought Gregg's patents and his company Gauss Electrophysics; lineage led to LaserDisc, a consumer flop. Read-through-light spinning disc, free now.
3. **IBM × the click** — 1991 reassignment to IBM Information Products (Lexmark spin-off); keyboard business sold off and wound down; buckling-spring IP in the public domain.
4. **AT&T × twistor** — Bell Labs' great hope for cheap memory, killed by early-1970s DRAM.
5. **Allied Chemical × Bunker Ramo** — 1981 acquisition; console product line vanished with the minicomputer era.
6. **Pertec × MITS Altair** — verified in the earlier session: Pertec bought MITS in 1977 and killed the toggle-switch front-panel line. (Not a patent find, but the founding ghost of the whole aesthetic.)

## WHAT THE STEALABLE STACK LOOKS LIKE
- **Readout:** flip-dot (US3303494A) or split-flap (US3501761A) — bistable moving-parts display, zero holding power, audible signature.
- **Front panel:** Bunker Ramo console (US3187321A) grammar + C&K bezels (US4004120A) + IBM buckling springs (US4118611A) for the click.
- **Selectors:** Gray-code dials (US2632058A).
- **Immutable layer (TSC):** woven core rope (US3419855) — truth as wiring geometry.
- **Rewritable layer (PSC):** twistor wire (US3083353A) or bubble loops (US3460116A).
- **Fast everyday layer (WFC):** circulating delay-line loops (US2629827A) or Gregg's optical disc (US3430966).
- **Spinning mechanics:** air-bearing drum (US3140474A).
