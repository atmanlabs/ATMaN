"""Build project-atman.zip from atman-live without private core secrets."""
from __future__ import annotations
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent / "project-atman.zip"

DENY_NAMES = {
    "psc.json",
    "psc.json.lock",
    "significant_events.json",
    ".env",
    "stage1-seal.json",
    "tsc.atman.private.json",
    "operator_auth.json",
    "auth_store.json",
    "queue.json",
    "ledger.jsonl",
    "scoreboard.json",
    "freeplay_state.json",
    "changes_index.json",
    "FAILURES.jsonl",
    "skills.json",
}
DENY_SUFFIXES = (".pyc", ".pyo", ".log", ".bak")
DENY_DIRS = {
    "__pycache__",
    ".git",
    "node_modules",
    "voices",
    "dist",
    "build",
    ".venv",
    "venv",
    "atman-private",
    "backups",
    "sandbox",
    "proposals",
}

INCLUDE_TOP = {
    ".gitignore",
    "ARCHITECTURE.md",
    "README.md",
    "ATMAN-SCAFFOLD-HANDOFF.md",
    "build_desktop.py",
    "cockpit.py",
    "config.py",
    "config.yaml",
    "core.py",
    "crate.py",
    "desktop.py",
    "desktop_worker.py",
    "drives.py",
    "episode_segmenter.py",
    "evolving_brain.py",
    "atman_core.py",
    "atman_icon.ico",
    "atman_icon.png",
    "gate_policy.json",
    "governor.py",
    "load_knowledge_bootstrap.py",
    "loop.py",
    "minecraft_chat.py",
    "minecraft_context.py",
    "observer.py",
    "operator_auth.py",
    "reason.py",
    "relay.py",
    "seal.py",
    "senses.py",
    "significant_events.py",
    "skills.py",
    "sleep.py",
    "sweep.py",
    "tsc.template.json",
    "voice.py",
    "wake.py",
    "working_context.py",
    "onboard.py",
    "llms.txt",
    "pack_public_scaffold.py",
    "SOUP-PHASE0-ARCHITECTURE.md",
    "SOUP-PHASE1-PROFILE.md",
    "SOUP-PHASE2-CHANGELOG.md",
    "SOUP-PHASE2-WFC-MEASURE.md",
    "SOUP-PHASE2-WFC-AFTER.md",
    "SOUP-PHASE3-CHANGELOG.md",
    "SOUP-PHASE3-FREEPLAY.md",
    "SOUP-SELF-UPGRADE.md",
}


def denied(path: Path) -> bool:
    if path.name in DENY_NAMES:
        return True
    if any(path.name.endswith(suf) for suf in DENY_SUFFIXES) or path.suffix.lower() in DENY_SUFFIXES:
        return True
    if ".bak-" in path.name:
        return True
    parts = set(path.parts)
    if parts & DENY_DIRS:
        return True
    return False


def collect() -> list[Path]:
    files: list[Path] = []
    for name in sorted(INCLUDE_TOP):
        p = ROOT / name
        if p.is_file() and not denied(p):
            files.append(p)
    for p in sorted(ROOT.glob("test_*.py")):
        if p.is_file() and not denied(p):
            files.append(p)
    for folder in ("adapters", "guardian", "ui", "extensions", "self_improve"):
        base = ROOT / folder
        if not base.exists():
            continue
        for p in sorted(base.rglob("*")):
            if p.is_file() and not denied(p):
                files.append(p)
    seen = set()
    out = []
    for p in files:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def main() -> None:
    files = collect()
    extras = [
        ("self_improve/CHANGELOG.md", "# ATMAN Self-Improve Changelog\\n\\n"),
        ("self_improve/proposals/.gitkeep", ""),
        ("self_improve/backups/.gitkeep", ""),
        ("self_improve/sandbox/.gitkeep", ""),
    ]
    if OUT.exists():
        OUT.unlink()
    with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        written = set()
        for p in files:
            arc = str(p.relative_to(ROOT)).replace("\\", "/")
            zf.write(p, arcname=arc)
            written.add(arc)
        for arc, data in extras:
            if arc not in written:
                zf.writestr(arc, data)
    print(f"Wrote {OUT} ({OUT.stat().st_size} bytes) files={len(files)}")
    with zipfile.ZipFile(OUT, "r") as zf:
        names = zf.namelist()
    bad = [n for n in names if any(x in n.lower() for x in ("tsc.atman.private", "stage1-seal", "psc.json", ".env", "atman-private"))]
    if bad:
        raise SystemExit(f"REFUSING: private paths in zip: {bad}")
    must = ["working_context.py", "self_improve/engine.py", "self_improve/safety.py", "self_improve/freeplay_proposer.py", "ATMAN-SCAFFOLD-HANDOFF.md"]
    missing = [m for m in must if m not in names]
    if missing:
        raise SystemExit(f"REFUSING: missing required public files: {missing}")
    print("private-core scan: clean")
    print("required soup/self_improve: present")
    print("entries:", len(names))


if __name__ == "__main__":
    main()
