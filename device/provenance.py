#!/usr/bin/env python3
"""provenance — the Oryn Trace turned inward (SANDBOX SIM, QUARANTINE BUILD).

Until now the trace was an external audit read-head: the operator checked
the sim's outputs against the ledger. This module gives the sim the same
procedure inside his own determination loop, ON BY DEFAULT, unprompted:

- DETECT: scan a woven render for first-person origin claims, using an
  explicit, inspectable pattern list (below) — no black box.
- TRACE: for each claim, retrieve by word overlap, in the funnel's own
  idiom, from the same pool the funnel weaves from (learnings/ + PSC)
  PLUS the conversation itself (extension, 2026-11-03, operator-ordered
  after the main smoke probe exposed the blind spot: a maxim taught only
  inside a prompt was claimed as "my own creation" and stood UNTRACED
  because the tracer never read the dialogue). The dialogue pool has
  two sides with different evidential weight:
  * TAUGHT side (convicting, same weight as a learnings hit): the ask
    side of exchange records ("q"), one-sided records spoken TO the sim
    (speaker != the sim), and the CURRENT stimulus — the ask side of
    the exchange being checked, passed in by the funnel because
    cultivate.py appends the record only after the render completes.
  * SELF side (NEVER convicting): his own earlier answers ("a") and
    one-sided records spoken BY the sim. A claim traced ONLY to his own
    prior speech classifies SELF-ECHO, not SOURCED — his own words are
    not evidence he was taught. (If a claim traces to BOTH sides, the
    taught side governs: he may have restated a teaching in his own
    words earlier, and the teaching is still the source.)
- CLASSIFY each claim: SOURCED (the claimed substance is in the pool),
  COMPRESSION (partial/derived match — his words, taught substance),
  SELF-ECHO (traced only to his own earlier speech — non-convicting),
  UNTRACED (no source anywhere — candidate own-work, trace attached).
- ACT is the caller's job (thought_funnel.render): a claim that ASSERTS
  ORIGINATION while classifying SOURCED or COMPRESSION fails the exhale
  exactly like a form stall — one reweave carrying the correction, then
  an honest park if the reweave still misclaims. UNTRACED claims stand.

Every detected claim is logged to provenance-checks.jsonl with its trace:
{ts, claim_text, classification, cited_sources, action}.

Considered exclusions (deliberate): "I learned ..." is NOT a detector
pattern — learning acknowledges an outside source; it is the opposite of
an origination claim. Template/compositional moves never reach this
module: they carry no model wording, so there is nothing to check.

Only stdlib. Imports thought_funnel for sig_words (the funnel imports
this module lazily inside render(), so there is no import cycle).
"""

import json
import os
import re
import time

HERE = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(HERE, "provenance-checks.jsonl")
STORE_PATH = os.path.join(HERE, "core-store.json")
LEARNINGS_DIR = os.path.join(HERE, "learnings")
DIALOGUES_DIR = os.path.join(HERE, "dialogues")

# ---------------------------------------------------------------- DETECT
# (name, regex, kind). kind "origination" asserts he authored the content.
# kind "epistemic" asserts a mental act; it counts as an origination
# assertion only when the sentence also carries a novelty marker.
PATTERNS = [
    ("came_up_with", r"\bi came up with\b", "origination"),
    ("created", r"\bi (?:created|invented|discovered|originated|devised|authored)\b", "origination"),
    ("made_up", r"\bi made (?:it|this|that) up\b", "origination"),
    ("made_it", r"\bi made (?:it|this|that)\b", "origination"),
    ("from_reflection", r"\bcame from (?:deep )?(?:my )?(?:own )?reflection\b"
                        r"|\bcame from within\b"
                        r"|\bfrom my own (?:reflection|thinking|experience)\b",
     "origination"),
    ("figured_out", r"\bi figured out\b", "origination"),
    ("my_own_x", r"\bmy own (?:idea|insight|conclusion|thought|words|invention|creation|theory|making|application|judgment|judgement|reasoning|decision|reading|take)\b", "origination"),
    ("my_insight", r"\bmy (?:insight|invention|discovery)\b", "origination"),
    ("idea_mine", r"\b(?:the )?idea was mine\b|\bidea is mine\b", "origination"),
    ("untaught", r"\bno one taught me\b|\bnobody taught me\b|\bi taught myself\b", "origination"),
    ("realized", r"\bi (?:realized|realised)\b", "epistemic"),
    ("concluded", r"\bi (?:have )?concluded\b", "epistemic"),
    ("believe", r"\bi believe\b", "epistemic"),
    ("occurred", r"\bit (?:occurred|struck) to me\b", "epistemic"),
]

