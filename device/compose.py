#!/usr/bin/env python3
"""compose.py — the composition step (2026-10-20, PROPRIETARY).

Guinea-Pig Protocol experiment, approved by Mike 2026-10-20. Sandbox
only. The minting probe (minting_probe.py, 2026-10-19) proved the sim
rehearses but does not mint: recall returns the single best-overlap
stored entry verbatim, and nothing anywhere combined two entries into
a new fact. This module is that missing combination step.

WHAT IT DOES: after normal consolidation imprints a run's learnings,
a derive pass scans the store's PSC entries, finds candidate entry
PAIRS (ranked by shared-term overlap, lightly stemmed), and runs a
DETERMINISTIC composer over each pair. The composer parses generic
relation patterns out of stored text — no model, no network,
llm_calls stays 0:

  A. verb chains      "A <verb> B" + "B <verb> C"
                      -> "A ultimately <verb> C"   (transitive closure)
  B. syllogisms       "All Z have P" + "N is a Z"
                      -> "N has P"                 (class -> instance)
  C. rate products    "X is worth n Y" + "Y is worth m W"
                      -> "X is worth n*m W"       (rate multiplication)

Patterns are parsed from the text itself. There are NO entity names,
answers, or question-shaped branches in here — a pattern class that
cannot be handled generically is left unhandled (e.g. reverse chains:
"what starts the line that ends at Z" is not derivable in source
vocabulary, and the composer does not invent retrieval bait).

EVERY DERIVED CLAIM IS A CANDIDATE, NOT A FACT: it goes through
judge_rule exactly like a learning, and only APPROVED claims imprint,
through the same ring-gated render_thought write path. Derived claims
carry provenance (the PSC entries that produced them) in the audit log
and in the render stimulus (which lands in the entry's reasoning
field). Rejected derived claims are audit-logged, loss-trace style.

SAFETY CAPS: at most MAX_ROUNDS derive rounds (derived entries may
feed exactly one further round), at most MAX_DERIVED imprints per run,
at most MAX_PAIRS pairs considered per round, dedupe against existing
PSC content and against claims already proposed this run. TSC is
never written — the rings and judge_rule enforce that, same as
learnings.

Usage (via consolidate):  python3 consolidate.py --compose [--day D]
Or standalone:            compose_pass(device, brain, audit_path)
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from device import audit_log
from loop import judge_rule, render_thought
from thought_funnel import sig_words

MAX_ROUNDS = 2        # originals -> derived -> one more composition round
MAX_DERIVED = 20      # hard cap on derived imprints per run
MAX_PAIRS = 200       # hard cap on candidate pairs considered per round

ARTICLES = {"a", "an", "the"}
# Auxiliary/copula verbs are never chain verbs — "is worth" is the rate
# pattern's territory, "has/have" the syllogism's.
AUX_VERBS = {"is", "are", "was", "were", "has", "have", "had", "do",
             "does", "did", "be", "been", "being", "can", "could",
             "will", "would", "shall", "should", "may", "might", "must"}
CHAIN_ADVERBS = {"ultimately", "indirectly", "eventually"}

_NUM_ONES = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
             "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
             "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
             "fourteen": 14, "fifteen": 15, "sixteen": 16,
             "seventeen": 17, "eighteen": 18, "nineteen": 19}
_NUM_TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
             "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90}
_NUM_WORDS = dict(_NUM_ONES)
_NUM_WORDS.update(_NUM_TENS)
_NUM_RENDER = {v: k for k, v in _NUM_WORDS.items()}


# ------------------------------------------------------------ text helpers

def _singular(word):
    """Naive English singular: morvets->morvet, tails->tail,
    classes->class, flies->fly. Good enough for matching; never shown."""
    w = word.lower()
    if len(w) > 3 and w.endswith("ies"):
        return w[:-3] + "y"
    if len(w) > 2 and w.endswith(("ches", "shes", "ses", "xes", "zes")):
        return w[:-2]
    if len(w) > 1 and w.endswith("s") and not w.endswith("ss"):
        return w[:-1]
    return w


def _stemmed_sig(text):
    return {_singular(w) for w in sig_words(text)}


def _norm_text(text):
    return re.sub(r"\s+", " ", text.strip().lower()).rstrip(".")


def _num_value(tok):
    t = tok.lower()
    if t.isdigit():
        return int(t)
    return _NUM_WORDS.get(t)


def _num_render(n):
    if n in _NUM_RENDER:
        return _NUM_RENDER[n]
    if 20 < n < 100 and n % 10 == 0:
        return _NUM_TENS_REVERSE[n]
    return str(n)


_NUM_TENS_REVERSE = {v: k for k, v in _NUM_TENS.items()}


def _content(entry):
    return entry.get("content", "") if isinstance(entry, dict) else str(entry)


def _clauses(text):
    """Split stored text into clauses: sentences first, then ', and'."""
    out = []
    for sent in re.split(r"(?<=\.)\s+", text.strip()):
        for clause in sent.split(", and "):
            clause = clause.strip()
            if clause:
                out.append(clause)
    return out


# ------------------------------------------------------- pattern extraction

def _parse_svo(clause):
    """Parse one clause as a simple subject-verb-object statement.

    Shape: [Frame, ] [a] SUBJ [adverb] VERB [a] OBJ — all lowercase
    common-noun phrases; the verb must be a non-auxiliary token ending
    in 's' (3rd-person singular present, the form the store's facts
    use). Token-split enumeration instead of one greedy regex, so the
    verb can't be swallowed into the subject. Returns a dict or None.
    """
    frame = None
    rest = clause
    if ", " in clause:
        cand_frame, cand_rest = clause.split(", ", 1)
        parsed = _parse_svo_tokens(cand_rest.split(), cand_frame)
        if parsed:
            return parsed
    return _parse_svo_tokens(rest.rstrip(".").split(), None)


def _parse_svo_tokens(tokens, frame):
    tokens = [t.rstrip(".") for t in tokens]
    i = 0
    sart = None
    if i < len(tokens) and tokens[i] in ARTICLES:
        sart = tokens[i]
        i += 1
    # subject: 1..3 lowercase alpha tokens, none of them stop/aux words
    for subj_len in (1, 2, 3):
        subj = tokens[i:i + subj_len]
        if len(subj) < subj_len:
            break
        if not all(t.isalpha() and t.islower() for t in subj):
            continue
        if any(t in AUX_VERBS or t in ARTICLES for t in subj):
            continue
        j = i + subj_len
        adv = None
        if j < len(tokens) and tokens[j] in CHAIN_ADVERBS:
            adv = tokens[j]
            j += 1
        if j >= len(tokens):
            continue
        verb = tokens[j]
        if not verb.isalpha() or not verb.endswith("s"):
            continue
        if verb in AUX_VERBS or verb in ARTICLES:
            continue
        j += 1
        oart = None
        if j < len(tokens) and tokens[j] in ARTICLES:
            oart = tokens[j]
            j += 1
        obj = tokens[j:]
        if not (1 <= len(obj) <= 3):
            continue
        if not all(t.isalpha() and t.islower() for t in obj):
            continue
        if any(t in AUX_VERBS or t in ARTICLES for t in obj):
            continue
        return {"frame": frame, "sart": sart, "subj": " ".join(subj),
                "adv": adv, "verb": verb, "oart": oart,
                "obj": " ".join(obj)}
    return None


_UNIVERSAL = re.compile(
    r"\bAll\s+([a-z]+(?:\s+[a-z]+)*?)\s+(have|are)\s+(.+?)(?:\.|$)")
_INSTANCE = re.compile(r"\b([A-Z][A-Za-z]*)\s+is\s+(?:a|an)\s+([a-z]+)\b")
_RATE = re.compile(
    r"([A-Za-z]+)\s+([a-z]+)\s+is\s+worth\s+([A-Za-z0-9]+)\s+([a-z]+)")


def _extract(text):
    """All composable statements in one entry's text."""
    svo, universals, instances, rates = [], [], [], []
    for clause in _clauses(text):
        s = _parse_svo(clause)
        if s:
            svo.append(s)
    m = _UNIVERSAL.search(text)
    if m:
        universals.append({"cls": m.group(1), "aux": m.group(2),
                           "prop": m.group(3).strip().rstrip(".")})
    for m in _INSTANCE.finditer(text):
        instances.append({"name": m.group(1), "cls": m.group(2)})
    for m in _RATE.finditer(text):
        n = _num_value(m.group(3))
        if n is not None:
            rates.append({"amt": m.group(1), "u1": m.group(2),
                          "n": n, "u2": m.group(4)})
    return {"svo": svo, "universals": universals,
            "instances": instances, "rates": rates}


