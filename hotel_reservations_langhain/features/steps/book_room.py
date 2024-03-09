from datetime import datetime
from unittest.mock import Mock

import behave
from hamcrest import assert_that, greater_than
from hotel_reservations.assistant import HotelReservationsAssistant
from hotel_reservations.core import Hotel, find_hotels, make_reservation

from agents_behave.conversation_analyzer import ConversationAnalyzer
from agents_behave.llm_user import LLMUser
from agents_behave.user_agent_conversation import UserAgentConversation


def format_date(date: str):
    return datetime.strptime(date, "%Y-%m-%d").date()


@behave.given("I'm a user with the following persona")
def step_impl(context):  # noqa F811 # type: ignore
    llm = context.llm
    context.llm_user = LLMUser(llm=llm, persona=context.text)


@behave.given("We have the following hotels")
def step_impl(context):  # noqa F811 # type: ignore
    hotels = []
    for row in context.table:
        hotels.append(
            Hotel(row["Id"], row["Name"], row["Location"], row["PricePerNight"])
        )
    context.hotels = hotels


@behave.when(
    "I start a conversation that should end when the assistant says {stop_word}"
)
def step_impl(context, stop_word):  # noqa F811 # type: ignore
    llm = context.llm
    make_reservation_mock = Mock(make_reservation, return_value=True)
    find_hotels_return_value = context.hotels
    find_hotels_mock = Mock(find_hotels, return_value=find_hotels_return_value)
    assistant = HotelReservationsAssistant(
        llm=llm,
        make_reservation=make_reservation_mock,
        find_hotels=find_hotels_mock,
    )
    context.make_reservation_mock = make_reservation_mock

    def assistant_chat(query: str):
        response = assistant.chat(query)
        return response["output"]

    context.conversation = UserAgentConversation(
        llm=llm,
        assistant=assistant_chat,
        user=context.llm_user,
        stop_condition=lambda state: state.last_assistant_message_contains(stop_word),
    )

    context.conversation_state = context.conversation.start()


@behave.then("A reservation should be made for the user with the following details")
def step_impl(context):  # noqa F811 # type: ignore
    lines = context.text.split("\n")
    lines = [line.strip() for line in lines if line.strip()]
    parameters = {
        label.strip(): value.strip()
        for label, value in [line.split(":") for line in lines]
    }

    context.make_reservation_mock.assert_called_once_with(
        hotel_name=parameters["hotel_name"],
        guest_name=parameters["guest_name"],
        checkin_date=format_date(parameters["checkin_date"]),
        checkout_date=format_date(parameters["checkout_date"]),
        guests=int(parameters["guests"]),
    )


@behave.then(
    "The conversation should fullfill the following criteria, with a score above {score}"
)
def step_impl(context, score):  # noqa F811 # type: ignore
    criteria = context.text.split("\n")
    criteria = [c.strip() for c in criteria if c.strip()]
    conversationAnalyzer = ConversationAnalyzer(llm=context.llm)
    chat_history = context.conversation_state.chat_history
    response = conversationAnalyzer.invoke(chat_history=chat_history, criteria=criteria)
    assert_that(
        int(response["score"]),
        greater_than(int(score)),
        reason=response["feedback"],
    )
