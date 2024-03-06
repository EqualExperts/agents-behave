import json
from dataclasses import dataclass
from datetime import date
from typing import Callable

from colorama import Fore
from hotel_reservations.messages import (
    AssistantMessage,
    LLMMessage,
    LLMMessages,
    SystemMessage,
    UserMessage,
)
from openai._types import NOT_GIVEN
from openai.types.chat import ChatCompletionMessageToolCall

from hotel_reservations_no_langhain.hotel_reservations.llms import BaseLLM

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


class HotelReservationsAssistant:
    def __init__(
        self,
        make_reservation: MakeReservation,
        llm: BaseLLM,
    ):
        self.make_reservation = make_reservation
        self.chat_history = LLMMessages()
        self.llm = llm

        self.tools = {
            "make_reservation": self.make_reservation,
        }

    def __call__(self, query: str) -> str:
        return self.chat(query)

    def chat(self, user_message: str) -> str:
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
                UserMessage(user_message),
            ]
        )
        tools = (
            [make_reservation_tool]
            if self.llm.supports_function_calling()
            else NOT_GIVEN
        )

        message = self.llm.chat_completions(messages=messages, tools=tools)  # type: ignore
        if message.tool_calls:
            response_message = self.call_tool(message.tool_calls[0])
        else:
            response_message = AssistantMessage(content=message.content)
        self.chat_history.add_message(UserMessage(user_message))
        self.chat_history.add_message(response_message)

        return response_message.content or ""

    def call_tool(self, tool_call: ChatCompletionMessageToolCall) -> LLMMessage:
        function_name = tool_call.function.name
        tool = self.tools[function_name]
        # tool_call_id = tool_call.id
        arguments = tool_call.function.arguments
        json_arguments = json.loads(arguments)
        json_arguments["checkin_date"] = date.fromisoformat(
            json_arguments["checkin_date"]
        )
        json_arguments["checkout_date"] = date.fromisoformat(
            json_arguments["checkout_date"]
        )
        tool_result = tool(**json_arguments)  # type: ignore
        # content = f"Called Function {function_name} with arguments {arguments}. Result: {tool_result}"
        # tool_message = ToolMessage(content=content, tool_call_id=tool_call_id)
        # self.chat_history.add_message(tool_message)
        if tool_result:
            content = "Reservation made successfully"
        else:
            content = "Reservation failed"
        response_message = AssistantMessage(content=content)
        self.chat_history.add_message(response_message)
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
Do not mention the tools to the user.

Here are the tools available to you:
{tools}
--------------------

Think about the user query step by step and decide if you need to use a tool for the next step.
Ask the user for more information if you need it.

Your response should always be in JSON format, using the following structure:
{{
    "content": "<your_response>"
    "function_call": <if you need to use a tool>
}}
---------------------

if you need to use a tool, the schema of the function call is:
{{
    "name": "<function_name>",
    "arguments": {{
        "<arg_1>": <arg_1_value>,
        "<arg_2>": <arg_2_value>
    }}
}}
---------------------
"""
