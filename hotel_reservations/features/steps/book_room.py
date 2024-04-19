from datetime import datetime
from unittest.mock import Mock

import behave
from hamcrest import assert_that, greater_than

from agents_behave.conversation_analyser import ConversationAnalyser
from agents_behave.conversation_runner import ConversationRunner
from agents_behave.test_user import TestUser
from hotel_reservations.assistant import HotelReservationsAssistant
from hotel_reservations.core import Hotel, find_hotels, make_reservation


def format_date(date: str):
    return datetime.strptime(date, "%Y-%m-%d").date()


@behave.given("A user with the following persona")
def step_impl(context):  # noqa F811 # type: ignore
    context.llm_user = TestUser(
        llm=context.user_llm,
        persona=context.text,
    )


@behave.given("We have the following hotels")
def step_impl(context):  # noqa F811 # type: ignore
    hotels = []
    for row in context.table:
        hotels.append(
            Hotel(row["Id"], row["Name"], row["Location"], row["PricePerNight"])
        )
    context.hotels = hotels


@behave.given("Today is {date}")
def step_impl(context, date):  # noqa F811 # type: ignore
    context.date = format_date(date)


@behave.when(
    "The user starts a conversation that should end when the assistant says {stop_word}"
)
def step_impl(context, stop_word):  # noqa F811 # type: ignore
    make_reservation_mock = Mock(make_reservation, return_value=True)
    find_hotels_return_value = context.hotels
    find_hotels_mock = Mock(find_hotels, return_value=find_hotels_return_value)
    current_date_mock = Mock(return_value=context.date)
    assistant = HotelReservationsAssistant(
        llm=context.assistant_llm,
        make_reservation=make_reservation_mock,
        find_hotels=find_hotels_mock,
        current_date=current_date_mock,
    )
    context.make_reservation_mock = make_reservation_mock
    context.find_hotels_mock = find_hotels_mock

    def assistant_chat_wrapper(query: str):
        response = assistant.chat(query)
        return response["output"]

    context.conversation = ConversationRunner(
        assistant=assistant_chat_wrapper,
        user=context.llm_user,
        stop_condition=lambda state: state.last_assistant_message_contains(stop_word),
    )

    context.conversation_state = context.conversation.start()


@behave.then("The assistant should get the hotels in {location}")
def step_impl(context, location):  # noqa F811 # type: ignore
    context.find_hotels_mock.assert_called_once_with(location)


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
    "The conversation should fullfill the following criteria, with a score above {minimum_acceptable_score}"
)
def step_impl(context, minimum_acceptable_score):  # noqa F811 # type: ignore
    criteria = context.text.split("\n")
    criteria = [c.strip() for c in criteria if c.strip()]
    conversationAnalyzer = ConversationAnalyser(llm=context.analyzer_llm)
    chat_history = context.conversation_state.chat_history
    response = conversationAnalyzer.analyse(
        chat_history=chat_history, criteria=criteria
    )
    assert_that(
        int(response["score"]),
        greater_than(int(minimum_acceptable_score)),
        reason=response["feedback"],
    )

    print(response["feedback"])
