from abc import ABC, abstractmethod

from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionMessageToolCall,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)


class LLMMessage(ABC):
    def __init__(self, role: str, content: str | None):
        self.role = role
        self.content = content

    def to_dict(self):
        return {"role": self.role.upper(), "content": self.content}

    def __repr__(self):
        return f"{self.role}: {self.content}"

    def __str__(self):
        return f"{self.role.upper()}: {self.content}"

    @abstractmethod
    def to_openai_message(self) -> ChatCompletionMessageParam:
        pass


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

    def to_openai_message(self):
        return ChatCompletionUserMessageParam(role="user", content=self.content or "")


class AssistantMessage(LLMMessage):
    def __init__(
        self,
        content: str | None,
    ):
        super().__init__("assistant", content)

    def to_openai_message(self):
        return ChatCompletionAssistantMessageParam(
            role="assistant", content=self.content
        )


class ChatResponseMessage(LLMMessage):
    def __init__(
        self,
        content: str | None,
        tool_calls: list[ChatCompletionMessageToolCall] | None = None,
    ):
        super().__init__("assistant", content)
        self.tool_calls = tool_calls or []

    def to_openai_message(self):
        return ChatCompletionAssistantMessageParam(
            role="assistant", content=self.content
        )


class LLMMessages:
    def __init__(self, messages: list[LLMMessage] | None = None):
        self.messages = messages if messages is not None else []

    def __iter__(self):
        return iter(self.messages)

    def add_message(self, message: LLMMessage):
        self.messages.append(message)

    def to_openai_messages(self):
        return [message.to_openai_message() for message in self.messages]
