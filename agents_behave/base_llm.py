from dataclasses import asdict, dataclass

from langchain_core.language_models.base import BaseLanguageModel


@dataclass
class Unionable:
    def __or__(self, other):
        other_without_none = {k: v for k, v in asdict(other).items() if v is not None}
        return self.__class__(**(asdict(self) | other_without_none))


@dataclass
class LLMConfig(Unionable):
    llm_name: str | None = None
    name: str | None = None
    model: str | None = None
    temperature: float | None = None
    base_url: str | None = None
    api_key: str | None = None
    supports_function_calling: bool = False

    @staticmethod
    def default():
        return LLMConfig(
            temperature=0.0,
            base_url=None,
            api_key=None,
        )

    def with_llm_name(self, llm_name: str) -> "LLMConfig":
        no_name = asdict(self)
        no_name.pop("llm_name")
        return LLMConfig(**no_name, llm_name=llm_name)

    def with_model(
        self,
        model: str,
    ) -> "LLMConfig":
        no_model = asdict(self)
        no_model.pop("model")
        return LLMConfig(**no_model, model=model)

    def has_function_calling_support(self) -> "LLMConfig":
        no_function_calling = asdict(self)
        no_function_calling.pop("supports_function_calling")
        return LLMConfig(**no_function_calling, supports_function_calling=True)


class BaseLLM:
    def __init__(self, llm_config: LLMConfig, llm: BaseLanguageModel):
        self.llm_config = llm_config
        self.llm = llm

    def supports_function_calling(self) -> bool:
        return self.llm_config.supports_function_calling
