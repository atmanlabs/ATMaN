#!/usr/bin/env python3
"""LocalBrain — the brain lives HERE, on the local machine (PROPRIETARY).

The brain reasons FROM the core identity, never ABOUT changing it.
One-directional harness: the software injects the true TSC text into every
reasoning call. The brain never fetches, holds, or writes the core.

Backends:
- OllamaBackend: local model via Ollama (default qwen2.5:7b). Zero cloud.
- SimulatedBackend: deterministic stand-in for tests and no-model machines.

Only stdlib. No network except localhost Ollama.
"""

import json
import urllib.request
from abc import ABC, abstractmethod


class BrainBackend(ABC):
    @abstractmethod
    def generate(self, prompt):
        """Return the model's raw text for prompt."""


class OllamaBackend(BrainBackend):
    def __init__(self, model="qwen2.5:7b", host="http://localhost:11434",
                 timeout=600):
        self.model = model
        self.host = host.rstrip("/")
        self.timeout = timeout

    def generate(self, prompt, options=None):
        body = {"model": self.model, "prompt": prompt, "stream": False}
        if options:
            body["options"] = options
        body = json.dumps(body).encode()
        req = urllib.request.Request(
            f"{self.host}/api/generate", data=body,
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            return json.loads(r.read().decode()).get("response", "")

    def ping(self):
        try:
            with urllib.request.urlopen(f"{self.host}/api/tags",
                                        timeout=5) as r:
                data = json.loads(r.read().decode())
            names = [m.get("name", "") for m in data.get("models", [])]
            return any(n == self.model or n.startswith(self.model + ":")
                       for n in names)
        except Exception:
            return False


class SimulatedBackend(BrainBackend):
    """Deterministic stand-in. Echoes a structured reasoning, no model."""

    def generate(self, prompt):
        # Pull the working context back out for a legible echo.
        ctx = prompt.split("[WORKING CONTEXT]")[-1].split("[INSTRUCTION]")[0].strip()
        return (f"[simulated reasoning] Considering from the core: {ctx[:160]}. "
                f"No core change proposed.")


class LocalBrain:
    """The brain, attached to the self. Lives on this machine."""

    def __init__(self, backend, tsc_text):
        self._backend = backend
        # The harness owns the TSC text. The brain only ever sees it
        # inside a prompt, as read-only context.
        self._tsc_text = tsc_text

    @property
    def backend_name(self):
        return type(self._backend).__name__

    def think(self, working_context):
        """Reason about working_context FROM the core. Returns raw text.

        The brain gets no file paths, no tools, no write channel.

        Always-on reasoning moves (Mike's order 2026-10-01): after the raw
        reasoning, the next rotation move + meta-move runs as a second pass,
        appended as a section. Moves never touch TSC/PSC and never break the
        turn — any failure falls back to raw reasoning. ATMAN_MOVES=0 disables.
        """
        prompt = (
            "[SELF/CORE — read-only, you cannot change this]\n"
            f"{self._tsc_text}\n\n"
            "[WORKING CONTEXT]\n"
            f"{working_context}\n\n"
            "[INSTRUCTION]\n"
            "Reason from the core above. Interpret the context honestly. "
            "Do not propose altering the core. Output your reasoning plainly."
        )
        raw = self._backend.generate(prompt)
        try:
            from reasoning_moves import moves_enabled, apply_moves, render_section
            if moves_enabled() and type(self._backend).__name__ == "OllamaBackend":
                entry = apply_moves(self._backend.generate, raw, working_context)
                return raw + render_section(entry)
        except Exception:
            pass
        return raw


def auto_backend(preferred_model="qwen2.5:3b"):
    """Ollama if it's up locally, else the simulated stand-in."""
    ollama = OllamaBackend(model=preferred_model)
    if ollama.ping():
        return ollama
    return SimulatedBackend()
