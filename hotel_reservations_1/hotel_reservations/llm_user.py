from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.language_models.base import BaseLanguageModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


class LLMUser:
    def __init__(self, persona: str, llm: BaseLanguageModel):
        self.agent = self.build_agent(persona, llm)
        self.chat_history = ChatMessageHistory()

    def build_agent(self, persona: str, llm: BaseLanguageModel):
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", USER_PROMPT),
                MessagesPlaceholder(variable_name="chat_history"),
                ("user", "{input}"),
            ]
        )
        prompt = prompt.partial(persona=persona)
        chain = prompt | llm | StrOutputParser()
        return chain

    def chat(self, user_message: str) -> str:
        assistant_response = self.agent.invoke(
            {"input": user_message, "chat_history": self.chat_history.messages},
        )
        self.chat_history.add_messages(
            [
                HumanMessage(content=user_message),
                AIMessage(content=assistant_response),
            ]
        )
        return assistant_response


USER_PROMPT = """
    Your role is to simulate a user that asked an Assistant to do a task. 
    Remember, you are not the Assistant, you are the user.
    If you don't know the answer, just pick a random one.

    Here is some information about you:
    {persona}

    When the Assistant finishes the task, it will not ask a question, it will just give you the result.
    You should then say "bye" to the Assistant to end the conversation.

    Conversation:
    {chat_history}
    -------------
    """  # noqa E501
