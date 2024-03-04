import json
from dataclasses import dataclass
from datetime import date
from typing import Callable

from hotel_reservations.messages import (
    AssistantMessage,
    LLMMessage,
    LLMMessages,
    SystemMessage,
    UserMessage,
)

from hotel_reservations_no_langhain.hotel_reservations.llms import OpenAIBaseLLM

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
        llm: OpenAIBaseLLM,
    ):
        self.make_reservation = make_reservation
        self.chat_history = LLMMessages()
        self.llm = llm

    def __call__(self, query: str) -> str:
        return self.chat(query)

    def chat(self, query: str) -> str:
        prompt = SYSTEM_PROMPT
        # prompt = prompt.format(
        #     tools_prompt=TOOLS_PROMPT.format(
        #         tools=json.dumps([make_reservation_tool], indent=4)
        #     )
        # )
        messages = LLMMessages(
            [
                SystemMessage(prompt),
                *self.chat_history.messages,
                UserMessage(query),
            ]
        )
        tools = [make_reservation_tool]
        completion = self.llm.chat_completions(messages=messages, tools=tools)  # type: ignore
        response = completion.choices[0]
        if response.message.tool_calls:
            tool_call = response.message.tool_calls[0]
            if tool_call.function.name == "make_reservation":
                arguments = tool_call.function.arguments
                json_arguments: dict = json.loads(arguments)
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
            response_message = LLMMessage.from_openai_message(
                completion.choices[0].message
            )
        self.chat_history.add_message(response_message)

        return response_message.content or ""


SYSTEM_PROMPT = """
You are a helpful hotel reservations assistant.
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
