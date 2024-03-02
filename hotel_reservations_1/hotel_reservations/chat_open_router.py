import os
from typing import Optional

from langchain_openai import ChatOpenAI


class ChatOpenRouter(ChatOpenAI):
    def __init__(
        self,
        model: str,
        openai_api_key: Optional[str] = None,
        openai_api_base: str = "https://openrouter.ai/api/v1",
        **kwargs,
    ):
        openai_api_key = openai_api_key or os.getenv("OPENROUTER_API_KEY")
        super().__init__(
            openai_api_base=openai_api_base,  # type: ignore
            openai_api_key=openai_api_key,  # type: ignore
            model_name=model,  # type: ignore
            # streaming=False,
            **kwargs,
        )
