from typing import Callable

from colorama import Fore
from hotel_reservations.llm_user import User
from hotel_reservations.llms import BaseLLM, LLMMessages
from hotel_reservations.messages import AssistantMessage, LLMMessage, UserMessage

Assistant = Callable[[str], str]


def stop_on_max_iterations(max_iterations: int):
    def stop_on_max_iterations_fn(state: UserAgentConversationState) -> bool:
        return state.iterations_count >= max_iterations

    return stop_on_max_iterations_fn


class UserAgentConversationState:
    def __init__(self):
        self.chat_history = LLMMessages()
        self.iterations_count = 0

    def add_message(self, message: LLMMessage):
        self.chat_history.add_message(message)

    def increment_iterations(self):
        self.iterations_count += 1

    def last_message(self) -> LLMMessage:
        return self.chat_history.messages[-1]

    def last_assistant_message(self) -> LLMMessage | None:
        return next(
            (
                message
                for message in reversed(self.chat_history.messages)
                if isinstance(message, AssistantMessage)
            ),
            None,
        )

    def last_assistant_message_contains(self, s: str) -> bool:
        a = self.last_assistant_message()
        return s.lower() in a.content.lower() if a and a.content else False


class UserAgentConversation:
    def __init__(
        self,
        user: User,
        assistant: Assistant,
        llm: BaseLLM,
        stop_condition: Callable[
            [UserAgentConversationState], bool
        ] = stop_on_max_iterations(10),
    ):
        self.user = user
        self.assistant = assistant
        self.llm = llm
        self.stop_condition = stop_condition

        self.state = UserAgentConversationState()

    def start(self) -> UserAgentConversationState:
        user_message = self.user.start()
        self.state = UserAgentConversationState()
        self.state.add_message(UserMessage(content=user_message))
        user_response = user_message
        while not self.stop_condition(self.state):
            print(f"{Fore.YELLOW}Iteration {self.state.iterations_count}{Fore.RESET}")
            llm_response = self.assistant(user_response)
            user_response = self.user.chat(llm_response)

            self.state.add_message(AssistantMessage(content=llm_response))
            self.state.add_message(UserMessage(content=user_response))

            self.state.increment_iterations()

        return self.state
