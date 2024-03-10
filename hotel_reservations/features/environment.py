from dotenv import load_dotenv

from agents_behave.base_llm import LLMConfig
from hotel_reservations.llms import LLMManager

load_dotenv()


def before_all(context):
    llm = LLMManager.create_llm(
        llm_name="openai-gpt-4",
        llm_config=LLMConfig(
            name="all",
            temperature=0.0,
        ),
    )
    context.llm = llm
