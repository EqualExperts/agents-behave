import json
from datetime import date
from typing import Any

from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain.pydantic_v1 import BaseModel, Field
from langchain_core.language_models.base import BaseLanguageModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_core.tools import tool
from langchain_core.utils.function_calling import convert_to_openai_function

from hotel_reservations.core import FindHotels, MakeReservation
from hotel_reservations.function_call_agent_output_parser import (
    FunctionCallAgentOutputParser,
)
from hotel_reservations.open_ai_functions_agent_output_parser_copy import (
    OpenAIFunctionsAgentOutputParser_Copy,
)


class MakeReservationInput(BaseModel):
    hotel_name: str = Field(
        description="The name of the hotel, exactly has returned by the find_hotels tool."
    )
    guest_name: str = Field(description="The name of the guest.")
    checkin_date: date = Field(description="The checkin date.")
    checkout_date: date = Field(description="The checkout date.")
    guests: int = Field(description="The number of guests.")


class FindHotelsInput(BaseModel):
    name: str = Field(description="The name of the hotel.", default="")
    location: str = Field(description="The location of the hotel.", default="")


class HotelReservationsAssistant:
    def __init__(
        self,
        llm: BaseLanguageModel,
        make_reservation: MakeReservation,
        find_hotels: FindHotels,
    ):
        self.make_reservation = make_reservation
        self.find_hotels = find_hotels
        self.chat_history = []
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
        functions = [convert_to_openai_function(tool) for tool in tools]

        supports_functions = False
        if supports_functions:
            llm = llm.bind(functions=[convert_to_openai_function(t) for t in tools])
            prompt = prompt.partial(tools_prompt="")
            parser = OpenAIFunctionsAgentOutputParser_Copy()
        else:
            tools_json = f"{json.dumps(functions, indent=2)}\n"
            tools_prompt = TOOLS_PROMPT.format(tools=tools_json)
            prompt = prompt.partial(tools_prompt=tools_prompt)
            parser = FunctionCallAgentOutputParser()

        agent: Any = (
            RunnablePassthrough.assign(
                agent_scratchpad=lambda x: format_to_openai_function_messages(
                    x["intermediate_steps"]
                )
            )
            | prompt
            | llm
            | parser
        )

        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
        )
        return agent_executor

    def chat(self, query: str):
        response = self.agent.invoke(
            {"input": query, "chat_history": self.chat_history},
        )
        self.chat_history.append(HumanMessage(content=query))
        self.chat_history.append(AIMessage(content=response["output"]))
        return response

    def build_tools(self):
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

        @tool(args_schema=FindHotelsInput)
        def find_hotels_tool(name: str = "", location: str = ""):
            """Useful to find hotels by name and/or location."""
            return self.find_hotels(name, location)

        tools: list = [make_reservation_tool, find_hotels_tool]
        return tools


SYSTEM_PROMPT = """
You are a helpful hotel reservations assistant.
You should not come up with any information, if you don't know something, just ask the user for more information or use a tool.
The name of the guest is mandatory to make the reservation.

{tools_prompt}
"""  # noqa E501


TOOLS_PROMPT = """
    You have some tools available to help you with the user query.
    You MUST use a tool to make a reservation.
    Here are the tools available to you:
    {tools}
    --------------------
    
    Think about the user query step by step and decide if you need to use a tool for the next step.
    Use only one tool at a time.

    if you do need to use a tool, you MUST return a response in the following JSON format:
    {{
        "function_call": {{
            "name": "add_numbers",
            "arguments": {{
                "a": 1,
                "b": 2
            }}
        }}
    }}
"""
