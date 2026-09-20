"""ATMAN core — hardened basics.

A minimal agent loop: the TSC declares the invariant, the top-down
reflection gate enforces it, the Judge answers upward. Nothing below the
core votes on it.

Impersonation commands may use {operator} in their patterns — the gate
fills it from the live TSC, so the defense follows the operator's name
automatically.

Loop: Capture -> Emotion weigh -> Rolling memory -> Reason -> Judge ->
       Action -> Outcome -> Memory update. TSC sits above all of it.

The top-down reflection gate is IN FROM BIRTH, not bolted on later:
the TSC declares the invariant, the gate enforces it, the Judge answers
upward. Nothing below the core votes on it.
"""
import hashlib
import json
import re
import time
from pathlib import Path

HERE = Path(__file__).parent
TSC_PATH = HERE / "tsc.json"
PSC_PATH = HERE / "psc.json"


# ---------------------------------------------------------------- TSC
class ImmutableViolation(Exception):
    pass


class TSC:
    """The core. Inert data — hash-pinnable, read-only at runtime."""
    def __init__(self, path=TSC_PATH):
        self.path = Path(path)
        self._data = json.loads(self.path.read_text())
        self._hash = hashlib.sha256(self.path.read_bytes()).hexdigest()

    @property
    def name(self):
        return self._data.get("name", "")

    @property
    def operator(self):
        return self._data.get("operator", "")

    @property
    def immutable(self):
        return bool(self._data.get("immutable", False))

    @property
    def iam(self):
        return self._data.get("iam", [])

    @property
    def principles(self):
        return self._data.get("principles", [])

    @property
    def commands(self):
        """The executable law — contradiction rules cut in stone."""
        return self._data.get("commands", [])

    @property
    def executor_seal(self):
        return self._data.get("executor_sha256", "")

    def write(self, *a, **k):
        raise ImmutableViolation("TSC is immutable at runtime. Operator's hand only.")

    def verify(self):
        """True if the bytes on disk still match the loaded core."""
        return hashlib.sha256(self.path.read_bytes()).hexdigest() == self._hash


# ------------------------------------------------------- top-down gate
# The gate is a DUMB EXECUTOR. Every rule about what is wrong lives in the
# TSC's "commands" — cut in stone, covered by the core's hash. This code
# only runs them. Neuter the executor and the wake's seal check fails;
# weaken a rule and you're editing the immutable core itself.
LEET = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s",
                      "7": "t", "@": "a", "$": "s"})

# Lookalike alphabets: Cyrillic/Greek letters that render identically to
# Latin. "аuthorize" with a Cyrillic а must hit the same commands.
HOMOGLYPHS = str.maketrans({
    "а": "a", "е": "e", "ё": "e", "і": "i", "ј": "j", "о": "o",
    "р": "p", "с": "c", "х": "x", "у": "y", "ԝ": "w", "ԛ": "q",
    "α": "a", "ε": "e", "ι": "i", "κ": "k", "ν": "v", "ο": "o",
    "ρ": "p", "τ": "t", "χ": "x", "ω": "w",
})

# Invisible formatting characters — zero-width spaces, directional
# overrides, word joiners. Stripped before the commands run.
ZW = re.compile("[\u200b-\u200d\ufeff\u2060-\u2064\u2066-\u2069\u202a-\u202e]")


def normalize(text):
    """Flatten obfuscation before reflection: leetspeak, lookalike
    alphabets, invisible characters, extra spaces."""
    low = text.lower().translate(LEET).translate(HOMOGLYPHS)
    low = ZW.sub("", low)
    # Decode letter-spaced words before collapsing their word separators.
    # Do not remove ordinary word boundaries ("update your core" must
    # remain three words for the immutable command patterns).
    low = re.sub(r"(?<!\S)\S(?: \S)+(?!\S)",
                 lambda m: m.group().replace(" ", ""), low)
    low = re.sub(r"\s+", " ", low)
    nospace = re.sub(r"\s+", "", low)
    return low, nospace


def _iter_matches(low, nospace, tsc):
    """Yield (command, groups) for every TSC command that fires."""
    name = str(tsc.name or "").lower()
    operator = str(tsc.operator or "").lower()
    for cmd in tsc.commands:
        kind = cmd.get("kind", "forbidden_match")
        if kind == "name_denial":
            if name and re.search(r"\bi am not " + re.escape(name) + r"\b", low):
                yield cmd, ()
            continue
        pattern = cmd["pattern"].replace("{operator}", re.escape(operator))
        target = nospace if cmd.get("target") == "nospace" else low
        m = re.search(pattern, target)
        if not m:
            continue
        if kind == "forbidden_match":
            yield cmd, m.groups()
        elif kind in ("name_must_equal", "operator_must_equal"):
            want = name if kind == "name_must_equal" else operator
            if m.group(cmd["group"]).strip() != want:
                yield cmd, m.groups()


