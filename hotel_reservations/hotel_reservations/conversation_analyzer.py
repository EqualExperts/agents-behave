from langchain.prompts import PromptTemplate
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.language_models.base import BaseLanguageModel
from langchain_core.messages import BaseMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate


class ConversationAnalyzer:
    def __init__(self, llm: BaseLanguageModel):
        self.chain = self.build_chain(llm)

    def invoke(self, chat_history: list[BaseMessage], criteria: list[str] = []):
        conversation = ChatMessageHistory()
        for c in chat_history:
            conversation.add_message(c)
        criteria_str = "\n".join([f"- {c}" for c in criteria])
        response = self.chain.invoke(
            {"conversation": conversation, "criteria": criteria_str}
        )
        return response

    def build_chain(self, llm: BaseLanguageModel):
        prompt = PromptTemplate(
            template=PROMPT, input_variables=["criteria", "conversation"]
        )
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", PROMPT),
            ]
        )
        chain = prompt | llm | JsonOutputParser()
        return chain


PROMPT = """
You are a conversational analyst. You are given a conversation between a user and an assistant.
Your task is to analyze the conversation to check if the assistant is answering the user's questions correctly.
You should also check that the assistant met all the criterias specified in the followbng list:
Remember, you task is to analyze the conversation, not to continue it.

Your response MUST be in JSON format using the following structure:
{{
    "score": <0..9>
    "feedback": "Your feedback here"
}}

Criteria:
{criteria}

Conversation:
{conversation}

ANALYSIS:
"""
