from abc import ABC

from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageToolCall,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)


class LLMMessage(ABC):
    def __init__(self, role: str, content: str | None):
        self.role = role
        self.content = content

    def __repr__(self):
        return f"{self.role}: {self.content}"

    def __str__(self):
        return f"{self.role.upper()}: {self.content}"


class SystemMessage(LLMMessage):
    def __init__(self, content: str):
        super().__init__("system", content)

    def to_openai_message(self):
        return ChatCompletionSystemMessageParam(
            role="system", content=self.content or ""
        )


class UserMessage(LLMMessage):
    def __init__(self, content: str):
        super().__init__("user", content)


class AssistantMessage(LLMMessage):
    def __init__(
        self,
        content: str | None,
    ):
        super().__init__("assistant", content)


class ChatResponseMessage(LLMMessage):
    def __init__(
        self,
        content: str | None,
        tool_calls: list[ChatCompletionMessageToolCall] | None = None,
    ):
        super().__init__("assistant", content)
        self.tool_calls = tool_calls or []


class LLMMessages:
    def __init__(self, messages: list[LLMMessage] | None = None):
        self.messages = messages if messages is not None else []

    def __iter__(self):
        return iter(self.messages)

    def add_message(self, message: LLMMessage):
        self.messages.append(message)


def to_openai_messages(messages: LLMMessages):
    return [to_openai_message(message) for message in messages]


def to_openai_message(message: LLMMessage):
    content = message.content or ""
    if isinstance(message, SystemMessage):
        return ChatCompletionSystemMessageParam(role="system", content=content)
    elif isinstance(message, UserMessage):
        return ChatCompletionUserMessageParam(role="user", content=content)
    elif isinstance(message, AssistantMessage):
        return ChatCompletionAssistantMessageParam(role="assistant", content=content)
    else:
        raise ValueError(f"Unexpected message type: {message}")