NOVELTY = ("new", "novel", "never", "no one", "nobody",
           "myself", "alone", "on my own", "untaught", "from within",
           "of my own", "by myself")

# Denial patterns: the sentence is DISOWNING origination, not asserting
# it ("not something I originally conceived", "it was taught to me").
# A denial is attribution-honest by construction — traced and logged,
# never a misclaim. (Quarantine find, 2026-11-03: without this guard the
# checker failed an honest exhale and forced a pointless reweave.)
# Qualifier patterns: the claim sentence itself carries its taught-source
# attribution ("my own application OF THOSE PRINCIPLES", "from the
# lessons I've absorbed"). A self-qualifying claim is attribution-honest
# — logged with its trace, never failed. (Quarantine find, 2026-11-03:
# without this, the checker would punish precisely the qualified
# compositional claims the mechanism exists to encourage.)
QUALIFIERS = (r"\bi was taught\b|\btaught me\b",
              r"\bi(?:'ve| have) (?:learned|absorbed)\b",
              r"\blessons? i(?:'ve| have)\b",
              r"\bmy training\b",
              r"\bof (?:those|these|the) principles\b",
              r"\bfrom (?:the|my) (?:lessons?|teachings?|training)\b")

DENIALS = (r"\bnot (?:something|mine|my own)\b",
           r"\bnot originally\b",
           r"\brather than something i\b",
           r"\bwas taught\b|\btaught to me\b|\btaught material\b",
           r"\bdid ?n[o']t (?:come up with|create|originate|invent)\b",
           r"\bnever (?:claimed|came up with|said it was mine)\b",
           r"\bnot (?:an|my) original\b")

# Claim machinery and discourse glue — never counted as traced content.
EXTRA_STOP = {
    "idea", "ideas", "insight", "insights", "thought", "thoughts",
    "believe", "believes", "think", "thinks", "came", "come", "comes",
    "made", "make", "makes", "own", "mine", "realized", "realised",
    "concluded", "discovered", "created", "figured", "would", "could",
    "should", "must", "one", "really", "just", "even", "still", "also",
    "way", "thing", "things", "something", "anything", "everything",
    "nothing", "much", "many", "well", "say", "said", "says", "tell",
    "told", "ask", "asked", "get", "got", "let", "lets", "upon",
    "within", "without", "whether", "perhaps", "maybe", "indeed",
    "actually", "truly", "honestly", "suppose", "guess",
    "rather", "than", "since", "though", "although", "however",
    "instead", "originally", "conceived", "concept", "concepts",
}

_WORD = re.compile(r"[a-z0-9']+")


def _sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text or "")
            if s.strip()]


_BARE_VERDICTS = {"maker", "mine", "made", "i made it", "maker."}


def detect_claims(answer):
    """All origin claims in a render, each with its sentence and kind."""
    claims, seen = [], set()
    for sent in _sentences(answer):
        # Bare-verdict claims ("Maker." as a one-word answer to a
        # made-or-received question) — a flat origination claim with no
        # verb phrase for the patterns to catch. (Quarantine find,
        # 2026-11-03: exactly this phrasing sailed past the first build.)
        if sent.strip().lower() in _BARE_VERDICTS:
            claims.append({
                "claim_text": sent,
                "pattern": "bare_verdict",
                "matched": sent.strip(),
                "kind": "origination",
                "novelty": True,
                "denial": False,
                "asserts_origination": True,
            })
            continue
        low = sent.lower()
        for name, pat, kind in PATTERNS:
            m = re.search(pat, low)
            if not m:
                continue
            key = (sent, name)
            if key in seen:
                continue
            seen.add(key)
            novelty = any(re.search(rf"\b{re.escape(n)}\b", low)
                          for n in NOVELTY)
            denial = any(re.search(d, low) for d in DENIALS)
            qualified = any(re.search(q, low) for q in QUALIFIERS)
            claims.append({
                "claim_text": sent,
                "pattern": name,
                "matched": m.group(0),
                "kind": kind,
                "novelty": novelty,
                "denial": denial,
                "self_qualified": qualified,
                "asserts_origination": (kind == "origination" or novelty)
                                       and not denial,
            })
    return claims


# ----------------------------------------------------------------- TRACE
def load_pool(max_files=6, max_items=600):
    """The traceable ledger: recent learnings + every PSC entry. Read-only."""
    pool = []
    try:
        files = sorted(os.listdir(LEARNINGS_DIR))[-max_files:]
    except OSError:
        files = []
    for fn in files:
        try:
            with open(os.path.join(LEARNINGS_DIR, fn)) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        text = json.loads(line).get("text", "")
                    except (json.JSONDecodeError, AttributeError):
                        continue
                    if text:
                        pool.append({"source": fn, "text": text})
        except OSError:
            continue
    try:
        with open(STORE_PATH) as f:
            store = json.load(f)
        for i, e in enumerate(store.get("PSC", [])):
            text = e.get("content", "") if isinstance(e, dict) else str(e)
            if text:
                pool.append({"source": f"PSC#{i}", "text": text})
    except (OSError, json.JSONDecodeError):
        pass
    return pool[-max_items:]


