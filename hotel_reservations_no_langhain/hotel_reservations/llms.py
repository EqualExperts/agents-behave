import json
import os
from abc import abstractmethod
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from typing import Literal

from hotel_reservations.callbacks import LLMCallbacks, NoOpLLMCallbacks
from hotel_reservations.messages import (
    ChatResponseMessage,
    LLMMessages,
    to_openai_messages,
)
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
    llm_name: str | None = None
    name: str | None = None
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
    def __init__(self, llm_config: LLMConfig):
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
            messages=to_openai_messages(messages),
            tools=tools,
            temperature=self.llm_config.temperature,
        )
        response_message = response.choices[0].message
        message = ChatResponseMessage(
            content=response_message.content,
            tool_calls=response_message.tool_calls,
        )
        self.llm_config.callbacks.on_chat_completions(
            self, messages, tools, response.__dict__, message
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
            messages=to_openai_messages(messages),
            tools=tools,
            temperature=self.llm_config.temperature,
        )
        response_message = response.choices[0].message
        content = response_message.content or ""
        tool_calls = self.extract_tool_calls(content)
        message = ChatResponseMessage(content=content, tool_calls=tool_calls)
        self.llm_config.callbacks.on_chat_completions(
            self, messages, tools, response.__dict__, message
        )
        return message

    def extract_tool_calls(
        self, content: str
    ) -> list[ChatCompletionMessageToolCall] | None:
        if """function""" in content:
            function_call = json.loads(content)
            function_name = function_call["function"]
            tool_input = json.dumps(function_call["parameters"])
            tool_call = ChatCompletionMessageToolCall(
                id="",
                type="function",
                function=Function(name=function_name, arguments=tool_input),
            )
            return [tool_call]
        else:
            return None


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

        response = completion(
            model=self.llm_config.model or "",
            messages=to_openai_messages(messages),
            temperature=self.llm_config.temperature,
        )
        message: ChatResponseMessage | None = None
        if isinstance(response, ModelResponse):
            choice = response.choices[0]
            if isinstance(choice, Choices):
                content = choice.message.content
                print(f"Content: {content}")
                decoded_content = self.decode_content(content)
                response_content = (
                    decoded_content["content"]
                    if decoded_content and "content" in decoded_content
                    else content
                )
                tool_calls = (
                    self.extract_tool_calls(decoded_content)
                    if decoded_content
                    else None
                )
                message = ChatResponseMessage(
                    content=response_content, tool_calls=tool_calls
                )

        if not message:
            raise ValueError(f"Unexpected response: {response}")

        self.llm_config.callbacks.on_chat_completions(
            self, messages, tools, response.__dict__, message
        )
        return message

    def extract_tool_calls(
        self, decoded_content: dict
    ) -> list[ChatCompletionMessageToolCall] | None:
        if "function_call" not in decoded_content:
            return None
        function_call = decoded_content["function_call"]
        if function_call is None:
            return None
        function_name = function_call["name"]
        tool_input = json.dumps(function_call["arguments"])
        tool_call = ChatCompletionMessageToolCall(
            id="",
            type="function",
            function=Function(name=function_name, arguments=tool_input),
        )
        return [tool_call]

    def decode_content(self, content: str) -> dict | None:
        json_content = content.replace("```json", "").replace("```", "")
        try:
            response = json.loads(json_content)
        except json.JSONDecodeError:
            return None

        return response


LLMS = Literal[
    "openai-gpt-4",
    "openrouter-mixtral",
    "together-mixtral",
    "litellm-gpt-4",
    "litellm-mixtral",
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
                llm_config.with_model(
                    "mistralai/mixtral-8x7b-instruct"
                ).with_function_calling()
            )
        elif llm_name == "litellm-gpt-4":
            return LiteLLM(llm_config.with_model("openai/gpt-4"))
        elif llm_name == "litellm-mixtral":
            return LiteLLM(
                llm_config.with_model("openrouter/mistralai/mixtral-8x7b-instruct")
            )
        else:
            raise ValueError(f"Unknown LLM type: {llm_name}")