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
from openai._types import NOT_GIVEN
from openai.types.chat import ChatCompletionMessageToolCall

from hotel_reservations_no_langhain.hotel_reservations.llms import BaseLLM

MakeReservation = Callable[[str, str, date, date, int], bool]
GetHotelPricePerNight = Callable[[str, date, date], float]


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


make_reservation_tool = {
    "type": "function",
    "function": {
        "name": "make_reservation",
        "description": "Useful to make an hotel reservation",
        "parameters": {
            "type": "object",
            "properties": {
                "guest_name": {
                    "type": "string",
                    "description": "The name of the guest",
                },
                "hotel_name": {
                    "type": "string",
                    "description": "The name of the hotel",
                },
                "checkin_date": {
                    "type": "string",
                    "format": "date",
                    "description": "The checkin date (YYYY-MM-DD)",
                },
                "checkout_date": {
                    "type": "string",
                    "format": "date",
                    "description": "The checkout date (YYYY-MM-DD)",
                },
                "guests": {
                    "type": "integer",
                    "description": "The number of guests",
                },
            },
            "required": [
                "guest_name",
                "hotel_name",
                "checkin_date",
                "checkout_date",
                "guests",
            ],
        },
    },
}


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


get_hotel_price_per_night_tool = {
    "type": "function",
    "function": {
        "name": "get_hotel_price_per_night",
        "description": "Useful to get the price per night of an hotel",
        "parameters": {
            "type": "object",
            "properties": {
                "hotel_name": {
                    "type": "string",
                    "description": "The name of the hotel",
                },
                "checkin_date": {
                    "type": "string",
                    "format": "date",
                    "description": "The checkin date (YYYY-MM-DD)",
                },
                "checkout_date": {
                    "type": "string",
                    "format": "date",
                    "description": "The checkout date (YYYY-MM-DD)",
                },
            },
            "required": ["hotel_name", "checkin_date", "checkout_date"],
        },
    },
}


class HotelReservationsAssistant:
    def __init__(
        self,
        make_reservation: MakeReservation,
        get_hotel_price_per_night: GetHotelPricePerNight,
        llm: BaseLLM,
    ):
        self.make_reservation = make_reservation
        self.get_hotel_price_per_night = get_hotel_price_per_night
        self.chat_history = LLMMessages()
        self.llm = llm

        self.tool_handlers = {
            "make_reservation": self.make_reservation_handler,
            "get_hotel_price_per_night": self.get_hotel_price_per_night_handler,
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
        return f"The price per night at {hotel_name} is {result}"

    def __call__(self, query: str) -> str:
        return self.chat(query)

    def chat(self, user_message: str) -> str:
        self.c = 0
        response_message = self.get_response(user_message)
        self.chat_history.add_message(UserMessage(user_message))
        self.chat_history.add_message(response_message)

        return response_message.content or ""

    def get_response(
        self,
        user_message: str,
        extra_messages: LLMMessages | None = None,
        recursion_level=0,
    ) -> LLMMessage:
        if recursion_level > 2:
            return AssistantMessage(content="done")

        prompt = SYSTEM_PROMPT
        tools = [
            make_reservation_tool,
            get_hotel_price_per_night_tool,
        ]

        tools_prompt = (
            ""
            if self.llm.supports_function_calling()
            else TOOLS_PROMPT.format(tools=json.dumps(tools, indent=4))
        )
        prompt = prompt.format(tools_prompt=tools_prompt)
        extra_messages = extra_messages or LLMMessages()
        messages = LLMMessages(
            [
                SystemMessage(prompt),
                *self.chat_history,
                *extra_messages,
            ]
        )
        if user_message:
            messages.add_message(UserMessage(user_message))

        completion_message = self.llm.chat_completions(
            messages=messages,
            tools=tools if self.llm.supports_function_calling() else NOT_GIVEN,  # type: ignore
        )
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
        tool_calls_message = ChatResponseMessage(
            content=tool_call.function.name, tool_calls=[tool_call]
        )
        tool__message = ToolMessage(content=tool_result, tool_call_id=tool_call_id)
        extra_messages = LLMMessages([tool_calls_message, tool__message])
        response_message = self.get_response(
            "",
            extra_messages=extra_messages,
            recursion_level=recursion_level + 1,
        )
        return response_message


SYSTEM_PROMPT = """
You are a helpful hotel reservations assistant.
You should not come up with any information, if you don't know something, just ask the user for more information or use a tool.
Ask the user for confirmation before making the reservation.
You should say goodbye when you are done.

{tools_prompt}
"""  # noqa E501

TOOLS_PROMPT = """
You have some tools available to help you with the user query.
Here is how you should handle user requests:

- Understand the user requirements.
- Decide if you need to use a tool to get the information you need.
- The tools available are: [get_hotel_price_per_night, make_reservation]
- If you need to use a tool, just return the tool call, the result will appear in the next message.

You must use the tool get_hotel_price_per_night to inform the user of the price per night and ask for confirmation before making the reservation.

Here are the tools available for you to use:
{tools}
--------------------

Your response should always be in JSON format, using the following structure:
{{
    "content": "<your_response>"
    "function_call": {{
        "name": "<function_name>",
        "arguments": {{
            "<arg_1>": <arg_1_value>,
            "<arg_2>": <arg_2_value>
        }}
    }}
}}
---------------------
Return only one of fields "content" or "function_call".

"""  # noqa E501
