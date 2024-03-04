import os
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from typing import Literal

from hotel_reservations.callbacks import LLMCallbacks, NoOpLLMCallbacks
from hotel_reservations.messages import LLMMessages
from openai import OpenAI
from openai._types import NOT_GIVEN, NotGiven
from openai.types.chat import ChatCompletionToolParam


@dataclass
class Unionable:
    def __or__(self, other):
        other_without_none = {k: v for k, v in asdict(other).items() if v is not None}
        return self.__class__(**(asdict(self) | other_without_none))


@dataclass
class LLMConfig(Unionable):
    model: str | None = None
    temperature: float = 0.0
    base_url: str | None = None
    api_key: str | None = None
    callbacks: LLMCallbacks = NoOpLLMCallbacks()

    @staticmethod
    def default():
        return LLMConfig(
            temperature=0.0,
            base_url=None,
            api_key=None,
            callbacks=NoOpLLMCallbacks(),
        )


class BaseLLM:
    def __init__(
        self,
        llm_config: LLMConfig,
    ):
        self.llm_config = llm_config


class OpenAIBaseLLM(BaseLLM):
    def __init__(
        self,
        llm_config: LLMConfig,
    ):
        super().__init__(llm_config)
        client = OpenAI(base_url=llm_config.base_url, api_key=llm_config.api_key)
        self.client = client

    def chat_completions(
        self,
        messages: LLMMessages,
        tools: Iterable[ChatCompletionToolParam] | NotGiven = NOT_GIVEN,
    ):
        response = self.client.chat.completions.create(
            model=self.llm_config.model or "",
            messages=messages.to_openai_messages(),
            tools=tools,
            temperature=self.llm_config.temperature,
        )
        self.llm_config.callbacks.on_chat_completions(messages, tools, response)
        return response


class OpenAILLM(OpenAIBaseLLM):
    def __init__(
        self,
        llm_config: LLMConfig,
    ):
        llm_config = LLMConfig(model="gpt-4-turbo-preview") | llm_config
        super().__init__(llm_config)


class OpenRouterLLM(OpenAIBaseLLM):
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


LLMS = Literal["openai-gpt-4", "openrouter-mixtral", "together-mixtral"]


class LLMManager:

    @staticmethod
    def create_llm(
        llm: LLMS, llm_config: LLMConfig = LLMConfig.default()
    ) -> OpenAIBaseLLM:
        if llm == "openai-gpt-4":
            return OpenAILLM(llm_config)
        elif llm == "openrouter-mixtral":
            return OpenRouterLLM(llm_config)
        else:
            raise ValueError(f"Unknown LLM type: {llm}")
