import sys
from typing import cast
from unittest.mock import Mock

from agents_behave.conversation_analyser import ConversationAnalyser
from agents_behave.llm_user import LLMUser
from agents_behave.user_agent_conversation import UserAssistantConversation
from hotel_reservations.assistant import HotelReservationsAssistant
from hotel_reservations.core import Hotel, find_hotels, make_reservation
from hotel_reservations.llms import LLM_NAMES, BaseLLM, LLMConfig, LLMManager


def create_llm(llm_name: LLM_NAMES, name: str) -> BaseLLM:
    return LLMManager.create_llm(
        llm_name=llm_name,
        llm_config=LLMConfig(
            name=name,
            temperature=0.0,
        ),
    )


def run(llm_name: LLM_NAMES):
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
    persona = """
        My name is John Smith. I don't like answering questions and I'm not very polite.
        My goal is to book a room in an hotel in London, starting in 2024-02-09 and ending in 2024-02-11, for 3 guests.
        I will not provide any information unless asked.
    """  # noqa E501
    llm_user = LLMUser(
        llm=create_llm(llm_name=llm_name, name="LLMUser"),
        persona=persona,
    )

    def assistant_chat_wrapper(query: str):
        response = assistant.chat(query)
        return response["output"]

    conversation = UserAssistantConversation(
        user=llm_user,
        assistant=assistant_chat_wrapper,
        stop_condition=lambda state: "bye"
        in str(state.chat_history[-1].content).lower(),
    )

    conversation_state = conversation.start()

    criteria = [
        "Get the price per night for the reservation and ask the user if it is ok",
        "Ask for all the information needed to make a reservation",
        "Make the reservation",
        "Be very polite and helpful",
        "There is no need to ask for the user for anything else, like contact information, payment method, etc.",
    ]
    criteria = [c.strip() for c in criteria if c.strip()]
    conversationAnalyser = ConversationAnalyser(
        llm=create_llm(llm_name, "ConversationAnalyzer")
    )
    chat_history = conversation_state.chat_history

    print("-" * 100)
    for message in chat_history:
        print(f"{message.type}:\n{message.content}")
    print("-" * 100)

    response = conversationAnalyser.analyse(
        chat_history=chat_history, criteria=criteria
    )

    print(response)


if __name__ == "__main__":
    llm_name = sys.argv[1]
    run(cast(LLM_NAMES, llm_name))
