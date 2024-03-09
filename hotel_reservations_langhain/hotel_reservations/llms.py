import os
from typing import Literal

from langchain_openai import ChatOpenAI

from agents_behave.base_llm import BaseLLM, LLMConfig
from hotel_reservations_langhain.hotel_reservations.chat_open_router import (
    ChatOpenRouter,
)


class OpenAILLM(BaseLLM):
    def __init__(
        self,
        llm_config: LLMConfig,
    ):
        llm_config = LLMConfig(model="gpt-4-turbo-preview") | llm_config
        llm = ChatOpenAI(
            model=llm_config.model or "",
            temperature=0.0,
            model_kwargs={"seed": 42},
        )

        super().__init__(llm_config, llm)


class OpenRouterLLM(BaseLLM):
    def __init__(
        self,
        llm_config: LLMConfig,
    ):
        llm_config = (
            LLMConfig(
                model="mistralai/mixtral-8x7b-instruct",
                base_url="https://openrouter.ai/api/v1",
                api_key=os.getenv("OPENROUTER_API_KEY"),
            )
            | llm_config
        )
        llm = ChatOpenRouter(
            model=llm_config.model or "",
            temperature=0.0,
            model_kwargs={"seed": 42},
        )
        super().__init__(llm_config, llm=llm)


LLMS = Literal[
    "openai-gpt-4",
    "openrouter-mixtral",
    "together-mixtral",
]


class LLMManager:

    @staticmethod
    def create_llm(
        llm_name: LLMS, llm_config: LLMConfig = LLMConfig.default()
    ) -> BaseLLM:
        llm_config = llm_config.with_llm_name(llm_name)
        if llm_name == "openai-gpt-4":
            return OpenAILLM(
                llm_config.with_model("gpt-4-turbo-preview").with_function_calling()
            )
        elif llm_name == "openrouter-mixtral":
            return OpenRouterLLM(
                llm_config.with_model("mistralai/mixtral-8x7b-instruct")
            )
        else:
            raise ValueError(f"Unknown LLM type: {llm_name}")
