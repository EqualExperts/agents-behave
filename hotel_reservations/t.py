from agents_behave.llm_user import LLMUser
from hotel_reservations.llms import LLMManager

llm = LLMManager.create_llm("openai-gpt-4")
persona = """
        My name is Pedro Sousa. I don't like answering questions and I'm lazy, so I'll only answer one question at a time.
        My goal is to book a room in an hotel in London, starting in 2024-02-09 and ending in 2024-02-11, for 2 guests.
        I will not provide any information unless asked.
"""  # noqa E501
user = LLMUser(llm=llm, persona=persona)

response = user.start()

print(response)
