from typing import Callable

from colorama import Fore
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from agents_behave.base_llm import BaseLLM
from agents_behave.llm_user import User

Assistant = Callable[[str], str]


def stop_on_max_iterations(max_iterations: int):
    def stop_on_max_iterations_fn(state: UserAgentConversationState) -> bool:
        return state.iterations_count >= max_iterations

    return stop_on_max_iterations_fn


class UserAgentConversationState:
    def __init__(self):
        self.chat_history: list[BaseMessage] = []
        self.iterations_count = 0

    def add_message(self, message: BaseMessage):
        self.chat_history.append(message)

    def increment_iterations(self):
        self.iterations_count += 1

    def last_message(self) -> BaseMessage:
        return self.chat_history[-1]

    def last_assistant_message(self) -> BaseMessage | None:
        return next(
            (
                message
                for message in reversed(self.chat_history)
                if isinstance(message, AIMessage)
            ),
            None,
        )

    def last_assistant_message_contains(self, s: str) -> bool:
        a = self.last_assistant_message()
        return (
            s.lower() in a.content.lower()
            if a and a.content and isinstance(a.content, str)
            else False
        )


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
        self.state.add_message(HumanMessage(content=user_message))
        user_response = user_message
        while not self.stop_condition(self.state):
            print(f"{Fore.YELLOW}Iteration {self.state.iterations_count}{Fore.RESET}")
            llm_response = self.assistant(user_response)
            user_response = self.user.chat(llm_response)

            self.state.add_message(AIMessage(content=llm_response))
            self.state.add_message(HumanMessage(content=user_response))

            self.state.increment_iterations()

        return self.state
