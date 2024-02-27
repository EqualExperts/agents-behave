from langchain_core.language_models.base import BaseLanguageModel
from langchain_openai import ChatOpenAI
from langchain_together import Together

from hotel_reservations.chat_open_router import ChatOpenRouter


class ModelConfig:
    def __init__(
        self,
        llm: BaseLanguageModel,
        model: str,
    ) -> None:
        self.llm = llm
        self.model = model


def model_gpt_3_5():
    model = "gpt-3.5-turbo-0125"
    return ModelConfig(
        llm=ChatOpenAI(
            model=model,
            temperature=0.0,
            model_kwargs={"seed": 42},
        ),
        model=model,
    )


def model_gpt_4():
    model = "gpt-4-turbo-preview"
    return ModelConfig(
        llm=ChatOpenAI(
            model=model,
            temperature=0.0,
            model_kwargs={"seed": 42},
        ),
        model=model,
    )


def model_mixtral_8_7B():
    model = "mistralai/mixtral-8x7b-instruct"
    return ModelConfig(
        llm=ChatOpenRouter(
            model=model,
            temperature=0.0,
            model_kwargs={"seed": 1234},
        ),
        model=model,
    )


def model_mixtral_8_7B_together():
    model = "mistralai/Mixtral-8x7B-Instruct-v0.1"
    return ModelConfig(
        llm=Together(
            model=model,
            temperature=0.0,
        ),  # type: ignore
        model=model,
    )


def claude_instant_v1_beta():
    model = "anthropic/claude-instant-1:beta"
    return ModelConfig(
        llm=ChatOpenRouter(model=model, temperature=0.0, model_kwargs={"seed": 42}),
        model=model,
    )


def llama_v2_70b_chat():
    model = "meta-llama/llama-2-70b-chat"
    return ModelConfig(
        llm=ChatOpenRouter(
            model=model,
            temperature=0.0,
            model_kwargs={"seed": 42},
        ),
        model=model,
    )


models_config = {
    "gpt-3": model_gpt_3_5,
    "gpt-4": model_gpt_4,
    "mixtral": model_mixtral_8_7B,
    "mixtral-together": model_mixtral_8_7B_together,
    "claude": claude_instant_v1_beta,
}


def create_model_config(model_name: str) -> ModelConfig:
    return models_config[model_name]()
