
"""
Shared local Ollama client for SwasthAI.

Used by the Diagnosis Agent and Drug Recommendation Agent.
Uses the model configured in backend.app.core.config.
"""


import json
import logging
import urllib.error
import urllib.request
from typing import Optional

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

  
class OllamaClient:
    """Lightweight HTTP client for the local Ollama API."""

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.model = settings.LOCAL_LLM_MODEL

    def is_available(self) -> bool:
        """Check whether the local Ollama server is responding."""
        try:
            request = urllib.request.Request(
                f"{self.base_url}/api/version"
            )
            with urllib.request.urlopen(request, timeout=5) as response:
                return response.status == 200

        except (urllib.error.URLError, TimeoutError, OSError):
            logger.warning("Ollama server is unavailable.")
            return False

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 500,
        timeout: int = 90,
    ) -> Optional[str]:
        """
        Generate a response from the configured local model.

        Returns:
            Generated text, or None if generation fails.
        """

        if not self.is_available():
            logger.warning("Cannot generate: Ollama is unavailable.")
            return None

        payload = {
            "model": self.model,
            "system": system_prompt,
            "prompt": user_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        try:
            request = urllib.request.Request(
                f"{self.base_url}/api/generate",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            with urllib.request.urlopen(request, timeout=timeout) as response:
                result = json.loads(response.read().decode("utf-8"))

            generated_text = result.get("response", "").strip()

            if not generated_text:
                logger.warning("Ollama returned an empty response.")
                return None

            return generated_text

        except (urllib.error.URLError, TimeoutError, OSError,
                json.JSONDecodeError) as exc:
            logger.exception("Ollama generation failed: %s", exc)
            return None


# Shared client instance for all SwasthAI agents.
ollama_client = OllamaClient()
