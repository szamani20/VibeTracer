import os
from types import SimpleNamespace

# We can use pydantic for these configs. OR, we can do it old school.


# Grab keys and provider choice
_openai = os.getenv("OPENAI_API_KEY")
_anthropic = os.getenv("ANTHROPIC_API_KEY")
_google = os.getenv("GOOGLE_API_KEY")
_provider = os.getenv("LLM_PROVIDER", "openai").lower()

# Validate
_allowed = {"openai", "anthropic", "google"}
if _provider not in _allowed:
    raise ValueError(f"LLM_PROVIDER must be one of {_allowed}; got '{_provider}'")

if _provider == "openai" and not _openai:
    raise ValueError("Must set OPENAI_API_KEY when LLM_PROVIDER=openai")
if _provider == "anthropic" and not _anthropic:
    raise ValueError("Must set ANTHROPIC_API_KEY when LLM_PROVIDER=anthropic")
if _provider == "google" and not _google:
    raise ValueError("Must set GOOGLE_API_KEY when LLM_PROVIDER=google")

# Bundle into a single object for import
settings = SimpleNamespace(
    openai_api_key=_openai,
    anthropic_api_key=_anthropic,
    google_api_key=_google,
    default_provider=_provider,
)
