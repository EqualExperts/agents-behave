import os
from dataclasses import asdict, dataclass
from typing import Literal

from langchain_core.language_models.base import BaseLanguageModel
from langchain_openai import ChatOpenAI

from hotel_reservations_langhain.hotel_reservations.chat_open_router import (
    ChatOpenRouter,
)


@dataclass
class Unionable:
    def __or__(self, other):
        other_without_none = {k: v for k, v in asdict(other).items() if v is not None}
        return self.__class__(**(asdict(self) | other_without_none))


@dataclass
class LLMConfig(Unionable):
    llm_name: str | None = None
    name: str | None = None
    model: str | None = None
    temperature: float | None = None
    base_url: str | None = None
    api_key: str | None = None
    supports_function_calling: bool = False

    @staticmethod
    def default():
        return LLMConfig(
            temperature=0.0,
            base_url=None,
            api_key=None,
        )

    def with_llm_name(self, llm_name: str) -> "LLMConfig":
        no_name = asdict(self)
        no_name.pop("llm_name")
        return LLMConfig(**no_name, llm_name=llm_name)

    def with_model(
        self,
        model: str,
    ) -> "LLMConfig":
        no_model = asdict(self)
        no_model.pop("model")
        return LLMConfig(**no_model, model=model)

    def with_function_calling(self) -> "LLMConfig":
        no_function_calling = asdict(self)
        no_function_calling.pop("supports_function_calling")
        return LLMConfig(**no_function_calling, supports_function_calling=True)


class BaseLLM:
    def __init__(self, llm_config: LLMConfig, llm: BaseLanguageModel):
        self.llm_config = llm_config
        self.llm = llm

    def supports_function_calling(self) -> bool:
        return self.llm_config.supports_function_calling


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
