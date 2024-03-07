from datetime import datetime
from unittest.mock import Mock

import behave
from hamcrest import assert_that, greater_than

from agents_behave.conversation_analyzer import ConversationAnalyzer
from agents_behave.llm_user import LLMUser
from agents_behave.user_conversation import UserConversation
from hotel_reservations.assistant import HotelReservationsAssistant
from hotel_reservations.core import Hotel, find_hotels, make_reservation


def format_date(date: str):
    return datetime.strptime(date, "%Y-%m-%d").date()


@behave.given("I'm a user with the following persona")
def step_impl(context):  # noqa F811 # type: ignore
    llm = context.model_config.llm
    context.llm_user = LLMUser(llm=llm, persona=context.text)


@behave.when('I say "{query}"')
def step_impl(context, query):  # noqa F811 # type: ignore
    context.query = query


@behave.then('The conversation should end when the user says "{stop}"')
def step_impl(context, stop):  # noqa F811 # type: ignore
    llm = context.model_config.llm
    make_reservation_mock = Mock(make_reservation, return_value=True)
    find_hotels_return_value = [
        Hotel("123", name="Kensington Hotel", location="London"),
    ]
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

    context.conversation = UserConversation(
        assistant=assistant_chat,
        user=context.llm_user,
        max_iterations=10,
        stop_condition=lambda state: stop.lower()
        in str(state.chat_history[-1].content).lower(),
    )

    context.conversation_state = context.conversation.start_conversation(
        context.query,
    )


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
    conversationAnalyzer = ConversationAnalyzer(llm=context.model_config.llm)
    chat_history = context.conversation_state.chat_history
    response = conversationAnalyzer.invoke(chat_history=chat_history, criteria=criteria)
    assert_that(
        int(response["score"]),
        greater_than(int(score)),
        reason=response["feedback"],
    )