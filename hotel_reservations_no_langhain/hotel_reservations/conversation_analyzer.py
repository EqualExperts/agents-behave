import json
from dataclasses import dataclass

from hotel_reservations.llms import BaseLLM
from hotel_reservations.messages import LLMMessages, SystemMessage


@dataclass
class ConversationReport:
    score: int
    feedback: str


class ConversationAnalyzer:
    def __init__(self, llm: BaseLLM):
        self.llm = llm

    def analyze(
        self, conversation: LLMMessages, criteria: list[str] | None = None
    ) -> ConversationReport:
        criteria_str = "\n".join([f"- {c}" for c in criteria or []])
        conversation_str = "\n".join(
            [f"{m}\n{'-' * 80}" for m in conversation.messages]
        )
        prompt = PROMPT.format(criteria=criteria_str, conversation=conversation_str)
        message = self.llm.chat_completions(
            messages=LLMMessages([SystemMessage(prompt)])
        )
        content = message.content or "{}"
        content = content.replace("```json", "").replace("```", "")
        json_response = json.loads(content)
        return ConversationReport(**json_response)


PROMPT = """
You are a conversational analyst. You are given a conversation between a user and an assistant.
Your task is to analyze the conversation to check if the assistant is answering the user's questions correctly.
You should also check that the assistant met all the criterias specified in the following list:

Your response MUST be in JSON format, without fences, using the following structure:
{{
    "score": <0..9>
    "feedback": "<Your feedback here>"
}}

Criteria:
{criteria}

Conversation:
{conversation}

ANALYSIS:
"""
