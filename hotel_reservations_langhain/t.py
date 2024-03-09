from agents_behave.llm_user import LLMUser
from hotel_reservations_langhain.hotel_reservations.llms import LLMManager

llm = LLMManager.create_llm("openrouter-mixtral")
persona = """
    My name is Pedro Sousa.
    I want to book a room in an hotel in London, starting in 2024-02-09 and ending in 2024-02-11
    It will be for 2 adults and 1 child.
    My budget is $350 per night.
"""
user = LLMUser(llm=llm, persona=persona)

response = user.start()

print(response)
