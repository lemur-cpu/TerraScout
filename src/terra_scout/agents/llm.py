from __future__ import annotations

from terra_scout.config import Settings, get_settings


class LanguageModelClient:
    """Optional prose helper. Detection and geospatial tools never require this."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    @property
    def is_configured(self) -> bool:
        return bool(self.settings.llm_api_key or self.settings.ollama_host)

    def complete(self, prompt: str) -> str | None:
        if not self.is_configured:
            return None
        if not self.settings.send_precise_coordinates_to_llm:
            from terra_scout.ethics import redact_coordinates

            prompt = redact_coordinates(prompt)
        # External providers are opt-in; the MVP records that no completion ran
        # unless a later adapter is wired. Do not fabricate model text.
        return None
