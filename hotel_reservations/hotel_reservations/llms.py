import os
from typing import Literal, Optional

from langchain_community.chat_models import ChatOllama
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

from agents_behave.base_llm import BaseLLM, LLMConfig

LLM_NAMES = Literal[
    "openai-gpt-4o",
    "openai-gpt-4",
    "openai-gpt-3.5",
    "groq-llama3-70",
    "groq-llama3-8",
    "ollama-llama3-8",
    "openrouter-mixtral",
    "openrouter-wizardlm2",
    "together-mixtral",
    "fireworks-firefunctions",
]


def create_llm(name: str, llm_name: LLM_NAMES) -> BaseLLM:
    return LLMManager.create_llm(
        llm_name=llm_name,
        llm_config=LLMConfig(
            name=name,
            temperature=0.0,
        ),
    )


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


class GroqLLM(BaseLLM):
    def __init__(
        self,
        llm_config: LLMConfig,
    ):
        llm_config = LLMConfig(model="llama3-70b-8192") | llm_config
        llm = ChatGroq(
            model=llm_config.model or "",
            temperature=0.0,
        )

        super().__init__(llm_config, llm)


class OllamaLLM(BaseLLM):
    def __init__(
        self,
        llm_config: LLMConfig,
    ):
        llm_config = LLMConfig(model="llama3") | llm_config
        llm = ChatOllama(
            model=llm_config.model or "",
            temperature=0.0,
        )

        super().__init__(llm_config, llm)


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


class BaseChatOpenAI(BaseLLM):
    def __init__(
        self,
        llm_config: LLMConfig,
    ):
        llm = ChatOpenAI(
            model=llm_config.model or "",
            temperature=0.0,
            openai_api_base=llm_config.base_url or "",  # type: ignore
            openai_api_key=llm_config.api_key,  # type: ignore
        )
        super().__init__(llm_config, llm=llm)


class OpenRouterLLM(BaseChatOpenAI):
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
        super().__init__(llm_config)


class FireworksLLM(BaseChatOpenAI):
    def __init__(
        self,
        llm_config: LLMConfig,
    ):
        llm_config = (
            LLMConfig(
                model="accounts/fireworks/models/firefunction-v1",
                base_url="https://api.fireworks.ai/inference/v1",
                api_key=os.getenv("FIREWORKS_API_KEY"),
            )
            | llm_config
        )
        super().__init__(llm_config)


class LLMManager:
    @staticmethod
    def create_llm(
        llm_name: LLM_NAMES, llm_config: LLMConfig = LLMConfig.default()
    ) -> BaseLLM:
        llm_config = llm_config.with_llm_name(llm_name)
        if llm_name == "openai-gpt-3.5":
            return OpenAILLM(
                llm_config.with_model("gpt-3.5-turbo").has_function_calling_support()
            )
        elif llm_name == "openai-gpt-4":
            return OpenAILLM(
                llm_config.with_model(
                    "gpt-4-turbo-preview"
                ).has_function_calling_support()
            )
        elif llm_name == "openai-gpt-4o":
            return OpenAILLM(
                llm_config.with_model(
                    "gpt-4o"
                ).has_function_calling_support()
            )
        elif llm_name == "groq-llama3-70":
            return GroqLLM(
                llm_config.with_model("llama3-70b-8192").has_function_calling_support()
            )
        elif llm_name == "groq-llama3-8":
            return GroqLLM(
                llm_config.with_model("llama3-8b-8192").has_function_calling_support()
            )
        elif llm_name == "ollama-llama3-8":
            return OllamaLLM(llm_config.with_model("llama3"))
        elif llm_name == "openrouter-mixtral":
            return OpenRouterLLM(
                llm_config.with_model("mistralai/mixtral-8x7b-instruct")
            )
        elif llm_name == "openrouter-wizardlm2":
            return OpenRouterLLM(
                llm_config.with_model(
                    "microsoft/wizardlm-2-8x22b"
                ).has_function_calling_support()
            )
        elif llm_name == "fireworks-firefunctions":
            return FireworksLLM(
                llm_config.with_model(
                    "accounts/fireworks/models/firefunction-v1"
                ).has_function_calling_support()
            )
        else:
            raise ValueError(f"Unknown LLM type: {llm_name} (Available: {LLM_NAMES})")
