import json
import os
import re
from abc import abstractmethod
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from typing import Literal

from hotel_reservations.callbacks import LLMCallbacks, NoOpLLMCallbacks
from hotel_reservations.messages import ChatResponseMessage, LLMMessages
from litellm import Choices, ModelResponse, completion
from openai import OpenAI
from openai._types import NOT_GIVEN, NotGiven
from openai.types.chat import ChatCompletionMessageToolCall, ChatCompletionToolParam
from openai.types.chat.chat_completion_message_tool_call import Function


@dataclass
class Unionable:
    def __or__(self, other):
        other_without_none = {k: v for k, v in asdict(other).items() if v is not None}
        return self.__class__(**(asdict(self) | other_without_none))


@dataclass
class LLMConfig(Unionable):
    model: str | None = None
    temperature: float | None = None
    base_url: str | None = None
    api_key: str | None = None
    callbacks: LLMCallbacks = NoOpLLMCallbacks()
    supports_function_calling: bool = False

    @staticmethod
    def default():
        return LLMConfig(
            temperature=0.0,
            base_url=None,
            api_key=None,
            callbacks=NoOpLLMCallbacks(),
        )

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
    def __init__(
        self,
        llm_config: LLMConfig,
    ):
        self.llm_config = llm_config
        self.llm_config.callbacks.on_create(self)

    def supports_function_calling(self) -> bool:
        return self.llm_config.supports_function_calling

    @abstractmethod
    def chat_completions(
        self,
        messages: LLMMessages,
        tools: Iterable[ChatCompletionToolParam] | NotGiven = NOT_GIVEN,
    ) -> ChatResponseMessage:
        pass


class OpenAILLM(BaseLLM):
    def __init__(
        self,
        llm_config: LLMConfig,
    ):
        llm_config = LLMConfig(model="gpt-4-turbo-preview") | llm_config
        super().__init__(llm_config)
        client = OpenAI(base_url=llm_config.base_url, api_key=llm_config.api_key)
        self.client = client

    @abstractmethod
    def chat_completions(
        self,
        messages: LLMMessages,
        tools: Iterable[ChatCompletionToolParam] | NotGiven = NOT_GIVEN,
    ) -> ChatResponseMessage:
        response = self.client.chat.completions.create(
            model=self.llm_config.model or "",
            messages=messages.to_openai_messages(),
            tools=tools,
            temperature=self.llm_config.temperature,
        )
        response_message = response.choices[0].message
        message = ChatResponseMessage(
            content=response_message.content, tool_calls=response_message.tool_calls
        )
        self.llm_config.callbacks.on_chat_completions(
            messages, tools, response.__dict__, message
        )
        return message


class OpenRouterLLM(OpenAILLM):
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

    @abstractmethod
    def chat_completions(
        self,
        messages: LLMMessages,
        tools: Iterable[ChatCompletionToolParam] | NotGiven = NOT_GIVEN,
    ) -> ChatResponseMessage:
        response = self.client.chat.completions.create(
            model=self.llm_config.model or "",
            messages=messages.to_openai_messages(),
            tools=tools,
            temperature=self.llm_config.temperature,
        )
        response_message = response.choices[0].message
        content = response_message.content or ""
        tool_calls = extract_tool_calls(content)
        message = ChatResponseMessage(
            content=response_message.content, tool_calls=tool_calls
        )
        self.llm_config.callbacks.on_chat_completions(
            messages, tools, response.__dict__, message
        )
        return message


class LiteLLM(BaseLLM):
    def __init__(
        self,
        llm_config: LLMConfig,
    ):
        llm_config = (
            LLMConfig(model="openrouter/mistralai/mixtral-8x7b-instruct") | llm_config
        )
        super().__init__(llm_config)

    def with_model(self, model: str):
        return self.llm_config | LLMConfig(model=model)

    def chat_completions(
        self,
        messages: LLMMessages,
        tools: Iterable[ChatCompletionToolParam] | NotGiven = NOT_GIVEN,
    ) -> ChatResponseMessage:
        converted_messages = messages.to_openai_messages()

        response = completion(
            model=self.llm_config.model or "",
            messages=converted_messages,
            temperature=self.llm_config.temperature,
        )
        message: ChatResponseMessage | None = None
        if isinstance(response, ModelResponse):
            choice = response.choices[0]
            if isinstance(choice, Choices):
                content = choice.message.content
                tool_calls = extract_tool_calls(content)
                striped_content = re.sub(r"\{.*\}", "", content)
                message = ChatResponseMessage(
                    content=striped_content, tool_calls=tool_calls
                )

        if not message:
            raise ValueError(f"Unexpected response: {response}")

        self.llm_config.callbacks.on_chat_completions(
            messages, tools, response.__dict__, message
        )
        return message


def extract_tool_calls(content: str) -> list[ChatCompletionMessageToolCall] | None:
    if "null" in content:
        return None
    pattern = r'\{\s*"function_call":\s*\{.*?\}\s*\}\s*\}'
    matches = re.findall(pattern, content, re.DOTALL)
    if matches:
        function_call = json.loads(matches[0])["function_call"]
        function_name = function_call["name"]
        tool_input = json.dumps(function_call["arguments"])
        tool_call = ChatCompletionMessageToolCall(
            id="",
            type="function",
            function=Function(name=function_name, arguments=tool_input),
        )
        return [tool_call]
    else:
        return None


LLMS = Literal[
    "openai-gpt-4",
    "openrouter-mixtral",
    "together-mixtral",
    "litellm-gpt-4",
    "litellm-mixtral",
]


class LLMManager:

    @staticmethod
    def create_llm(llm: LLMS, llm_config: LLMConfig = LLMConfig.default()) -> BaseLLM:
        if llm == "openai-gpt-4":
            return OpenAILLM(
                llm_config.with_model("gpt-4-turbo-preview").with_function_calling()
            )
        elif llm == "openrouter-mixtral":
            return OpenRouterLLM(
                llm_config.with_model("mistralai/mixtral-8x7b-instruct")
            )
        elif llm == "litellm-gpt-4":
            return LiteLLM(
                llm_config.with_model("openai/gpt-4").with_function_calling()
            )
        elif llm == "litellm-mixtral":
            return LiteLLM(
                llm_config.with_model("openrouter/mistralai/mixtral-8x7b-instruct")
            )
        else:
            raise ValueError(f"Unknown LLM type: {llm}")
