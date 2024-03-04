import json
from dataclasses import dataclass

from hotel_reservations_no_langhain.hotel_reservations.llms import OpenAIBaseLLM
from hotel_reservations.messages import LLMMessages, SystemMessage


@dataclass
class ConversationReport:
    score: int
    feedback: str


class ConversationAnalyzer:
    def __init__(self, llm: OpenAIBaseLLM):
        self.llm = llm

    def analyze(
        self, conversation: LLMMessages, criteria: list[str] = []
    ) -> ConversationReport:
        criteria_str = "\n".join([f"- {c}" for c in criteria])
        conversation_str = "\n".join([str(m) for m in conversation.messages])
        prompt = PROMPT.format(criteria=criteria_str, conversation=conversation_str)
        completion = self.llm.chat_completions(
            messages=LLMMessages([SystemMessage(prompt)])
        )
        content = completion.choices[0].message.content or "{}"
        json_response = json.loads(content)
        return ConversationReport(**json_response)


PROMPT = """
You are a conversational analyst. You are given a conversation between a user and an assistant.
Your task is to analyze the conversation to check if the assistant is answering the user's questions correctly.
You should also check that the assistant met all the criterias specified in the following list:

Your response MUST be in JSON format using the following structure:
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
