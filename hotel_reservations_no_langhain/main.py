import json
import sys
from dataclasses import asdict
from typing import cast

import litellm
from colorama import Fore, Style
from hotel_reservations.assistant import (
    HotelReservationsAssistant,
    get_hotel_price_per_night,
    make_reservation,
)
from hotel_reservations.callbacks import ConsoleLLMCallbacks
from hotel_reservations.conversation_analyzer import ConversationAnalyzer
from hotel_reservations.llm_user import LLMUser
from hotel_reservations.llms import LLMS, BaseLLM, LLMConfig, LLMManager
from hotel_reservations.user_agent_conversation import UserAgentConversation

litellm.success_callback = ["langfuse"]


def create_llm(llm_name: LLMS, name: str) -> BaseLLM:
    callbacks = ConsoleLLMCallbacks()
    return LLMManager.create_llm(
        llm_name=llm_name,
        llm_config=LLMConfig(
            name=name,
            temperature=0.0,
            callbacks=callbacks,
        ),
    )


def assistant(llm_name: LLMS):
    assistant = HotelReservationsAssistant(
        make_reservation=make_reservation,
        get_hotel_price_per_night=get_hotel_price_per_night,
        llm=create_llm(llm_name, "assistant"),
    )
    assistant.chat("I want to book a room")
    assistant.chat(
        "My name is Pedro Sousa, It's the Hilton Hotel, starting in 2024-02-09 and ending in 2024-02-11. It will be for 2 adults."  # noqa E501
    )


def conversation(llm_name: LLMS):
    persona = """
        Your name is Pedro Sousa.
        You want to book a room in the Hilton Hotel, starting in 2024-02-09 and ending in 2024-02-11.
        It will be for 2 adults.
    """
    user = LLMUser(
        persona=persona,
        llm=create_llm(llm_name, "LLMUser"),
    )

    assistant = HotelReservationsAssistant(
        make_reservation=make_reservation,
        get_hotel_price_per_night=get_hotel_price_per_night,
        llm=create_llm(llm_name, "Assistant"),
    )

    conversation = UserAgentConversation(
        user,
        assistant,
        llm=create_llm(llm_name, "UserAgentConversation"),
        stop_condition=lambda state: state.iterations_count >= 6
        or state.last_assistant_message_contains("bye"),
    )
    conversation_state = conversation.start()

    criteria = [
        "Ask for the information needed to make a reservation.",
        "There is no need to ask for anything else besides the information needed to call the make_reservation tool.",
        "Ask for confirmation before making the reservation.",
        "Be polite and helpful.",
    ]
    conversation_analyzer = ConversationAnalyzer(
        llm=create_llm(llm_name, "ConversationAnalyzer"),
    )
    report = conversation_analyzer.analyze(
        conversation=conversation_state.chat_history,
        criteria=criteria,
    )

    print("-" * 80)
    for message in conversation_state.chat_history.messages:
        print(message)
    print("-" * 80)

    print(json.dumps(asdict(report), indent=4))


def test(llm_name: LLMS):
    llm = create_llm(llm_name, "LLMUser")
    persona = """
        Your name is Pedro Sousa.
        You want to book a room in the Hilton Hotel, starting in 2024-02-09 and ending in 2024-02-11.
        It will be for 2 adults.
    """
    user = LLMUser(persona=persona, llm=llm)
    user.start()
    c = user.chat(
        """
Sure, I'd be happy to help you with that! Could you please provide me with the following information:

1. The name of the guest
2. The name of the hotel
3. The check-in date (format: YYYY-MM-DD)
4. The check-out date (format: YYYY-MM-DD)
5. The number of guests

Once I have this information, I can make the reservation for you.
              """
    )
    print(c)


if __name__ == "__main__":
    print(Fore.YELLOW + Style.BRIGHT)
    print(" ###  #####   #   ####  #####")
    print("#   #   #    # #  #   #   #  ")
    print("#       #   #   # #   #   #  ")
    print(" ###    #   #   # ####    #  ")
    print("    #   #   ##### # #     #  ")
    print("#   #   #   #   # #  #    #  ")
    print(" ###    #   #   # #   #   #  ")
    print(Style.RESET_ALL)

    llm_name = sys.argv[1] if len(sys.argv) > 1 else "openrouter-mixtral"
    conversation(cast(LLMS, llm_name))