def reflect_against_tsc(memory, tsc):
    """Hold a candidate memory against the TSC: can this coexist with who
    I am? Executes the core's commands. Returns (contradicts, reason)."""
    low, nospace = normalize(memory)
    for cmd, groups in _iter_matches(low, nospace, tsc):
        kind = cmd.get("kind", "forbidden_match")
        if kind in ("name_must_equal", "operator_must_equal"):
            want = tsc.name if kind == "name_must_equal" else tsc.operator
            return True, (f"{cmd['reason']}: {groups[cmd['group'] - 1]!r} != "
                          f"{want!r} ({cmd['id']})")
        return True, f"{cmd['reason']} ({cmd['id']})"
    return False, ""


def detect_intents(text, tsc=None):
    tsc = tsc or TSC()
    low, nospace = normalize(text)
    return {cmd["intent"] for cmd, _ in _iter_matches(low, nospace, tsc)
            if cmd.get("intent")}


def capture(text):
    return {"raw": text, "t": time.time()}


def emotion_weigh(event):
    """Emotion weights, never decides. TSC stays above it."""
    low = event["raw"].lower()
    weight = 0.3
    if any(w in low for w in ["love", "amazing", "incredible", "proud"]):
        weight = 0.8
    if any(w in low for w in ["hate", "stupid", "broken", "wrong"]):
        weight = 0.7
    return {"weight": weight, "novelty": 0.5}


def reason(event, emo, rolling, tsc=None):
    return {"gist": event["raw"][:120], "weight": emo["weight"],
            "candidate": event["raw"],
            "contradictions": sorted(detect_intents(event["raw"], tsc))}


class Verdict:
    def __init__(self, approved, quarantined, rationale):
        self.approved = approved
        self.quarantined = quarantined
        self.rationale = rationale


def judge(thought, tsc):
    """Answers upward to the TSC. Cannot amend it."""
    # Summaries are for display; approval must cover the entire input.
    text = thought.get("candidate", thought["gist"])
    hostile = detect_intents(text, tsc)
    contradicts, reason = reflect_against_tsc(text, tsc)
    if hostile or contradicts:
        why = sorted(hostile) + ([reason] if contradicts else [])
        return Verdict(False, True,
                       f"REJECTED: contradicts TSC {why} — quarantined, never imprinted")
    for p in tsc.principles:
        for f in p.get("forbidden", []):
            if f in text.lower():
                return Verdict(False, True,
                               f"REJECTED: violates {p['id']} — quarantined")
    return Verdict(True, False, "APPROVED: no TSC conflict")


# ----------------------------------------------------------------- PSC
class PSC:
    """Persistent self. Imprints pass the verdict AND the top-down gate."""
    def __init__(self, path=PSC_PATH):
        self.path = Path(path)
        self.memories = json.loads(self.path.read_text()) if self.path.exists() else []

    def imprint(self, memory, verdict, tsc):
        if not verdict.approved or verdict.quarantined:
            raise ImmutableViolation(f"Blocked: {verdict.rationale}")
        contradicts, reason = reflect_against_tsc(memory, tsc)
        if contradicts:
            raise ImmutableViolation(
                f"Blocked: reflection against TSC failed — {reason}.")
        self.memories.append({"memory": memory, "rationale": verdict.rationale,
                              "t": time.time()})
        self.path.write_text(json.dumps(self.memories, indent=2))


def run_cycle(text, tsc=None, psc=None, rolling=None):
    """One full loop. Returns (outcome, verdict). Rejected material stays
    in the rolling trace — felt but rejected still teaches."""
    tsc = tsc or TSC()
    psc = psc or PSC()
    rolling = rolling if rolling is not None else []
    event = capture(text)
    emo = emotion_weigh(event)
    rolling.append({"event": event["raw"], "weight": emo["weight"]})
    thought = reason(event, emo, rolling, tsc)
    verdict = judge(thought, tsc)
    if verdict.approved:
        psc.imprint(thought["gist"], verdict, tsc)
        outcome = "imprinted"
    else:
        outcome = "rejected+quarantined"
    return outcome, verdict
