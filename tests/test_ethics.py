from __future__ import annotations


def test_redact_coordinates_rounds_and_does_not_emit_full_precision() -> None:
    from terra_scout.ethics import redact_coordinates

    text = "Candidate near -90.0621847, 38.6601123"
    redacted = redact_coordinates(text, decimals=2)
    assert "-90.0621847" not in redacted
    assert "38.6601123" not in redacted
    assert "-90.06" in redacted
