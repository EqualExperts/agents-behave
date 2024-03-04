import sys

from hotel_reservations.assistant import HotelReservationsAssistant, make_reservation
from hotel_reservations.callbacks import ConsoleLLMCallbacks
from hotel_reservations.llms import LLMConfig, LLMManager


def assistant(llm):
    callbacks = ConsoleLLMCallbacks()
    llm = LLMManager.create_llm(llm=llm, llm_config=LLMConfig(callbacks=callbacks))
    assistant = HotelReservationsAssistant(make_reservation=make_reservation, llm=llm)
    assistant.chat("I want to book a room")
    assistant.chat(
        "My name is Pedro Sousa, It's the Hilton Hotel, starting in 2024-02-09 and ending in 2024-02-11. It will be for 2 adults."  # noqa E501
    )


if __name__ == "__main__":
    llm = sys.argv[1] if len(sys.argv) > 1 else "openrouter-mixtral"
    assistant(llm)