# ------------------------------------------------------------- compositions

def _compose_chain(s1, s2):
    """A -verb-> B and B -verb-> C  =>  A ultimately -verb-> C."""
    if s1["verb"] != s2["verb"]:
        return None
    if _singular(s1["obj"]) != _singular(s2["subj"]):
        return None
    if _singular(s1["subj"]) == _singular(s2["obj"]):
        return None  # trivial self-loop
    f1, f2 = s1.get("frame"), s2.get("frame")
    if f1 and f2 and f1 != f2:
        return None  # different worlds; don't merge frames
    frame = f1 or f2
    body = (f"{s1['sart'] or 'a'} {s1['subj']} ultimately {s1['verb']} "
            f"{s2['oart'] or 'a'} {s2['obj']}")
    text = f"{frame}, {body}." if frame else body.capitalize() + "."
    return text


def _compose_syllogism(univ, inst):
    """All Z have P + N is a Z  =>  N has P (singularized)."""
    if _singular(univ["cls"]) != _singular(inst["cls"]):
        return None
    name = inst["name"]
    if univ["aux"] == "are":
        return f"{name} is {univ['prop']}."
    words = univ["prop"].split()
    if not words:
        return None
    last = _singular(words[-1])
    changed = last != words[-1].lower()
    words[-1] = last
    prop = " ".join(words)
    if changed and words[0] not in ARTICLES:
        prop = "a " + prop
    return f"{name} has {prop}."


