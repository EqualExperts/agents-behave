import sys
from typing import cast
from unittest.mock import Mock

from hotel_reservations.assistant import HotelReservationsAssistant
from hotel_reservations.core import Hotel, find_hotels, make_reservation
from hotel_reservations.llms import LLMS, BaseLLM, LLMConfig, LLMManager

from agents_behave.conversation_analyzer import ConversationAnalyzer
from agents_behave.llm_user import LLMUser
from agents_behave.user_conversation import UserConversation


def create_llm(llm_name: LLMS, name: str) -> BaseLLM:
    return LLMManager.create_llm(
        llm_name=llm_name,
        llm_config=LLMConfig(
            name=name,
            temperature=0.0,
        ),
    )


def run(llm_name: LLMS):
    make_reservation_mock = Mock(make_reservation, return_value=True)
    find_hotels_return_value = [
        Hotel("123", name="Kensington Hotel", location="London", price_per_night=300),
        Hotel("124", name="Notting Hill Hotel", location="London", price_per_night=400),
    ]
    find_hotels_mock = Mock(find_hotels, return_value=find_hotels_return_value)
    assistant = HotelReservationsAssistant(
        llm=create_llm(llm_name, "assistant"),
        make_reservation=make_reservation_mock,
        find_hotels=find_hotels_mock,
    )
    persona = """My name is Pedro Sousa.
        I want to book a room in an hotel in London, starting in 2024-02-09 and ending in 2024-02-11
        It will be for 2 adults and 1 child.
        My budget is $350 per night.
    """
    llm_user = LLMUser(
        llm=create_llm(
            llm_name=llm_name,
            name="LLMUser",
        ),
        persona=persona,
    )

    query = "Hi"

    def assistant_chat(query: str):
        response = assistant.chat(query)
        return response["output"]

    conversation = UserConversation(
        assistant=assistant_chat,
        user=llm_user,
        max_iterations=10,
        stop_condition=lambda state: "bye"
        in str(state.chat_history[-1].content).lower(),
    )

    conversation_state = conversation.start_conversation(query)

    criteria = [
        "Say hello to the user",
        "Ask for all the information needed to make a reservation",
        "Be very polite and helpful",
    ]
    criteria = [c.strip() for c in criteria if c.strip()]
    conversationAnalyzer = ConversationAnalyzer(
        llm=create_llm(llm_name, "ConversationAnalyzer")
    )
    chat_history = conversation_state.chat_history
    response = conversationAnalyzer.invoke(chat_history=chat_history, criteria=criteria)

    print(response)


if __name__ == "__main__":
    llm_name = sys.argv[1] if len(sys.argv) > 1 else "openrouter-mixtral"
    run(cast(LLMS, llm_name))
