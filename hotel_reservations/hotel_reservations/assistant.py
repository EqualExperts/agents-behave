from datetime import date
from typing import Any

from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad import (
    format_log_to_str,
    format_to_openai_function_messages,
)
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools.render import render_text_description_and_args
from langchain_core.language_models.base import BaseLanguageModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.runnables import RunnablePassthrough
from langchain_core.tools import tool
from langchain_core.utils.function_calling import convert_to_openai_function

from agents_behave.base_llm import BaseLLM
from hotel_reservations.core import FindHotels, MakeReservation
from hotel_reservations.function_call_agent_output_parser import (
    FunctionCallAgentOutputParser,
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
        llm: BaseLLM,
        make_reservation: MakeReservation,
        find_hotels: FindHotels,
        current_date=lambda: date.today(),
        verbose=False,
    ):
        self.make_reservation = make_reservation
        self.find_hotels = find_hotels
        self.current_date = current_date
        self.verbose = verbose

        self.chat_history: list[BaseMessage] = []
        self.agent = self.build_agent(llm)

    def build_agent(self, llm: BaseLLM):
        tools = self.build_tools()
        agent: Any
        if llm.supports_function_calling():
            agent = self.build_agent_with_function_calling(llm.llm, tools)
        else:
            agent = self.build_agent_without_function_calling(llm.llm, tools)

        return AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=self.verbose,
            return_intermediate_steps=True,
            handle_parsing_errors=True,
            max_iterations=5,
        )

    def build_agent_with_function_calling(self, llm: BaseLanguageModel, tools: list):
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT),
                MessagesPlaceholder(variable_name="chat_history"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )
        prompt = prompt.partial(
            current_date=self.current_date().strftime("%Y-%m-%d"),
        )

        functions = [convert_to_openai_function(tool) for tool in tools]
        llm_with_tools = llm.bind(functions=functions)

        return (
            RunnablePassthrough.assign(
                agent_scratchpad=lambda x: format_to_openai_function_messages(
                    x["intermediate_steps"]
                )
            )
            | prompt
            | llm_with_tools
            | OpenAIFunctionsAgentOutputParser()
        )

    def build_agent_without_function_calling(self, llm: BaseLanguageModel, tools: list):
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT_NO_FUNCTION_CALLING),
                MessagesPlaceholder(variable_name="chat_history"),
            ]
        )

        prompt = prompt.partial(
            tool_description_with_args=render_text_description_and_args(tools),
            tool_names=", ".join([t.name for t in tools]),
            current_date=self.current_date().strftime("%Y-%m-%d"),
        )

        llm_with_stop = llm.bind(stop=["\nObservation"])

        return (
            RunnablePassthrough.assign(
                agent_scratchpad=lambda x: format_log_to_str(x["intermediate_steps"])
            )
            | prompt
            | llm_with_stop
            | FunctionCallAgentOutputParser()
        )

    def chat(self, query: str):
        self.chat_history.append(HumanMessage(content=query))
        response = self.agent.invoke({"chat_history": self.chat_history})
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
        def find_hotels_tool(location: str):
            """Useful to find hotels by name and/or location."""
            return self.find_hotels(location)

        tools: list = [make_reservation_tool, find_hotels_tool]
        return tools


SYSTEM_PROMPT = """
You are a helpful hotel reservations assistant.
The name of the guest is mandatory to make the reservation, ensure you ask for it.
You should present the user with the price per night before making the reservation.
Ask the user for confirmation before making the reservation.

Today is {current_date}.
"""

SYSTEM_PROMPT_NO_FUNCTION_CALLING = """You are a helpful assistant that can make room reservations. 
You should keep a conversation with the user and help them make a reservation. Ask for all the information needed to make a reservation.

You have access to the following tools:

{tool_description_with_args}

The way you use the tools is by specifying a json blob.
Specifically, this json should have a `action` key (name of the tool to use) and a `action_input` key (input to the tool).

The only values that should be in the "action" field are: {tool_names}

The $JSON_BLOB should only contain a SINGLE action and MUST be formatted as markdown, do NOT return a list of multiple actions. Here is an example of a valid $JSON_BLOB:

```
{{
  "action": $TOOL_NAME,
  "action_input": $INPUT
}}
```
Make sure to have the $INPUT in the right format for the tool you are using, and do not put variable names as input if you can find the right values.

You should ALWAYS use the following format:

Thought: you should always think about one action to take. Then use the action as follows:
Action:
```
$JSON_BLOB
```
Observation: the result of the action
... (this Thought/Action/Observation can repeat N times, you should take several steps when needed. The $JSON_BLOB must only use a SINGLE action at a time.)

If you need to ask for more information, you can ask the user for it. Do not return the $JSON_BLOB if you need to ask for more information.

{agent_scratchpad}
"""  # noqa E501

HUMAN_PROMPT = "Question: {input}"

SCRATCHPAD_PROMPT = "{agent_scratchpad}"