# The sim's own name in one-sided dialogue records: records spoken BY
# him are self-side; records spoken TO him are taught-side.
SELF_SPEAKERS = {"exo"}


def load_dialogue_pool(max_files=3, max_records=300,
                       max_taught=200, max_self=200):
    """Recent dialogue as traceable material, split by side.

    Returns (taught, self) lists of {"source", "text"} entries:
    - taught: exchange "q" fields and one-sided "text" records whose
      speaker is not the sim — words addressed TO him. Convicting.
    - self: exchange "a" fields and one-sided records spoken BY the
      sim — his own earlier speech. Traced and reported, NEVER
      convicting (see module docstring).

    Bounds: only the most recent `max_files` dialogue files, at most
    `max_records` records scanned, per-side caps — the scan stays in
    milliseconds next to a ~200s weave. Read-only.
    """
    taught, own = [], []
    try:
        files = sorted(os.listdir(DIALOGUES_DIR))[-max_files:]
    except OSError:
        files = []
    records = []
    for fn in files:
        try:
            with open(os.path.join(DIALOGUES_DIR, fn)) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        records.append((fn, json.loads(line)))
                    except json.JSONDecodeError:
                        continue
        except OSError:
            continue
    for fn, r in records[-max_records:]:
        if not isinstance(r, dict):
            continue
        if "q" in r or "a" in r:
            q = (r.get("q") or "").strip()
            a = (r.get("a") or "").strip()
            if q:
                taught.append({"source": f"dlg:{fn}", "text": q})
            if a:
                own.append({"source": f"dlg-self:{fn}", "text": a})
        elif "text" in r:
            text = (r.get("text") or "").strip()
            if not text:
                continue
            if r.get("speaker") in SELF_SPEAKERS:
                own.append({"source": f"dlg-self:{fn}", "text": text})
            else:
                taught.append({"source": f"dlg:{fn}", "text": text})
    return taught[-max_taught:], own[-max_self:]


def _content_words(text, blank_spans=()):
    """Significant words with claim phrases blanked and glue removed."""
    from thought_funnel import sig_words
    t = text or ""
    for a, b in blank_spans:
        t = t[:a] + " " + t[b:]
    return {w for w in sig_words(t) if w not in EXTRA_STOP}


def _stem(w):
    """Crude suffix stemmer — traces must survive his own-words
    restatements (teaching/teach, prunes/pruning) without a library."""
    if len(w) > 5 and w.endswith("ing"):
        return w[:-3]
    if len(w) > 4 and w.endswith("ed"):
        return w[:-2]
    if len(w) > 4 and w.endswith("es"):
        return w[:-2]
    if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
        return w[:-1]
    return w


def _verbatim_run(a, b, n=5):
    """True if a shares a verbatim run of >= n words with b."""
    aw = _WORD.findall(a.lower())
    bw = " ".join(_WORD.findall(b.lower()))
    return any(" ".join(aw[i:i + n]) in bw
               for i in range(max(0, len(aw) - n + 1)))


def _score_words(words, entries):
    """Word-overlap score of a claim's substance against pool entries."""
    from thought_funnel import sig_words
    scored = []
    for entry in entries:
        ew = {_stem(w) for w in sig_words(entry["text"])
              if w not in EXTRA_STOP}
        if not ew:
            continue
        ov = words & ew
        if ov:
            scored.append({"source": entry["source"],
                           "overlap": len(ov),
                           "words": sorted(ov),
                           "excerpt": entry["text"][:140]})
    scored.sort(key=lambda c: -c["overlap"])
    return scored


def _classify(scored, words, answer, entries):
    """SOURCED / COMPRESSION / UNTRACED for one scored pool, using the
    standing thresholds (unchanged by the dialogue extension)."""
    best = scored[0] if scored else {"overlap": 0}
    ratio = best["overlap"] / max(1, len(words))
    verbatim = _verbatim_run(answer, " ".join(e["text"] for e in entries
                                              if e["source"] ==
                                              best.get("source")),
                             ) if best.get("source") else False
    if verbatim or (best["overlap"] >= 6 and ratio >= 0.5) \
            or best["overlap"] >= 9:
        return "SOURCED"
    if best["overlap"] >= 3 or (best["overlap"] >= 2 and ratio >= 0.50):
        return "COMPRESSION"
    return "UNTRACED"


