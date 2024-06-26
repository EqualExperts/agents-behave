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


class TestUser(User):
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
    Your role is to simulate a user that asked an Assistant to do a task. 
    You have a goal and you need the Assistant to help you achieve it.

    Here is some information about you and your goal (in your own words):
    {persona}

    You should say "bye" to the Assistant when you think the conversation is over.
    Now start by asking the Assistant for help.
    """  # noqa E501
