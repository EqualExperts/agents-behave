from abc import ABC, abstractmethod
from collections.abc import Iterable

from colorama import Fore, Style
from hotel_reservations.messages import LLMMessages
from hotel_reservations.reports import (
    ChatCompletionReport,
    MessagesReport,
    Report,
    ToolParamReport,
)
from openai._types import NotGiven
from openai.types.chat import ChatCompletion, ChatCompletionToolParam


class LLMCallbacks(ABC):
    def __init__(self):
        self.callbacks = {}

    @abstractmethod
    def on_create(self, llm):
        pass

    @abstractmethod
    def on_chat_completions(
        self,
        messages: LLMMessages,
        tools: Iterable[ChatCompletionToolParam] | NotGiven,
        response: ChatCompletion,
    ):
        pass


class NoOpLLMCallbacks(LLMCallbacks):
    def on_create(self, llm):
        pass

    def on_chat_completions(
        self,
        messages: LLMMessages,
        tools: Iterable[ChatCompletionToolParam] | NotGiven,
        response: ChatCompletion,
    ):
        pass


class ConsoleLLMCallbacks(LLMCallbacks):
    def on_create(self, llm):
        self.output("LLM created")
        self.report(Report("LLM Config", llm.llm_config.__dict__))

    def on_chat_completions(
        self,
        messages: LLMMessages,
        tools: Iterable[ChatCompletionToolParam] | NotGiven,
        response: ChatCompletion,
    ):
        self.report(MessagesReport(messages))
        if tools:
            for tool in tools:
                self.report(ToolParamReport(tool))
        self.report(ChatCompletionReport(response))

    def report(self, report: Report, ident=0):
        self.output("-" * 80)
        self.title(report.name, ident=ident)
        for k, v in report.values.items():
            if isinstance(v, Report):
                self.report(v, ident=ident + 4)
            else:
                self.details(
                    f"{Style.BRIGHT}{Fore.MAGENTA}{k}: {Fore.LIGHTBLUE_EX}{v}{Style.RESET_ALL}",
                    ident=ident + 4,
                )
        self.output("-" * 80)

    def title(self, message: str, ident=0):
        self.output(f"{Fore.BLUE}{message}{Style.RESET_ALL}", ident=ident)

    def details(self, message: str, ident=0):
        self.output(message, ident=ident)

    def output(self, message: str, color: str = Fore.GREEN, ident=0):
        print(f"{' ' * ident}{color}{message}{Style.RESET_ALL}")
