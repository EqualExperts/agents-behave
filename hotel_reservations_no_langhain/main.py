import json
import sys
from dataclasses import asdict

import litellm
from hotel_reservations.assistant import HotelReservationsAssistant, make_reservation
from hotel_reservations.callbacks import ConsoleLLMCallbacks
from hotel_reservations.conversation_analyzer import ConversationAnalyzer
from hotel_reservations.llm_user import LLMUser
from hotel_reservations.llms import LLMConfig, LLMManager
from hotel_reservations.user_agent_conversation import UserAgentConversation

litellm.success_callback = ["langfuse"]


def assistant(llm):
    callbacks = ConsoleLLMCallbacks()
    llm = LLMManager.create_llm(
        llm=llm,
        llm_config=LLMConfig(
            temperature=0.0,
            callbacks=callbacks,
        ),
    )
    assistant = HotelReservationsAssistant(make_reservation=make_reservation, llm=llm)
    assistant.chat("I want to book a room")
    assistant.chat(
        "My name is Pedro Sousa, It's the Hilton Hotel, starting in 2024-02-09 and ending in 2024-02-11. It will be for 2 adults."  # noqa E501
    )


def conversation(llm):
    callbacks = ConsoleLLMCallbacks()
    llm = LLMManager.create_llm(
        llm=llm,
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

    assistant = HotelReservationsAssistant(
        make_reservation=make_reservation,
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

    criteria = [
        "Ask for the information needed to make a reservation",
        "Be polite and helpful",
    ]
    conversation_analyzer = ConversationAnalyzer(llm=llm)
    report = conversation_analyzer.analyze(
        conversation=conversation_state.chat_history,
        criteria=criteria,
    )

    print("-" * 80)
    for message in conversation_state.chat_history.messages:
        print(message)
    print("-" * 80)

    print(json.dumps(asdict(report), indent=4))


def test(llm):
    callbacks = ConsoleLLMCallbacks()
    llm = LLMManager.create_llm(
        llm=llm,
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
    user.chat("hello")
    user.chat("I'm Pedro")


if __name__ == "__main__":
    llm = sys.argv[1] if len(sys.argv) > 1 else "openrouter-mixtral"
    conversation(llm)
    # print(litellm.supports_function_calling("mistralai/mixtral-8x7b-instruct"))
