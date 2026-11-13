from __future__ import annotations

import re

_COORDINATE_PATTERN = re.compile(r"(-?\d{1,3}\.\d{3,})")


def redact_coordinates(text: str, decimals: int = 2) -> str:
    """Round high-precision coordinates in prose so logs and LLM prompts stay coarse."""

    def _replace(match: re.Match[str]) -> str:
        value = float(match.group(1))
        return f"{value:.{decimals}f}"

    return _COORDINATE_PATTERN.sub(_replace, text)


def llm_may_receive_precise_coordinates(enabled: bool) -> bool:
    return bool(enabled)
