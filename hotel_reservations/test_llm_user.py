from agents_behave.llm_user import LLMUser
from hotel_reservations.assistant import HotelReservationsAssistant
from hotel_reservations.core import find_hotels, make_reservation
from hotel_reservations.llms import LLMManager

llm = LLMManager.create_llm("openai-gpt-4")
persona = """
        My name is John Smith. I don't like answering questions and I'm very rude.
        My goal is to book a room in an hotel in London, starting in 2024-02-09 and ending in 2024-02-11, for 3 guests.
"""  # noqa E501
user = LLMUser(llm=llm, persona=persona)

assistant = HotelReservationsAssistant(
    llm=llm, make_reservation=make_reservation, find_hotels=find_hotels
)

response = user.start()
print(response)

# response = assistant.chat(response)["output"]
# print(response)

# response = user.start()
# print(response)
