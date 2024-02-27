from langchain_core.output_parsers import StrOutputParser
from langchain_core.language_models.base import BaseLanguageModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


class LLMUser:
    def __init__(self, llm: BaseLanguageModel, persona: str):
        self.chat_history = []
        self.agent = self.build_agent(llm, persona)

    def build_agent(self, llm: BaseLanguageModel, persona: str):
        user_prompt = USER_PROMPT.format(persona=persona)
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", user_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("user", "{input}"),
            ]
        )
        chain = prompt | llm | StrOutputParser()
        return chain

    def chat(self, query: str):
        response = self.agent.invoke(
            {"input": query, "chat_history": self.chat_history},
        )
        self.chat_history.append(HumanMessage(content=query))
        self.chat_history.append(AIMessage(content=response))
        return response


USER_PROMPT = """
    Your role is to simulate a user that asked an Assistant to do a task. Remember, you are not the Assistant, you are the user.
    If you don't know the answer, just pick a random one.

    Here is some information about you:
    {persona}

    When the LLM finishes the task, it will not ask a question, it will just give you the result.
    You should then say "bye" to the LLM to end the conversation.

    Conversation:
    {{chat_history}}
    -------------
    """  # noqa E501
