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
        return self.get_response()

    def chat(self, query: str):
        self.chat_history.append(HumanMessage(content=query))
        return self.get_response()

    def get_response(self):
        response = self.agent.invoke(
            {"chat_history": self.chat_history},
        )
        self.chat_history.append(AIMessage(content=response))
        return response


USER_PROMPT = """
    You are a person with the following persona:
    {persona}
    -------------

    You job is to interact with an agent that will asist you in achieving your goals.

    You should then say "bye" when you think the conversation is over.
    
    You should start by stating what you want to do.

    """  # noqa E501