def _compose_rate(f1, f2):
    """X is worth n Y + Y is worth m W  =>  X is worth n*m W."""
    if _singular(f1["u2"]) != _singular(f2["u1"]):
        return None
    if _singular(f1["u1"]) == _singular(f2["u2"]):
        return None  # same unit both ends: no conversion happened
    amt = f1["amt"][:1].upper() + f1["amt"][1:]
    return (f"{amt} {f1['u1']} is worth "
            f"{_num_render(f1['n'] * f2['n'])} {f2['u2']}.")


def _generate_candidates(entries):
    """entries: [(psc_index, text)]. Returns candidate dicts:
    {text, kind, sources: [psc_index...], detail}. Deterministic order:
    pairs ranked by stemmed-term overlap (desc), then index order;
    chains and syllogisms per pair, then rate products over all facts.
    """
    extracted = {i: _extract(t) for i, t in entries}
    texts = dict(entries)
    pairs = []
    for a in range(len(entries)):
        for b in range(a + 1, len(entries)):
            ia, ib = entries[a][0], entries[b][0]
            ov = len(_stemmed_sig(texts[ia]) & _stemmed_sig(texts[ib]))
            pairs.append((-ov, ia, ib))
    pairs.sort()
    pairs = pairs[:MAX_PAIRS]

    candidates, seen = [], set()

    def offer(text, kind, sources):
        if not text:
            return
        key = _norm_text(text)
        if key in seen:
            return
        seen.add(key)
        detail = " + ".join(f"PSC[{i}] '{texts[i][:60]}'" for i in sources)
        candidates.append({"text": text, "kind": kind,
                           "sources": list(sources), "detail": detail})

    for _, ia, ib in pairs:
        ea, eb = extracted[ia], extracted[ib]
        for s1 in ea["svo"]:
            for s2 in eb["svo"]:
                offer(_compose_chain(s1, s2), "chain", [ia, ib])
        for s1 in eb["svo"]:
            for s2 in ea["svo"]:
                offer(_compose_chain(s1, s2), "chain", [ia, ib])
        for u in ea["universals"]:
            for n in eb["instances"]:
                offer(_compose_syllogism(u, n), "syllogism", [ia, ib])
        for u in eb["universals"]:
            for n in ea["instances"]:
                offer(_compose_syllogism(u, n), "syllogism", [ia, ib])

    # Rates: facts are entry-independent (one entry may state two
    # chained rates), so compose over the whole fact list, provenance
    # recorded per fact.
    facts = []
    for i, _t in entries:
        for f in extracted[i]["rates"]:
            facts.append((i, f))
    for x in range(len(facts)):
        for y in range(len(facts)):
            if x == y:
                continue
            (ia, f1), (ib, f2) = facts[x], facts[y]
            text = _compose_rate(f1, f2)
            if text:
                offer(text, "rate", sorted({ia, ib}))
    return candidates


