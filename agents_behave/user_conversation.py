from typing import Callable

from agents_behave.llm_user import LLMUser
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

Assistant = Callable[[str], str]


class UserConversationState:
    def __init__(self, chat_history: list[BaseMessage] = []):
        self.chat_history = chat_history

    def add_message(self, message: BaseMessage):
        self.chat_history.append(message)


class UserConversation:
    def __init__(
        self,
        assistant: Assistant,
        user: LLMUser,
        stop_condition: Callable[[UserConversationState], bool] = lambda _: False,
        max_iterations: int = 10,
        options={},
    ):
        self.assistant = assistant
        self.user = user
        self.stop_condition = stop_condition
        self.max_iterations = max_iterations
        self.options = options

        self.state = UserConversationState()

    def start_conversation(self, query: str):
        self.state.add_message(HumanMessage(content=query))
        user_response = query
        iterations = 0
        done = False
        while not done:
            llm_response = self.assistant(user_response)
            user_response = self.user.chat(llm_response)

            self.state.add_message(AIMessage(content=llm_response))
            self.state.add_message(HumanMessage(content=user_response))

            iterations += 1
            done = iterations >= self.max_iterations or self.stop_condition(self.state)

        return self.state
