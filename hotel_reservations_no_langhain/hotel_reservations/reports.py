from hotel_reservations.messages import LLMMessage, LLMMessages
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionMessage,
    ChatCompletionMessageToolCall,
    ChatCompletionToolParam,
)


class Report:
    def __init__(self, name: str, values: dict):
        self.name = name
        self.values = values


class MessageReport(Report):
    def __init__(self, message: LLMMessage):
        super().__init__(
            "message",
            {
                "role": message.role,
                "content": message.content,
            },
        )


class MessagesReport(Report):
    def __init__(self, messages: LLMMessages):
        super().__init__("messages", {m.role: m.content for m in messages})


class ToolParamReport(Report):
    def __init__(self, tool_param: ChatCompletionToolParam):
        super().__init__(
            "tool_param",
            {
                "tool_param": tool_param,
            },
        )


class ToolCallsReport(Report):
    def __init__(self, tool_calls: ChatCompletionMessageToolCall):
        super().__init__(
            "tool_calls",
            {
                "tool_calls": tool_calls.function,
            },
        )


class ChatCompletionMessageReport(Report):
    def __init__(self, message: ChatCompletionMessage):
        super().__init__(
            "chat_completion_message",
            {
                "content": message.content,
                "tool_calls": (
                    ToolCallsReport(message.tool_calls[0])
                    if message.tool_calls
                    else None
                ),
            },
        )


class ChatCompletionReport(Report):
    def __init__(self, completion: ChatCompletion):
        super().__init__(
            "chat_completion",
            {
                "choices": ChatCompletionMessageReport(completion.choices[0].message),
                "model": completion.model,
            },
        )
