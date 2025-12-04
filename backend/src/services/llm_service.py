"""Hybrid LLM service supporting cloud and local LLMs."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Literal
import structlog

from src.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


class LLMProvider(ABC):
    """Abstract LLM provider interface."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate text from prompt."""
        pass

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
    ):
        """Generate streaming response."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get provider name."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI GPT-4o provider."""

    def __init__(self):
        """Initialize OpenAI provider."""
        self.api_key = settings.OPENAI_API_KEY
        self.model = "gpt-4o"
        self.client = None

    async def _get_client(self):
        """Lazy load OpenAI client."""
        if self.client is None:
            try:
                from openai import AsyncOpenAI

                self.client = AsyncOpenAI(api_key=self.api_key)
                logger.info("OpenAI client initialized", model=self.model)
            except ImportError:
                raise ImportError("openai package is not installed")

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate text using OpenAI."""
        await self._get_client()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return response.choices[0].message.content

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
    ):
        """Generate streaming response."""
        await self._get_client()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return "openai"


class AnthropicProvider(LLMProvider):
    """Anthropic Claude 3.5 provider."""

    def __init__(self):
        """Initialize Anthropic provider."""
        self.api_key = settings.ANTHROPIC_API_KEY
        self.model = "claude-3-5-sonnet-20241022"
        self.client = None

    async def _get_client(self):
        """Lazy load Anthropic client."""
        if self.client is None:
            try:
                from anthropic import AsyncAnthropic

                self.client = AsyncAnthropic(api_key=self.api_key)
                logger.info("Anthropic client initialized", model=self.model)
            except ImportError:
                raise ImportError("anthropic package is not installed")

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate text using Anthropic."""
        await self._get_client()

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens or 4096,
            temperature=temperature,
            system=system_prompt or "",
            messages=[{"role": "user", "content": prompt}],
        )

        return response.content[0].text

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
    ):
        """Generate streaming response."""
        await self._get_client()

        stream = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            temperature=temperature,
            system=system_prompt or "",
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        )

        async for event in stream:
            if event.type == "content_block_delta":
                yield event.delta.text

    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return "anthropic"


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider."""

    def __init__(self):
        """Initialize Ollama provider."""
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate text using Ollama."""
        try:
            import httpx

            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": full_prompt,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens,
                        },
                    },
                )
                response.raise_for_status()
                result = response.json()
                return result.get("response", "")
        except Exception as e:
            logger.error("Ollama generation failed", error=str(e))
            raise

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
    ):
        """Generate streaming response."""
        try:
            import httpx

            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

            async with httpx.AsyncClient(timeout=300.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": full_prompt,
                        "stream": True,
                        "options": {"temperature": temperature},
                    },
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line:
                            import json

                            data = json.loads(line)
                            if "response" in data:
                                yield data["response"]
        except Exception as e:
            logger.error("Ollama streaming failed", error=str(e))
            raise

    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return "ollama"


class HybridLLMService:
    """Hybrid LLM service with intelligent routing."""

    def __init__(self):
        """Initialize hybrid LLM service."""
        self.providers: Dict[str, LLMProvider] = {}
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize available LLM providers."""
        # Cloud providers
        if settings.OPENAI_API_KEY:
            self.providers["openai"] = OpenAIProvider()
            logger.info("OpenAI provider initialized")

        if settings.ANTHROPIC_API_KEY:
            self.providers["anthropic"] = AnthropicProvider()
            logger.info("Anthropic provider initialized")

        # Local provider
        if settings.LLM_PROVIDER in ["local", "hybrid"]:
            self.providers["ollama"] = OllamaProvider()
            logger.info("Ollama provider initialized")

    def _estimate_complexity(self, prompt: str) -> Literal["simple", "complex"]:
        """
        Estimate query complexity.

        Args:
            prompt: User prompt

        Returns:
            Complexity level
        """
        # Simple heuristics for complexity estimation
        complex_indicators = [
            "compare",
            "analyze",
            "relationship",
            "difference",
            "multiple",
            "several",
            "complex",
            "interpretation",
            "precedent",
            "case law",
        ]

        prompt_lower = prompt.lower()
        word_count = len(prompt.split())

        # Complex if contains indicators or is long
        if any(indicator in prompt_lower for indicator in complex_indicators):
            return "complex"
        if word_count > 50:
            return "complex"

        return "simple"

    def _select_provider(
        self, complexity: Literal["simple", "complex"], force_provider: Optional[str] = None
    ) -> LLMProvider:
        """
        Select appropriate LLM provider based on complexity.

        Args:
            complexity: Query complexity
            force_provider: Force specific provider (for testing)

        Returns:
            Selected LLM provider
        """
        if force_provider and force_provider in self.providers:
            return self.providers[force_provider]

        provider_type = settings.LLM_PROVIDER.lower()

        if provider_type == "openai":
            return self.providers.get("openai") or self.providers.get("anthropic")
        elif provider_type == "anthropic":
            return self.providers.get("anthropic") or self.providers.get("openai")
        elif provider_type == "local":
            return self.providers.get("ollama")
        elif provider_type == "hybrid":
            # Use local for simple, cloud for complex
            if complexity == "simple" and "ollama" in self.providers:
                return self.providers["ollama"]
            else:
                # Prefer Anthropic, fallback to OpenAI
                return (
                    self.providers.get("anthropic")
                    or self.providers.get("openai")
                    or self.providers.get("ollama")
                )
        else:
            # Default: try cloud first, fallback to local
            return (
                self.providers.get("anthropic")
                or self.providers.get("openai")
                or self.providers.get("ollama")
            )

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        provider: Optional[str] = None,
    ) -> tuple[str, str]:
        """
        Generate text with automatic provider selection.

        Args:
            prompt: User prompt
            system_prompt: System prompt
            temperature: Generation temperature
            max_tokens: Maximum tokens
            provider: Force specific provider

        Returns:
            Tuple of (generated_text, provider_name)
        """
        complexity = self._estimate_complexity(prompt)
        selected_provider = self._select_provider(complexity, provider)

        if not selected_provider:
            raise ValueError("No LLM provider available")

        logger.debug(
            "Generating text",
            provider=selected_provider.provider_name,
            complexity=complexity,
        )

        try:
            text = await selected_provider.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return text, selected_provider.provider_name
        except Exception as e:
            logger.error(
                "Generation failed, trying fallback",
                provider=selected_provider.provider_name,
                error=str(e),
            )

            # Fallback to another provider
            fallback_provider = None
            for name, prov in self.providers.items():
                if prov != selected_provider:
                    fallback_provider = prov
                    break

            if fallback_provider:
                logger.info("Using fallback provider", provider=fallback_provider.provider_name)
                text = await fallback_provider.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return text, fallback_provider.provider_name
            else:
                raise

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        provider: Optional[str] = None,
    ):
        """Generate streaming response."""
        complexity = self._estimate_complexity(prompt)
        selected_provider = self._select_provider(complexity, provider)

        if not selected_provider:
            raise ValueError("No LLM provider available")

        async for chunk in selected_provider.generate_stream(
            prompt=prompt, system_prompt=system_prompt, temperature=temperature
        ):
            yield chunk


# Singleton instance
_llm_service: HybridLLMService | None = None


def get_llm_service() -> HybridLLMService:
    """Get LLM service singleton."""
    global _llm_service
    if _llm_service is None:
        _llm_service = HybridLLMService()
    return _llm_service

