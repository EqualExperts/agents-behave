import os
from typing import Literal

from langchain_openai import ChatOpenAI

from agents_behave.base_llm import BaseLLM, LLMConfig
from hotel_reservations.chat_open_router import ChatOpenRouter


class OpenAILLM(BaseLLM):
    def __init__(
        self,
        llm_config: LLMConfig,
    ):
        llm_config = LLMConfig(model="gpt-3.5-turbo") | llm_config
        llm = ChatOpenAI(
            model=llm_config.model or "",
            temperature=0.0,
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
        )
        super().__init__(llm_config, llm=llm)


LLM_NAMES = Literal[
    "openai-gpt-3.5",
    "openai-gpt-4",
    "openrouter-mixtral",
    "together-mixtral",
]


class LLMManager:

    @staticmethod
    def create_llm(
        llm_name: LLM_NAMES, llm_config: LLMConfig = LLMConfig.default()
    ) -> BaseLLM:
        llm_config = llm_config.with_llm_name(llm_name)
        if llm_name == "openai-gpt-3.5":
            return OpenAILLM(
                llm_config.with_model("gpt-3.5-turbo").with_function_calling()
            )

        elif llm_name == "openai-gpt-4":
            return OpenAILLM(
                llm_config.with_model("gpt-4-turbo-preview").with_function_calling()
            )
        elif llm_name == "openrouter-mixtral":
            return OpenRouterLLM(
                llm_config.with_model("mistralai/mixtral-8x7b-instruct")
            )
        else:
            raise ValueError(f"Unknown LLM type: {llm_name}")
