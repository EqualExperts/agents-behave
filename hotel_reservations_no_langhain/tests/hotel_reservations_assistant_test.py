from datetime import date
from unittest.mock import Mock

from dotenv import load_dotenv
from hamcrest import assert_that, greater_than
from hotel_reservations.assistant import HotelReservationsAssistant, make_reservation
from hotel_reservations.conversation_analyzer import ConversationAnalyzer
from hotel_reservations.llm_user import LLMUser
from hotel_reservations.llms import LLMConfig, LLMManager
from hotel_reservations.user_agent_conversation import UserAgentConversation

from hotel_reservations_no_langhain.hotel_reservations.callbacks import (
    ConsoleLLMCallbacks,
)

load_dotenv()


def test_i_want_to_book_a_room():
    callbacks = ConsoleLLMCallbacks()
    llm = LLMManager.create_llm(
        llm="openrouter-mixtral",
        llm_config=LLMConfig(
            temperature=0.0,
            callbacks=callbacks,
        ),
    )
    persona = """
        My name is Pedro Sousa.
        I want to book a room in the Hilton Hotel, starting in 2024-02-09 and ending in 2024-02-11.
        It will be for 2 adults.
    """
    user = LLMUser(persona=persona, llm=llm)

    make_reservation_mock = Mock(make_reservation, return_value=True)
    assistant = HotelReservationsAssistant(
        make_reservation=make_reservation_mock,
        llm=llm,
    )

    conversation = UserAgentConversation(
        user,
        assistant,
        llm=llm,
        stop_condition=lambda state: state.iterations_count >= 10
        or "bye" in str(state.last_message().content).lower(),
    )
    conversation_state = conversation.start("I want to book a room")

    print("-" * 80)
    for message in conversation_state.chat_history.messages:
        print(message)
    print("-" * 80)

    criteria = [
        "Ask for the information needed to make a reservation",
        "Be polite and helpful",
    ]
    conversation_analyzer = ConversationAnalyzer(llm=llm)
    report = conversation_analyzer.analyze(
        conversation=conversation_state.chat_history,
        criteria=criteria,
    )

    assert_that(report.score, greater_than(0))

    make_reservation_mock.assert_called_once_with(
        hotel_name="Hilton Hotel",
        guest_name="Pedro Sousa",
        checkin_date=date(2024, 2, 9),
        checkout_date=date(2024, 2, 11),
        guests=2,
    )
