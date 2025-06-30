import os
from types import SimpleNamespace

# We can use pydantic for these configs. OR, we can do it old school.


# Grab keys and provider choice
_openai = os.getenv("OPENAI_API_KEY")
_anthropic = os.getenv("ANTHROPIC_API_KEY")
_google = os.getenv("GOOGLE_API_KEY")
_provider = os.getenv("LLM_PROVIDER", "openai").lower()

# Bundle into a single object for import
settings = SimpleNamespace(
    openai_api_key=_openai,
    anthropic_api_key=_anthropic,
    google_api_key=_google,
    default_provider=_provider,
)
