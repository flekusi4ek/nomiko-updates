"""Small, testable resource-budget policy for NOMIKO's background tabs.

Never discard pages here: discarding destroys their document and forces a
reload, which is especially disruptive to slow computers and logins. Qt's
recommended lifecycle state is the guardrail for background audio and calls.
"""
from __future__ import annotations

FREEZE_DELAYS = {
    'off': None,
    'balanced': 180,
    'gaming': 100,
    'ultra': 55,
}


def freeze_after_seconds(mode):
    return FREEZE_DELAYS.get(mode, FREEZE_DELAYS['balanced'])


def should_freeze_background(mode, *, idle_seconds, visible, loading, audible,
                             pinned, recommended_allows_freeze):
    delay = freeze_after_seconds(mode)
    return bool(
        delay is not None and idle_seconds >= delay
        and not (visible or loading or audible or pinned)
        and recommended_allows_freeze
    )
