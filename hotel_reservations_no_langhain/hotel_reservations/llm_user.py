from abc import abstractmethod

from hotel_reservations.llms import BaseLLM
from hotel_reservations.messages import (
    AssistantMessage,
    LLMMessages,
    SystemMessage,
    UserMessage,
)


class User:
    @abstractmethod
    def start(self) -> str:
        pass

    @abstractmethod
    def chat(self, llm_response: str) -> str:
        pass


class ConsoleInputUser(User):
    def start(self):
        return input("> ")

    def chat(self, llm_response: str) -> str:
        print(llm_response)
        return input("> ")


class LLMUser(User):
    def __init__(self, persona: str, llm: BaseLLM):
        self.persona = persona
        self.llm = llm
        self.chat_history = LLMMessages()

    def start(self) -> str:
        prompt = SYSTEM_PROMPT.format(persona=self.persona)
        messages = LLMMessages([SystemMessage(prompt)])
        user_response = self.llm.chat_completions(messages=messages)
        content = user_response.content or ""
        self.chat_history.add_message(AssistantMessage(content))
        return content

    def chat(self, llm_response: str) -> str:
        prompt = SYSTEM_PROMPT.format(persona=self.persona)
        llm_message = UserMessage(llm_response)
        self.chat_history.add_message(llm_message)
        messages = LLMMessages(
            [
                SystemMessage(prompt),
                *self.chat_history.messages,
            ]
        )
        user_response = self.llm.chat_completions(messages=messages)
        content = user_response.content or ""
        self.chat_history.add_message(AssistantMessage(content))
        return content


SYSTEM_PROMPT = """
    Your role is to simulate a User that asked an Assistant to do a task. Remember, you are the User, not the Assistant.
    If you don't know the answer, just pick a random one.

    Here is some information about you:
    {persona}
    -------------
    """  # noqa E501
