import json
from dataclasses import dataclass
from datetime import date
from random import randint
from typing import Callable

from colorama import Fore
from hotel_reservations.messages import (
    AssistantMessage,
    ChatResponseMessage,
    LLMMessage,
    LLMMessages,
    SystemMessage,
    ToolMessage,
    UserMessage,
)
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.utils.function_calling import convert_to_openai_function
from openai._types import NOT_GIVEN
from openai.types.chat import ChatCompletionMessageToolCall

from hotel_reservations_no_langhain.hotel_reservations.llms import BaseLLM

MakeReservationType = Callable[[str, str, date, date, int], bool]
GetHotelPricePerNightType = Callable[[str, date, date], float]


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
        f"""{Fore.RED}
        Making reservation for:
                guest_name: {guest_name}
                hotel_name: {hotel_name}
                checkin_date: {checkin_date}
                checkout_date: {checkout_date}
                guests: {guests}
        {Fore.RESET}
        """
    )
    # Make the reservation
    # ...
    return True

    """Books a room in a hotel for a specified guest and date range."""


class MakeReservation(BaseModel):

    hotel_name: str = Field(description="the name of the hotel")
    guest_name: str = Field(description="the name of the guest")
    checkin_date: str = Field(
        description="the start date of the reservation (YYYY-MM-DD)"
    )
    checkout_date: str = Field(
        description="the end date of the reservation (YYYY-MM-DD)"
    )
    guests: int = Field(description="the number of guests")


def get_hotel_price_per_night(
    hotel_name: str, checkin_date: date, checkout_date: date
) -> float:
    price = randint(100, 500)
    print(
        f"""{Fore.RED}
        Getting price per night for:
                hotel_name: {hotel_name}
                checkin_date: {checkin_date}
                checkout_date: {checkout_date}

        Price per night: {price}
        {Fore.RESET}
        """
    )
    return price


class GetHotelPricePerNight(BaseModel):
    """Gets the price per night of a hotel."""

    hotel_name: str = Field(description="the name of the hotel")
    checkin_date: str = Field(
        description="the start date of the reservation (YYYY-MM-DD)"
    )
    checkout_date: str = Field(
        description="the end date of the reservation (YYYY-MM-DD)"
    )


class HotelReservationsAssistant:
    def __init__(
        self,
        make_reservation: MakeReservationType,
        get_hotel_price_per_night: GetHotelPricePerNightType,
        llm: BaseLLM,
    ):
        self.make_reservation = make_reservation
        self.get_hotel_price_per_night = get_hotel_price_per_night
        self.chat_history = LLMMessages()
        self.llm = llm

        self.tool_handlers = {
            "MakeReservation": self.make_reservation_handler,
            "GetHotelPricePerNight": self.get_hotel_price_per_night_handler,
        }

    def make_reservation_handler(self, arguments: dict):
        hotel_name = arguments["hotel_name"]
        guest_name = arguments["guest_name"]
        checkin_date = date.fromisoformat(arguments["checkin_date"])
        checkout_date = date.fromisoformat(arguments["checkout_date"])
        guests = arguments["guests"]
        result = self.make_reservation(
            hotel_name, guest_name, checkin_date, checkout_date, guests
        )
        return (
            f"The reservation for {guest_name} at {hotel_name} was successful: {result}"
        )

    def get_hotel_price_per_night_handler(self, arguments: dict):
        hotel_name = arguments["hotel_name"]
        checkin_date = date.fromisoformat(arguments["checkin_date"])
        checkout_date = date.fromisoformat(arguments["checkout_date"])
        result = self.get_hotel_price_per_night(hotel_name, checkin_date, checkout_date)
        return f"The price per night at {hotel_name} is ${result}"

    def __call__(self, query: str) -> str:
        return self.chat(query)

    def chat(self, user_message: str) -> str:
        self.chat_history.add_message(UserMessage(user_message))
        response_message = self.get_response()
        self.chat_history.add_message(response_message)

        return response_message.content or ""

    def get_response(
        self,
        extra_messages: LLMMessages | None = None,
        recursion_level=0,
    ) -> LLMMessage:
        if recursion_level > 2:
            return AssistantMessage(content="done")

        prompt = (
            SYSTEM_PROMPT
            if self.llm.supports_function_calling()
            else SYSTEM_PROMPT_NO_FUNCTIONS
        )

        available_tools = [
            MakeReservation,
            GetHotelPricePerNight,
        ]

        if self.llm.supports_function_calling():
            prompt = SYSTEM_PROMPT
            tools = available_tools
        else:
            fn = """{"name": "function_name", "arguments": {"arg_1": "value_1", "arg_2": value_2, ...}}"""
            tools_json = [
                str(convert_to_openai_function(tool)) for tool in available_tools
            ]
            prompt = SYSTEM_PROMPT_NO_FUNCTIONS.format(
                tools="\n".join(tools_json), fn=fn
            )
            tools = NOT_GIVEN

        extra_messages = extra_messages or LLMMessages()
        messages = LLMMessages(
            [
                SystemMessage(prompt),
                *self.chat_history,
                *extra_messages,
                # AssistantMessage(content=""),
            ]
        )

        # print("-" * 80)
        # print(messages)
        # print("-" * 80)

        completion_message = self.llm.chat_completions(messages=messages, tools=tools)

        if completion_message.tool_calls:
            response_message = self.call_tool(
                completion_message.tool_calls[0], recursion_level
            )
        else:
            response_message = AssistantMessage(content=completion_message.content)
        return response_message

    def call_tool(
        self, tool_call: ChatCompletionMessageToolCall, recursion_level: int
    ) -> LLMMessage:
        function_name = tool_call.function.name
        tool_handler = self.tool_handlers[function_name]
        tool_call_id = tool_call.id
        arguments = tool_call.function.arguments
        json_arguments = json.loads(arguments)
        tool_result = tool_handler(json_arguments)
        if self.llm.supports_function_calling():
            tool_calls_message = ChatResponseMessage(
                content=tool_call.function.name, tool_calls=[tool_call]
            )
            tool__message = ToolMessage(content=tool_result, tool_call_id=tool_call_id)
            extra_messages = LLMMessages([tool_calls_message, tool__message])
        else:
            tool__message = AssistantMessage(content=tool_result)
            extra_messages = LLMMessages([tool__message])
        response_message = self.get_response(
            extra_messages=extra_messages,
            recursion_level=recursion_level + 1,
        )
        return response_message


SYSTEM_PROMPT = """
You are a helpful hotel reservations assistant.
You should not come up with any information, if you don't know something, just ask the user for more information.
The name of guest is mandatory to make the reservation.
You should present the user with the price per night before making the reservation. Use a 
Ask the user for confirmation before making the reservation.
You should say goodbye when you are done.
"""

SYSTEM_PROMPT_NO_FUNCTIONS = """
You have with access to the following functions:

{tools}

To use these functions respond with:
<multiplefunctions>
    <functioncall> {fn} </functioncall>
    <functioncall> {fn} </functioncall>
    ...
</multiplefunctions>

Edge cases you must handle:
- If you need to ask for more information, you can ask the user for it. Do not return any functions in this case.

You should not come up with any information, if you don't know something, just ask the user for more information.
The name of guest is mandatory to make the reservation.
You should present the user with the price per night before making the reservation. Use a 
Ask the user for confirmation before making the reservation.
You should say goodbye when you are done.

"""
