from typing import Literal
from vibetracer.llm.prompt_template import PROMPT_TEMPLATE
from vibetracer.llm.config import load_settings
from openai import OpenAI
import anthropic
from google import genai


class Fixer:
    """
    Analyze a tracer report string with an LLM and return a structured audit in markdown format.
    Supports OpenAI, Anthropic Claude, and Google Gemini.
    """

    def __init__(self,
                 provider: Literal["openai", "anthropic", "google"] = 'openai',
                 temperature: float = 0.2,
                 max_tokens: int = 100000):
        self.provider = provider
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.clients = {}

    def _initialize_clients(self):
        if self.clients.get(self.provider) is not None:
            return

        settings = load_settings()
        self._validate_configs(settings)

        # Initialize clients
        if self.provider == "openai":
            self.clients[self.provider] = OpenAI(api_key=settings.openai_api_key)
        elif self.provider == "anthropic":
            self.clients[self.provider] = anthropic.Client(api_key=settings.anthropic_api_key)
        elif self.provider == "google":
            self.clients[self.provider] = genai.Client(api_key=settings.google_api_key)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    @staticmethod
    def _validate_configs(settings):
        # Validate
        _allowed = {"openai", "anthropic", "google"}
        provider = settings.default_provider
        if provider not in _allowed:
            raise ValueError(f"LLM_PROVIDER must be one of {_allowed}; got '{provider}'")

        if provider == "openai" and settings.openai_api_key is None:
            raise ValueError("Must set OPENAI_API_KEY when LLM_PROVIDER=openai")
        if provider == "anthropic" and settings.anthropic_api_key is None:
            raise ValueError("Must set ANTHROPIC_API_KEY when LLM_PROVIDER=anthropic")
        if provider == "google" and settings.google_api_key is None:
            raise ValueError("Must set GOOGLE_API_KEY when LLM_PROVIDER=google")

    def analyze(self, report: str) -> str:
        """
        Send the report to the chosen LLM and return its response string.
        """
        self._initialize_clients()

        prompt = PROMPT_TEMPLATE.format(report=report)

        if self.provider == "openai":
            resp = self.clients[self.provider].chat.completions.create(
                model="o4-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt},
                ],
                # temperature=self.temperature,
                max_completion_tokens=self.max_tokens,
            )
            return resp.choices[0].message.content

        elif self.provider == "anthropic":
            # Claude requires a single prompt; we prefix with system instructions if desired
            full = f"{anthropic.HUMAN_PROMPT} {prompt}{anthropic.AI_PROMPT}"
            resp = self.clients[self.provider].completions.create(
                model="claude-3",
                prompt=full,
                temperature=self.temperature,
                max_tokens_to_sample=self.max_tokens,
            )
            return resp.completion

        elif self.provider == "google":
            # Gemini usage
            resp = self.clients[self.provider].chat.completions.create(
                model="gemini-2.5-pro",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt},
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            return resp.choices[0].message.content

        else:
            raise RuntimeError("No valid LLM provider configured.")