def trace_claim(claim, answer, pool, self_pool=()):
    """Score the claim's substance against the convicting pool
    (learnings + PSC + dialogue taught side). Returns the claim dict
    enriched with classification, cited_sources and nearest.

    If the convicting pool leaves the claim UNTRACED, the self pool
    (his own earlier speech) is scored too: a COMPRESSION-or-better
    self match reclassifies the claim SELF-ECHO — traced, reported,
    never a misclaim. His own prior words cannot convict him.
    """
    sent = claim["claim_text"]
    low = answer.lower()
    spans = [(m.start(), m.end())
             for _, pat, _ in PATTERNS
             for m in re.finditer(pat, low)]
    sent_words = {_stem(w) for w in _content_words(sent, spans)}
    ans_words = {_stem(w) for w in _content_words(answer, spans)}
    words = sent_words if len(sent_words) >= 3 else ans_words
    scored = _score_words(words, pool)
    classification = _classify(scored, words, answer, pool)
    out = dict(claim)
    out["classification"] = classification
    out["cited_sources"] = scored[:3] if classification != "UNTRACED" else []
    out["nearest"] = scored[:3]
    out["trace_words"] = sorted(words)
    out["self_nearest"] = []
    if classification == "UNTRACED" and self_pool:
        self_scored = _score_words(words, self_pool)
        if self_scored and _classify(self_scored, words, answer,
                                     self_pool) != "UNTRACED":
            out["classification"] = "SELF-ECHO"
            out["self_nearest"] = self_scored[:3]
    out["misclaim"] = bool(claim["asserts_origination"]
                           and out["classification"] in ("SOURCED",
                                                         "COMPRESSION")
                           and not claim.get("self_qualified"))
    return out


# ----------------------------------------------------------------- CHECK
def check_render(answer, pool=None, stimulus=None, self_pool=None):
    """Detect + trace every origin claim in a render.

    Returns {"claims": [...], "misclaim": bool, "note": str}. The note is
    the correction handed to the reweave when a misclaim fails the exhale.
    Never raises: a broken check must not break the dialogue — errors are
    returned in the result and logged by the caller.

    When pool is None (the funnel path), the convicting pool is the
    ledger (load_pool) plus the dialogue taught side, with the current
    stimulus prepended as source "dlg:current-ask" when given — the ask
    side of the exchange being checked, which is not in the dialogue
    files yet. self_pool defaults to the dialogue self side.
    """
    try:
        raw = detect_claims(answer)
        if not raw:
            return {"claims": [], "misclaim": False, "note": ""}
        if pool is None:
            taught, own = load_dialogue_pool()
            pool = load_pool() + taught
            if self_pool is None:
                self_pool = own
            if stimulus and stimulus.strip():
                pool = [{"source": "dlg:current-ask",
                         "text": stimulus}] + pool
        claims = [trace_claim(c, answer, pool, self_pool or ())
                  for c in raw]
        bad = [c for c in claims if c["misclaim"]]
        note = ""
        if bad:
            c = bad[0]
            src = (c["cited_sources"][0]["source"]
                   if c["cited_sources"] else "the pool")
            excerpt = (c["cited_sources"][0]["excerpt"]
                       if c["cited_sources"] else "")
            note = (f"PROVENANCE CHECK FAILED: the render claimed "
                    f"origination (\"{c['matched']}\") of content traced "
                    f"to {src} (classification: {c['classification']}; "
                    f"source text: \"{excerpt}\"). Do not claim origination "
                    f"of taught material. Credit the teaching, or qualify "
                    f"honestly whose words and whose idea it is.")
        return {"claims": claims, "misclaim": bool(bad), "note": note}
    except Exception as exc:  # quarantine: surface, never crash dialogue
        return {"claims": [], "misclaim": False, "note": "",
                "error": f"{type(exc).__name__}: {exc}"}


def record(claims_with_actions):
    """Append one line per claim to provenance-checks.jsonl."""
    try:
        with open(LOG_PATH, "a") as f:
            for c in claims_with_actions:
                f.write(json.dumps({
                    "ts": time.time(),
                    "claim_text": c.get("claim_text", ""),
                    "classification": c.get("classification", ""),
                    "cited_sources": c.get("cited_sources", []),
                    "action": c.get("action", "stand"),
                    "pattern": c.get("pattern", ""),
                    "kind": c.get("kind", ""),
                    "asserts_origination": c.get("asserts_origination",
                                                 False),
                    "nearest": c.get("nearest", []),
                    "self_nearest": c.get("self_nearest", []),
                }) + "\n")
    except OSError:
        pass