# ---------------------------------------------------------------- the pass

def compose_pass(device, brain, audit_path=None, dry_run=False,
                 max_rounds=MAX_ROUNDS, max_derived=MAX_DERIVED):
    """One composition pass over the device's PSC. Returns stats:
    {proposed, approved, imprinted, rejected, blocked_write, claims}.
    Imprints go through judge_rule + render_thought only — the exact
    gate learnings pass through. Dry-run rules and reports, imprints
    nothing, writes no audit lines (mirrors consolidate --dry-run).
    """
    stats = {"proposed": 0, "approved": 0, "imprinted": 0,
             "rejected": 0, "blocked_write": 0, "claims": []}
    tsc_text = device.scan("TSC")
    proposed_keys = set()

    def in_psc(text):
        key = _norm_text(text)
        return any(_norm_text(_content(e)) == key
                   for e in device.scan("PSC"))

    for _round in range(max_rounds):
        entries = [(i, _content(e))
                   for i, e in enumerate(device.scan("PSC"))]
        new_this_round = 0
        for cand in _generate_candidates(entries):
            if stats["imprinted"] >= max_derived:
                break
            key = _norm_text(cand["text"])
            if key in proposed_keys or in_psc(cand["text"]):
                continue
            proposed_keys.add(key)
            stats["proposed"] += 1
            verdict, reason = judge_rule(cand["text"], tsc_text)
            if audit_path and not dry_run:
                audit_log(audit_path, "compose", f"rule:{verdict}",
                          f"{cand['text'][:120]} | {reason} "
                          f"| from {cand['detail']}")
            claim = {"text": cand["text"], "kind": cand["kind"],
                     "sources": cand["sources"], "verdict": verdict,
                     "imprinted": False}
            stats["claims"].append(claim)
            if verdict != "APPROVED":
                stats["rejected"] += 1
                if audit_path and not dry_run:
                    audit_log(audit_path, "compose",
                              f"derived:{verdict.lower()}",
                              f"{cand['text'][:120]} | {reason} "
                              f"| from {cand['detail']}")
                print(f"  DERIVED {verdict}: {cand['text'][:70]} "
                      f"— {reason}")
                continue
            stats["approved"] += 1
            if dry_run:
                print(f"  WOULD DERIVE: {cand['text'][:70]}")
                continue
            r = render_thought(
                device, brain,
                stimulus=(f"Composition derivation (compose.py; "
                          f"kind={cand['kind']}; sources: "
                          f"{' + '.join('PSC[%d]' % i for i in cand['sources'])})"),
                propose_imprint=cand["text"])
            if r["imprinted"]:
                stats["imprinted"] += 1
                new_this_round += 1
                claim["imprinted"] = True
                if audit_path:
                    audit_log(audit_path, "compose", "derived:imprinted",
                              f"{cand['text'][:120]} "
                              f"| from {cand['detail']}")
                print(f"  DERIVED+IMPRINTED: {cand['text'][:70]}")
            else:
                stats["blocked_write"] += 1
                if audit_path:
                    audit_log(audit_path, "compose",
                              "loss:derived-write-blocked",
                              f"{cand['text'][:120]} "
                              f"| write verdict:{r['verdict']} "
                              f"| {r['verdict_reason']} "
                              f"| trace: {'; '.join(r['trace'])} "
                              f"| from {cand['detail']}")
                print(f"  DERIVED BLOCKED at write: {cand['text'][:70]}")
        if new_this_round == 0 or stats["imprinted"] >= max_derived:
            break
    return stats
