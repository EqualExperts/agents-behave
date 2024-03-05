from typing import Callable

from hotel_reservations.llm_user import LLMUser
from hotel_reservations.llms import BaseLLM, LLMMessages
from hotel_reservations.messages import AssistantMessage, LLMMessage, UserMessage

Assistant = Callable[[str], str]


def stop_on_max_iterations(max_iterations: int):
    def default_stop_condition_0(state: UserAgentConversationState) -> bool:
        return state.iterations_count >= max_iterations

    return default_stop_condition_0


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


class UserAgentConversation:
    def __init__(
        self,
        user: LLMUser,
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

    def start(self, user_message: str) -> UserAgentConversationState:
        self.user.start(user_message)
        self.state = UserAgentConversationState()
        self.state.add_message(UserMessage(content=user_message))
        user_response = user_message
        done = False
        while not done:
            llm_response = self.assistant(user_response)
            user_response = self.user.chat(llm_response)

            self.state.add_message(AssistantMessage(content=llm_response))
            self.state.add_message(UserMessage(content=user_response))

            self.state.increment_iterations()
            done = self.stop_condition(self.state)

        return self.state
