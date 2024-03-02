from typing import Callable

from hotel_reservations.llm_user import LLMUser
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.language_models.base import BaseLanguageModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

Assistant = Callable[[str], str]


def stop_on_max_iterations(max_iterations: int):
    def default_stop_condition_0(state: UserAgentConversationState) -> bool:
        return state.iterations_count >= max_iterations

    return default_stop_condition_0


class UserAgentConversationState:
    def __init__(self):
        self.chat_history = ChatMessageHistory()
        self.iterations_count = 0

    def add_message(self, message: BaseMessage):
        self.chat_history.add_message(message)

    def increment_iterations(self):
        self.iterations_count += 1

    def last_message(self) -> BaseMessage:
        return self.chat_history.messages[-1]


class UserAgentConversation:
    def __init__(
        self,
        user: LLMUser,
        assistant: Assistant,
        llm: BaseLanguageModel,
        stop_condition: Callable[
            [UserAgentConversationState], bool
        ] = stop_on_max_iterations(10),
    ):
        self.user = user
        self.assistant = assistant
        self.llm = llm
        self.stop_condition = stop_condition

        self.state = UserAgentConversationState()

    def start(self, query: str) -> UserAgentConversationState:
        self.state = UserAgentConversationState()
        self.state.add_message(HumanMessage(content=query))
        user_response = query
        done = False
        while not done:
            llm_response = self.assistant(user_response)
            user_response = self.user.chat(llm_response)

            self.state.add_message(AIMessage(content=llm_response))
            self.state.add_message(HumanMessage(content=user_response))

            self.state.increment_iterations()
            done = self.stop_condition(self.state)

        return self.state
