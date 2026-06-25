"""
fix_livekit_bug.py
Run ONCE: python fix_livekit_bug.py

Patches the livekit-agents chat_context.py bug where the serializer calls
.audio on a plain string system prompt, causing:
  AttributeError: 'str' object has no attribute 'audio'

This is a bug in livekit-agents 1.6.3 and 1.6.4.
"""
import sys
import site
from pathlib import Path


def find_chat_context():
    for sp in site.getsitepackages():
        p = Path(sp) / "livekit" / "agents" / "llm" / "chat_context.py"
        if p.exists():
            return p
    # Also check venv site-packages
    for p in Path(sys.executable).parent.parent.rglob("livekit/agents/llm/chat_context.py"):
        return p
    return None


BUGGY_LINE   = '    d: dict[str, Any] = {"type": "instructions", "audio": v.audio}'
FIXED_LINES  = '''\
    if isinstance(v, str):
        d: dict[str, Any] = {"type": "instructions", "text": v}
    else:
        d: dict[str, Any] = {"type": "instructions", "audio": v.audio}\
'''

BUGGY_BLOCK  = (
    "        if v is not None:\n"
    "    d: dict[str, Any] = {\"type\": \"instructions\", \"audio\": v.audio}\n"
)


def patch(path: Path) -> None:
    text = path.read_text(encoding="utf-8")

    if FIXED_LINES in text:
        print(f"[fix_livekit_bug] Already patched: {path}")
        return

    if BUGGY_LINE not in text:
        print(f"[fix_livekit_bug] Buggy line not found — file may have changed.\n  Path: {path}")
        print("  Printing lines 160-175 for inspection:")
        lines = text.splitlines()
        for i, line in enumerate(lines[159:175], start=160):
            print(f"    {i}: {line}")
        sys.exit(1)

    patched = text.replace(BUGGY_LINE, FIXED_LINES)
    path.write_text(patched, encoding="utf-8")
    print(f"[fix_livekit_bug] Patched successfully: {path}")


if __name__ == "__main__":
    target = find_chat_context()
    if not target:
        print("[fix_livekit_bug] Could not find chat_context.py in venv. "
              "Make sure you run this with the .venv Python.")
        sys.exit(1)
    print(f"[fix_livekit_bug] Found: {target}")
    patch(target)
    print("[fix_livekit_bug] Done. You can now run: python agent_worker.py dev")