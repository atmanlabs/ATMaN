"""Configuration and Permission Fence manager for EXO Live.

Enforces that every capability and loop action stays strictly behind
the permission fence. Zero external dependencies required.
"""
from pathlib import Path
from types import MappingProxyType
import re

HERE = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = HERE / "config.yaml"


def _parse_scalar(val: str):
    v = val.strip()
    if not v:
        return ""
    if v.lower() == "true":
        return True
    if v.lower() == "false":
        return False
    if v.lower() == "null" or v == "~":
        return None
    if re.fullmatch(r"[-+]?\d+", v):
        return int(v)
    if re.fullmatch(r"[-+]?\d*\.\d+(?:[eE][-+]?\d+)?", v):
        return float(v)
    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
        return v[1:-1]
    return v


try:
    import yaml
    _HAVE_YAML = True
except ImportError:
    _HAVE_YAML = False


def parse_simple_yaml(text: str) -> dict:
    """YAML parser for nested mappings, lists, and scalars with pure-Python fallback."""
    if _HAVE_YAML:
        try:
            loaded = yaml.safe_load(text)
            if isinstance(loaded, dict):
                return loaded
            return {}
        except Exception:
            pass

    # Pure-Python fallback
    cleaned = []
    for raw_line in text.splitlines():
        line_no_comment = ""
        in_quote = False
        quote_char = ""
        for char in raw_line:
            if char in ('"', "'"):
                if not in_quote:
                    in_quote = True
                    quote_char = char
                elif quote_char == char:
                    in_quote = False
            elif char == "#" and not in_quote:
                break
            line_no_comment += char

        stripped = line_no_comment.strip()
        if stripped:
            indent = len(raw_line) - len(raw_line.lstrip())
            cleaned.append((indent, stripped))

    root = {}
    stack = [(-1, root)]

    for i, (indent, stripped) in enumerate(cleaned):
        next_is_list = False
        if i + 1 < len(cleaned):
            next_indent, next_stripped = cleaned[i + 1]
            if next_stripped.startswith("- ") and next_indent > indent:
                next_is_list = True

        if stripped.startswith("- "):
            while stack and (indent < stack[-1][0] or (indent == stack[-1][0] and not isinstance(stack[-1][1], list))):
                stack.pop()
        else:
            while stack and indent <= stack[-1][0]:
                stack.pop()

        parent_indent, parent_container = stack[-1]

        if stripped.startswith("- "):
            item_val = stripped[2:].strip()
            if isinstance(parent_container, list):
                parent_container.append(_parse_scalar(item_val))
        elif ":" in stripped:
            k, v = stripped.split(":", 1)
            k = k.strip()
            v = v.strip()
            if not v:
                if next_is_list:
                    new_container = []
                    parent_container[k] = new_container
                    next_indent = cleaned[i + 1][0]
                    stack.append((next_indent, new_container))
                else:
                    new_container = {}
                    parent_container[k] = new_container
                    stack.append((indent, new_container))
            else:
                parent_container[k] = _parse_scalar(v)

    return root


def freeze_config(val):
    if isinstance(val, dict):
        return MappingProxyType({k: freeze_config(v) for k, v in val.items()})
    if isinstance(val, list):
        return tuple(freeze_config(v) for v in val)
    return val


class PermissionFenceError(Exception):
    """Raised when an operation attempts to breach the permission fence."""
    pass


class Config:
    """Immutable configuration and permission fence representation."""

    def __init__(self, path: Path | str = DEFAULT_CONFIG_PATH):
        self.path = Path(path)
        if self.path.exists():
            content = self.path.read_text(encoding="utf-8")
            raw_data = parse_simple_yaml(content)
        else:
            raw_data = {}
        self._data = freeze_config(raw_data)

    def get(self, *keys, default=None):
        curr = self._data
        for k in keys:
            if isinstance(curr, (dict, MappingProxyType)) and k in curr:
                curr = curr[k]
            else:
                return default
        return curr

    @property
    def mind(self):
        return self._data.get("mind", {})

    @property
    def drives(self):
        return self._data.get("drives", {})

    @property
    def permissions(self):
        return self._data.get("permissions", {})

    @property
    def storage(self):
        return self._data.get("storage", {})

    def is_action_permitted(self, action_name: str) -> bool:
        """Check if action is explicitly permitted by the permission fence."""
        actions = self.permissions.get("actions", {})
        return bool(actions.get(action_name, False))

    def is_tool_permitted(self, tool_name: str) -> bool:
        """Check if tool is in the allowed list and not in denied list."""
        tools = self.permissions.get("tools", {})
        allowed = tools.get("allowed", ())
        denied = tools.get("denied", ())
        if tool_name in denied:
            return False
        return tool_name in allowed

    def check_action(self, action: dict) -> tuple[bool, str]:
        """Validate action against permission fence. Returns (allowed, rationale)."""
        action_type = action.get("type", "unknown")
        if not self.is_action_permitted(action_type):
            return False, f"Permission fence blocked unauthorized action '{action_type}'"

        tool_target = action.get("tool")
        if tool_target and not self.is_tool_permitted(tool_target):
            return False, f"Permission fence blocked unauthorized tool '{tool_target}'"

        return True, f"Action '{action_type}' permitted by fence"
