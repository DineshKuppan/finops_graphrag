import os
from typing import Optional

import instructor
import openai

from src.domain import FinOpsContractGraph
from src.interfaces.llm_extractor import ILlmExtractor


class LiteLLMInstructorExtractor(ILlmExtractor):
    """Structured extraction against a local LiteLLM proxy serving Llama models.

    The LiteLLM proxy (https://docs.litellm.ai/docs/proxy/quick_start) exposes
    an OpenAI-compatible `/chat/completions` API in front of local models
    (Ollama, vLLM, llama.cpp, etc.), so the stock `openai` client just needs
    to be pointed at the proxy's `base_url` — no OpenAI account or API key
    involved. `model` must match the model name configured in the proxy's
    `config.yaml` (e.g. "llama3", "ollama/llama3").
    """

    def __init__(
        self,
        model: str = "llama3",
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        base_client = openai.OpenAI(
            base_url=base_url or os.getenv("LITELLM_PROXY_URL", "http://localhost:4000"),
            # LiteLLM proxy ignores the key's value unless you've configured
            # virtual keys/auth on the proxy — a placeholder is fine locally.
            api_key=api_key or os.getenv("LITELLM_API_KEY", "sk-local"),
        )
        self.client = instructor.from_openai(base_client)
        self.model = model

    def extract_structured_data(self, text: str) -> FinOpsContractGraph:
        return self.client.chat.completions.create(
            model=self.model,
            response_model=FinOpsContractGraph,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a FinOps Graph extraction expert. Parse all metadata, penalties, "
                        "lease components, and financial terms. Carefully segregate them into either "
                        "'REALTY' or 'Subscription' domains based on text essence."
                    )
                },
                {"role": "user", "content": text}
            ]
        )
