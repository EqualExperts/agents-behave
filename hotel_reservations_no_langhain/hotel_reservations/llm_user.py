from hotel_reservations.llms import BaseLLM
from hotel_reservations.messages import (
    AssistantMessage,
    LLMMessages,
    SystemMessage,
    UserMessage,
)


class LLMUser:
    def __init__(self, persona: str, llm: BaseLLM):
        self.persona = persona
        self.llm = llm
        self.chat_history = LLMMessages()

    def start(self, user_message: str):
        self.chat_history.add_message(UserMessage(user_message))

    def chat(self, llm_response: str) -> str:
        prompt = SYSTEM_PROMPT.format(persona=self.persona)
        llm_message = AssistantMessage(llm_response)
        self.chat_history.add_message(llm_message)
        messages = LLMMessages(
            [
                SystemMessage(prompt),
                *self.chat_history.messages,
            ]
        )
        user_response = self.llm.chat_completions(messages=messages)
        content = user_response.content or ""
        self.chat_history.add_message(UserMessage(content))
        return content


SYSTEM_PROMPT = """
    Your role is to simulate a User that asked an Assistant to do a task. Remember, you are the User, not the Assistant.
    If you don't know the answer, just pick a random one.

    Here is some information about you:
    ---------------------------------------------
    {persona}
    ---------------------------------------------

    When the Assistant finishes the task, it will not ask a question, it will just give you the result.
    You should then say "bye" to the Assistant to end the conversation.
    -------------
    """  # noqa E501
