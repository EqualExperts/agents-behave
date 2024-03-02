from dataclasses import dataclass
from datetime import date
from typing import Any, Callable

from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.pydantic_v1 import BaseModel, Field
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.language_models.base import BaseLanguageModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool

MakeReservation = Callable[[str, str, date, date, int], bool]


class MakeReservationInput(BaseModel):
    hotel_name: str = Field(description="The name of the hotel.")
    guest_name: str = Field(description="The name of the guest.")
    checkin_date: date = Field(description="The checkin date.")
    checkout_date: date = Field(description="The checkout date.")
    guests: int = Field(description="The number of guests.")


@dataclass
class Hotel:
    id: str
    name: str
    location: str


def make_reservation(
    hotel_name: str,
    guest_name: str,
    checkin_date: date,
    checkout_date: date,
    guests: int,
):
    print(
        f"""Making reservation for:
                guest_name: {guest_name}
                hotel_name: {hotel_name}
                checkin_date: {checkin_date}
                checkout_date: {checkout_date}
                guests: {guests}
        """
    )
    # Make the reservation
    # ...
    return True


class HotelReservationsAssistant:
    def __init__(
        self,
        make_reservation: MakeReservation,
        llm: BaseLanguageModel,
    ):
        self.make_reservation = make_reservation
        self.chat_history = ChatMessageHistory()
        self.agent = self.build_agent(llm)

    def build_agent(self, llm):
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT),
                MessagesPlaceholder(variable_name="chat_history"),
                ("user", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        tools = self.build_tools()
        agent: Any = create_openai_functions_agent(llm, tools, prompt)

        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
        )
        return agent_executor

    def __call__(self, query: str) -> str:
        return self.chat(query)

    def chat(self, query: str):
        result = self.agent.invoke(
            {"input": query, "chat_history": self.chat_history.messages},
        )
        response = result["output"]
        self.chat_history.add_messages(
            [
                HumanMessage(content=query),
                AIMessage(content=response),
            ]
        )
        return response

    def build_tools(self) -> list:
        @tool(args_schema=MakeReservationInput)
        def make_reservation_tool(
            hotel_name, guest_name, checkin_date, checkout_date, guests
        ):
            """Useful to make an hotel reservation"""

            return self.make_reservation(
                hotel_name,
                guest_name,
                checkin_date,
                checkout_date,
                guests,
            )

        return [make_reservation_tool]


SYSTEM_PROMPT = """
You are a helpful hotel reservations assistant.
"""
