from hotel_reservations_no_langhain.hotel_reservations.llms import OpenAIBaseLLM
from hotel_reservations.messages import LLMMessages, SystemMessage, UserMessage


class LLMUser:
    def __init__(self, persona: str, llm: OpenAIBaseLLM):
        self.persona = persona
        self.llm = llm
        self.chat_history = LLMMessages()

    def chat(self, user_message: str) -> str:
        prompt = USER_PROMPT.format(
            persona=self.persona,
            chat_history=self.chat_history,
        )
        messages = LLMMessages(
            [
                SystemMessage(prompt),
                *self.chat_history.messages,
                UserMessage(user_message),
            ]
        )
        completion = self.llm.chat_completions(
            messages=messages,
        )
        content = completion.choices[0].message.content or "{}"
        return content


USER_PROMPT = """
    Your role is to simulate a user that asked an Assistant to do a task. Remember, you are not the Assistant, you are the user.
    If you don't know the answer, just pick a random one.

    Here is some information about you:
    {persona}

    You should say "bye" when you are done.

    Conversation:
    {chat_history}
    -------------
    """  # noqa E501
