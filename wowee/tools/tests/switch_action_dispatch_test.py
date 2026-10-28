#!/usr/bin/env python3
"""Keep every Switch action-bar tier on the direct UseAction path."""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
engine = (ROOT / "src/addons/lua_engine.cpp").read_text()
profile = (ROOT / "addons/ConsolePort/Controllers/SWITCH/Switch.lua").read_text()
init = (ROOT / "addons/ConsolePort/Init/Init.lua").read_text()


def body(source: str, signature: str) -> str:
    start = source.index(signature)
    opening = source.index("{", start)
    depth, end = 1, opening + 1
    while depth:
        depth += (source[end] == "{") - (source[end] == "}")
        end += 1
    return source[start:end]


dispatch = body(engine, "bool LuaEngine::dispatchBindingKey(")
action_start = dispatch.index("// 3. Action bar slots")
action_end = dispatch.index("// Left alone if the client performs it", action_start)
action = dispatch[action_start:action_end]

# All four multi bars must map to their real global slot ranges.
for prefix, base in (
    ("MULTIACTIONBAR1BUTTON", 60),
    ("MULTIACTIONBAR2BUTTON", 48),
    ("MULTIACTIONBAR3BUTTON", 24),
    ("MULTIACTIONBAR4BUTTON", 36),
):
    assert f'{{"{prefix}", {base}}}' in engine

# The old regression only took multi-bar ownership while GetCursorInfo was
# non-nil, then sent ordinary presses into hidden Blizzard button scripts.
assert "bool takeOver" not in action
assert "lua_pcall" not in action
assert "if (slot >= 1 && slot <= 120)" in action
assert "elseif UseAction then UseAction(s) end" in action
assert 'outcome = down ? "action" : "action-release"' in action
assert re.search(r"if \(down\).*?executeString\(.*?return true;", action, re.S)

# ZR's four face buttons are a contiguous, visible four-slot action tier. An
# encounter-only ExtraActionButton is not a usable fourth handheld slot.
ctrl_actions = dict(re.findall(
    r"\['(CP_R_(?:UP|DOWN|LEFT|RIGHT))'\]\s*=\s*\{(.*?)\n\s*\},",
    profile,
    re.S,
))
expected = {
    "CP_R_LEFT": "MULTIACTIONBAR1BUTTON1",   # Y
    "CP_R_UP": "MULTIACTIONBAR1BUTTON2",     # X
    "CP_R_RIGHT": "MULTIACTIONBAR1BUTTON3",  # A
    "CP_R_DOWN": "MULTIACTIONBAR1BUTTON4",   # B
}
for button, command in expected.items():
    assert re.search(r"\['CTRL-'\]\s*=\s*'" + command + r"'", ctrl_actions[button])
assert "EXTRAACTIONBUTTON1" not in ctrl_actions["CP_R_DOWN"]

# Existing per-character SavedVariables must receive the new ZR+B mapping.
assert "(ConsolePortBindingSet.woweeBindRev or 0) < 8" in init
assert "set.CP_R_DOWN['CTRL-'] = 'MULTIACTIONBAR1BUTTON4'" in init
assert "ConsolePortBindingSet.woweeBindRev = 8" in init

print("PASS Switch action dispatch: all multi-bar tiers use direct UseAction, "
      "releases are consumed, and ZR+B migrates to slot 64")
