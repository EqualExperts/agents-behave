from datetime import date

from dotenv import load_dotenv

from agents_behave.base_llm import LLMConfig
from hotel_reservations.llms import LLM_NAMES, BaseLLM, LLMManager

load_dotenv(override=True)


def create_llm(name: str, llm_name: LLM_NAMES) -> BaseLLM:
    return LLMManager.create_llm(
        llm_name=llm_name,
        llm_config=LLMConfig(
            name=name,
            temperature=0.0,
        ),
    )


def before_all(context):
    llm = create_llm("llama3", "groq-llama3-70")
    context.assistant_llm = llm
    context.user_llm = llm
    context.analyser_llm = llm
    context.date = date.today()
    context.hotels = []
