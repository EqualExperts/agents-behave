# This class was generated by a code assistant.

from agents_behave.llm_user import User


class ConsoleUser(User):
    def start(self) -> str:
        return input("You: ")

    def chat(self, llm_response: str) -> str:
        print(f"Assistant: {llm_response}")
        return input("You: ")
