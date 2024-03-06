from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import asdict

from colorama import Fore, Style
from hotel_reservations.messages import ChatResponseMessage, LLMMessages
from hotel_reservations.reports import (
    MessageReport,
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
        llm,
        messages: LLMMessages,
        tools: Iterable[ChatCompletionToolParam] | NotGiven,
        llm_response: dict,
        response: ChatResponseMessage,
    ):
        pass


class NoOpLLMCallbacks(LLMCallbacks):
    def on_create(self, llm):
        pass

    def on_chat_completions(
        self,
        llm,
        messages: LLMMessages,
        tools: Iterable[ChatCompletionToolParam] | NotGiven,
        llm_response: dict,
        response: ChatCompletion,
    ):
        pass


class ConsoleLLMCallbacks(LLMCallbacks):
    def on_create(self, llm):
        self.output("LLM created")
        no_key = asdict(llm.llm_config)
        no_key.pop("api_key")
        self.report(Report("LLM Config", no_key))

    def on_chat_completions(
        self,
        llm,
        messages: LLMMessages,
        tools: Iterable[ChatCompletionToolParam] | NotGiven,
        llm_response: dict,
        message: ChatResponseMessage,
    ):
        self.output(
            f"---- {llm.llm_config.name}{'-' * 80}", color=Fore.YELLOW + Style.BRIGHT
        )
        self.report(MessagesReport(messages))
        if tools:
            for tool in tools:
                self.report(ToolParamReport(tool))
        self.report(Report("LLM Response", llm_response))
        self.report(MessageReport(message))

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
                    line_ident=ident + 4 + len(k) + 2,
                )

    def title(self, message: str, ident=0):
        self.output(f"{Fore.BLUE}{message}{Style.RESET_ALL}", ident=ident)

    def details(self, message: str, ident=0, line_ident=0):
        idented_message = self.justify(message).replace("\n", f"\n{' ' * line_ident}")
        self.output(idented_message, ident=ident)

    def output(self, message: str, color: str = Fore.GREEN, ident=0):
        print(f"{' ' * ident}{color}{message}{Style.RESET_ALL}")

    def justify(self, message: str, width=150):
        lines = message.split("\n")
        splitted_lines = [self.chunk(line, width) for line in lines]
        flatted_lines = [line for lines in splitted_lines for line in lines]
        return "\n".join(flatted_lines)

    def chunk(self, line: str, width):
        return [line[i : i + width] for i in range(0, len(line), width)]  # noqa E203
