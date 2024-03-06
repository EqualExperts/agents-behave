from hotel_reservations.messages import ChatResponseMessage, LLMMessage, LLMMessages
from openai.types.chat import ChatCompletionMessageToolCall, ChatCompletionToolParam


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
        super().__init__(
            "messages", {f"{m.role} - {i+1}": m.content for i, m in enumerate(messages)}
        )


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
    def __init__(self, message: ChatResponseMessage):
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
