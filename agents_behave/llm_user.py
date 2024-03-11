from abc import abstractmethod

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from agents_behave.base_llm import BaseLLM


class User:
    @abstractmethod
    def start(self) -> str:
        pass

    @abstractmethod
    def chat(self, llm_response: str) -> str:
        pass


class LLMUser(User):
    def __init__(self, llm: BaseLLM, persona: str):
        self.chat_history = []
        self.agent = self.build_agent(llm, persona)

    def build_agent(self, llm: BaseLLM, persona: str):
        user_prompt = USER_PROMPT.format(persona=persona)
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", user_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
            ]
        )
        chain = prompt | llm.llm | StrOutputParser()
        return chain

    def start(self):
        response = self.get_response()
        self.chat_history.append(AIMessage(content=response))
        return response

    def chat(self, query: str):
        self.chat_history.append(HumanMessage(content=query))
        response = self.get_response()
        self.chat_history.append(AIMessage(content=response))
        return response

    def get_response(self):
        response = self.agent.invoke(
            {"chat_history": self.chat_history},
        )
        return response


USER_PROMPT = """
    Your role is to simulate a user that asked an Assistant to do a task. Remember, you are not the Assistant, you are the user.
    If you don't know the answer, just pick a random one.

    Here is some information about you:
    {persona}

    When the LLM finishes the task, it will not ask a question, it will just give you the result.
    You should then say "bye" to the LLM to end the conversation.
    """  # noqa E501
