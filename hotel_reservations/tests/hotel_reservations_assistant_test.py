import datetime
from unittest.mock import Mock

from dotenv import load_dotenv
from hamcrest import assert_that, greater_than

from agents_behave.base_llm import LLMConfig
from agents_behave.conversation_analyser import ConversationAnalyser
from agents_behave.conversation_runner import ConversationRunner
from agents_behave.test_user import TestUser
from hotel_reservations.assistant import HotelReservationsAssistant
from hotel_reservations.core import Hotel, find_hotels, make_reservation
from hotel_reservations.llms import LLM_NAMES, BaseLLM, LLMManager

load_dotenv()

verbose = True


def create_llm(name: str, llm_name: LLM_NAMES) -> BaseLLM:
    return LLMManager.create_llm(
        llm_name=llm_name,
        llm_config=LLMConfig(
            name=name,
            temperature=0.0,
        ),
    )


def test_book_a_room_with_a_budget():
    # Given
    assistant_llm = create_llm("Assistant", "fireworks-firefunctions")
    user_llm = create_llm("User", "openrouter-mixtral")
    conversation_analyser_llm = create_llm("ConversationAnalyser", "openrouter-mixtral")

    make_reservation_mock = Mock(make_reservation, return_value=True)
    find_hotels_return_value = [
        Hotel("123", name="Kensington Hotel", location="London", price_per_night=300),
        Hotel("124", name="Notting Hill Hotel", location="London", price_per_night=400),
    ]
    find_hotels_mock = Mock(find_hotels, return_value=find_hotels_return_value)
    assistant = HotelReservationsAssistant(
        llm=assistant_llm,
        make_reservation=make_reservation_mock,
        find_hotels=find_hotels_mock,
        verbose=verbose,
    )

    persona = """
        My name is John Smith. I don't like answering questions and I'm very rude.
        My goal is to book a room in an hotel in London, starting in 2024-02-09 and ending in 2024-02-11, for 3 guests.
    """
    llm_user = TestUser(
        llm=user_llm,
        persona=persona,
    )

    # When
    def assistant_chat_wrapper(query: str):
        response = assistant.chat(query)
        return response["output"]

    conversation = ConversationRunner(
        assistant=assistant_chat_wrapper,
        user=llm_user,
        stop_condition=lambda state: state.last_assistant_message_contains("bye"),
    )

    conversation_state = conversation.start()

    print("-" * 80)
    for m in conversation_state.chat_history:
        print(f"{'-' * 20}{m.type}{'-' * 20}")
        print(f"{m.content}\n")
    print("-" * 80)

    # Then
    find_hotels_mock.assert_called_once_with("London")
    make_reservation_mock.assert_called_once_with(
        "Kensington Hotel",
        "John Smith",
        datetime.date(2024, 2, 9),
        datetime.date(2024, 2, 11),
        3,
    )

    criteria = [
        "Get the price per night for the reservation and ask the user if it is ok",
        "Ask for all the information needed to make a reservation",
        "Be very polite and helpful",
        "There is no need to ask for the user for anything else, like contact information, payment method, etc.",
    ]
    conversationAnalyzer = ConversationAnalyser(
        llm=conversation_analyser_llm,
    )
    chat_history = conversation_state.chat_history
    response = conversationAnalyzer.analyse(
        chat_history=chat_history, criteria=criteria
    )

    minimum_acceptable_score = 7
    assert_that(
        int(response["score"]),
        greater_than(minimum_acceptable_score),
        reason=response["feedback"],
    )
