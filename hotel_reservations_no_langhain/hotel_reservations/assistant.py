import json
from dataclasses import dataclass
from datetime import date
from typing import Callable

from hotel_reservations.llms import BaseLLM
from hotel_reservations.messages import (
    AssistantMessage,
    LLMMessages,
    SystemMessage,
    UserMessage,
)

MakeReservation = Callable[[str, str, date, date, int], bool]


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
                    "description": "The checkin date",
                },
                "checkout_date": {
                    "type": "string",
                    "format": "date",
                    "description": "The checkout date",
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


class HotelReservationsAssistant:
    def __init__(
        self,
        make_reservation: MakeReservation,
        llm: BaseLLM,
    ):
        self.make_reservation = make_reservation
        self.chat_history = LLMMessages()
        self.llm = llm

    def __call__(self, query: str) -> str:
        return self.chat(query)

    def chat(self, query: str) -> str:
        prompt = SYSTEM_PROMPT
        tools_prompt = (
            ""
            if self.llm.supports_function_calling()
            else TOOLS_PROMPT.format(
                tools=json.dumps([make_reservation_tool], indent=4)
            )
        )
        prompt = prompt.format(tools_prompt=tools_prompt)
        messages = LLMMessages(
            [
                SystemMessage(prompt),
                *self.chat_history.messages,
                UserMessage(query),
            ]
        )
        tools = [make_reservation_tool]
        message = self.llm.chat_completions(messages=messages, tools=tools)  # type: ignore
        if message.tool_calls:
            tool_call = message.tool_calls[0]
            if tool_call.function.name == "make_reservation":
                arguments = tool_call.function.arguments
                json_arguments = json.loads(arguments)
                json_arguments["checkin_date"] = date.fromisoformat(
                    json_arguments["checkin_date"]
                )
                json_arguments["checkout_date"] = date.fromisoformat(
                    json_arguments["checkout_date"]
                )
                tool_result = self.make_reservation(**json_arguments)  # type: ignore
                if tool_result:
                    response_message = AssistantMessage(
                        content="Reservation made successfully",
                    )
                else:
                    response_message = AssistantMessage(
                        content="Failed to make reservation",
                    )
                self.chat_history.add_message(response_message)
        else:
            response_message = AssistantMessage(content=message.content)
        self.chat_history.add_message(response_message)

        return response_message.content or ""


SYSTEM_PROMPT = """
You are a helpful hotel reservations assistant.
You should not come up with any information, if you don't know something, just ask the user for more information or use a tool.
The name of the guest is mandatory to make the reservation.

{tools_prompt}
"""  # noqa E501


TOOLS_PROMPT = """
You have some tools available to help you with the user query.
Do not mention the tools to the user.

Here are the tools available to you:
{tools}
--------------------

Think about the user query step by step and decide if you need to use a tool for the next step.
Ask the user for more information if you need it.

if you do need to use a tool, you MUST return a response in the following JSON format:
{{
    "function_call": {{
        "name": "<function_name>",
        "arguments": {{
            "<arg_1>": <arg_1_value>,
            "<arg_2>": <arg_2_value>
        }}
    }}
}}
"""
